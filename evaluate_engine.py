"""SparkLens rule-engine evaluator.

Scores the engine's findings (dataset_predicted.csv) against LLM-authored
expected outcomes (dataset_expected.csv). Both paragraphs are split into
atomic claims and normalised with a Spark-domain lexicon, so the exact wording
does not matter. Claims are vectorised with TF-IDF (or raw term counts) and
matched directionally: a predicted claim is supported when an expected claim
says the same thing or contains it (precision); an expected claim is covered
when a predicted claim contains its content (recall). Guards reject matches
that disagree on stage counts, numbers or polarity. Precision is the headline
metric; the final score is F0.5.

Fully offline: no API calls, no model downloads - only scikit-learn.

Usage:
  python evaluate_engine.py export     # eval_plans/<id>.txt + predicted template (manual CLI route)
  python evaluate_engine.py predict    # run `cli.main analyze <plan> --eval` for every plan
  python evaluate_engine.py evaluate   # precision / recall / F1 / final score (+ delta vs baseline)
  python evaluate_engine.py baseline   # evaluate and freeze eval_baseline.json
  python evaluate_engine.py validate   # measure the evaluator itself on known-answer test cases
  python evaluate_engine.py selftest   # offline sanity checks of the matcher and metrics
"""

import argparse
import csv
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
except ImportError:
    sys.exit("Error: scikit-learn is required. Install it with: pip install scikit-learn")

ROOT = Path(__file__).resolve().parent
EXPECTED_CSV = ROOT / "dataset_expected.csv"
PREDICTED_CSV = ROOT / "dataset_predicted.csv"
PLANS_DIR = ROOT / "eval_plans"
REVIEW_CSV = ROOT / "eval_review.csv"
BASELINE_JSON = ROOT / "eval_baseline.json"

# Scoring configuration. It is stored in the baseline so later runs stay comparable.
DEFAULT_THRESHOLD = 0.45
CONCEPT_WEIGHT = 0.75  # weight of the Spark-concept channel (lexicon concepts)
FREE_WEIGHT = 0.25     # weight of the free-wording channel (all other words and numbers)
BETA = 0.5             # F-beta for the final score; beta < 1 weights precision above recall

# Folders holding rule-engine code; used to flag uncommitted engine changes in a baseline.
ENGINE_PATHS = ["analyzer", "rules", "models", "services"]


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

# Ordered (pattern, concept) pairs applied to lower-cased, CamelCase-split,
# punctuation-free text. Specific phrases come before the generic ones they
# contain. Concepts are emitted in UPPER case so later patterns never re-match
# them, and are lower-cased at the end.
LEXICON: list[tuple[str, str]] = [
    # Absence of data movement (before polarity so "unnecessary" is still visible)
    (r"(?:without|no|avoids?|avoiding|avoided|never|zero|remov(?:e|es|ed|ing)|eliminat(?:e|es|ed|ing))"
     r"(?: (?:any|an?|the|both|all|these|those|of|one|\d+|join|extra|additional|further|unnecessary|intermediate))*"
     r" (?:shuffl(?:e|es|ed|ing)|exchanges?|data movement|moving data|moving rows|network transfer)", "noshuffle"),

    # Polarity
    (r"not (?:strictly |really |actually |structurally )?(?:required|needed|necessary)"
     r"|unnecessary|redundant|avoidable|superfluous", "redundant"),
    (r"not an? (?:optimi[sz]ation (?:target|opportunity)|problem|issue|concern)", "required"),
    (r"(?:structurally )?(?:required|necessary|mandatory|unavoidable|needed|inherent)", "required"),
    (r"inefficient|suboptimal|wasteful|costly|expensive", "inefficient"),
    (r"efficient|optimal|cheap|cheaper|inexpensive", "efficient"),
    (r"disabled|turned off|switched off|deactivated|not enabled|(?:is|are|was|were) off", "disabled"),
    (r"enabled|turned on|switched on|activated", "enabled"),
    (r"bottleneck|choke point|no parallelism|serial(?:ly|ised|ized|ises|izes)?"
     r"|(?:limits?|limiting|reduces?|reducing|restricts?|kills?|removes?) (?:all )?parallelism", "bottleneck"),

    # Joins
    (r"broadcast nested loop join|nested loop join|nested loop|bnlj", "nestedloopjoin"),
    (r"cartesian product|cartesian join|cartesian|cross join|cross product", "cartesianjoin"),
    (r"shuffled hash join|shuffle hash join|shj", "shuffledhashjoin"),
    (r"sort merge join|sort merge|merge joined|merge join|smj", "sortmergejoin"),
    (r"broadcast hash join|broadcast join|broadcasted join|bhj|map side join", "broadcastjoin"),
    (r"broadcast(?:ing|s|ed)?(?: exchange)?", "broadcast"),
    (r"(?:left )?semi join|left semi", "semijoin"),
    (r"(?:left )?anti join|left anti", "antijoin"),
    (r"(?:full |left |right )?outer joins?|full outer", "outerjoin"),
    (r"joins?|joined|joining", "join"),

    # Exchanges & partitioning
    (r"reused? exchange|exchange reuse", "reusedexchange"),
    (r"reus(?:e|es|ed|ing)", "reuse"),
    (r"coalesc\w*", "coalesce"),
    (r"repartition by range|range partition(?:ing|ed|s)?|rangepartitioning", "rangepartitioning"),
    (r"hash partition(?:ing|ed|s)?|hashpartitioning|hash distribut\w*|hash (?:shuffl\w*|exchanges?)"
     r"|(?:by|using|with) a hash of|hash(?:es|ed|ing)(?: (?:every|each|all|the|raw|rows?))* (?:on|by)",
     "hashpartitioning"),
    (r"round robin(?: partition(?:ing|ed)?)?|roundrobinpartitioning", "roundrobinpartitioning"),
    (r"single partition|singlepartition|(?:into|to) (?:one|1) partition|partitions? into one|single task|one task"
     r"|1 task|single executor|one executor|single core|one core", "singlepartition"),
    (r"shuffle (?:exchange|write|read|map stage)(?: sink| source)?|exchanges?|shuffles?|shuffled|shuffling"
     r"|reshuffl\w*|redistribut\w*|repartition\w*|data movement|network transfer"
     r"|mov(?:e|es|ed|ing) (?:the |all |any |every )?(?:data|rows?)", "shuffle"),

    # Aggregation
    (r"(?:2|multi|multiple) ?(?:phase|stage|step)s? aggregat\w*|(?:2|multi|multiple) ?(?:phase|step)s?"
     r"|partial (?:and|then|followed by|plus) (?:a )?final(?: merge)?(?: aggregat\w*)?", "twophaseagg"),
    (r"(?:partial|map side|local|pre|combiner) (?:hash )?aggregat\w*|preaggregat\w*"
     r"|partial (?:sum|count|avg|average|min|max|merge)|partial|partially", "partialagg"),
    (r"global aggregat\w*|aggregat\w* without (?:grouping )?keys|no grouping keys"
     r"|ungrouped aggregat\w*", "globalagg"),
    (r"(?:final|merge|reduce side|post shuffle) (?:hash )?aggregat\w*|final merge|finalmerge"
     r"|merge (?:sum|count|avg|average)", "finalagg"),
    (r"count distinct|countdistinct|distinct count", "countdistinct"),
    (r"distinct|deduplicat\w*|dedup\w*|drop duplicates|(?:remov|eliminat)\w* duplicates?", "distinct"),
    (r"expand|rollup|cube|grouping sets?", "expand"),
    (r"object hash aggregat\w*|collect (?:list|set)", "objecthashagg"),
    (r"sort aggregat\w*|hash aggregat\w*|aggregat\w*|group by|groupby|grouped|grouping", "aggregation"),

    # Sorting & limits
    (r"take ordered and project|top n|top k", "topn"),
    (r"sort within partitions|sortwithinpartitions|partition local sort|local sort|per partition sort", "localsort"),
    (r"order by|orderby|sorts?|sorted|sorting|ordering|ordered", "sort"),
    (r"ascending|asc|(?:lowest|smallest|earliest)(?: \w+)? first|from (?:lowest|smallest) to (?:highest|largest)",
     "ascending"),
    (r"descending|desc|(?:highest|largest|biggest|latest)(?: \w+)? first|from (?:highest|largest) to (?:lowest|smallest)",
     "descending"),
    (r"collect limit|global limit|local limit|limit(?:s|ed)?", "limit"),

    # Stages & pipelines
    (r"whole stage code ?gen\w*|code ?gen(?:eration)?", "codegen"),
    (r"stage boundar(?:y|ies)|stage breaks?|new stages?|(?:ends?|closes?|stops?) (?:one |a |the )?stages?"
     r"|stages? (?:ends?|stops?)", "stageboundary"),
    (r"stages?", "stage"),
    (r"wide (?:transformation|dependency|dependencies|operator)s?", "wide"),
    (r"narrow(?: transformations?| operators?| dependency| dependencies)?", "narrow"),
    (r"(?:long|deep|complex|lengthy|large) (?:narrow |transformation |operator )?(?:pipeline|chain)s?", "longpipeline"),
    (r"pipelin\w*|fused|fuses|fusing|chained", "pipeline"),

    # AQE
    (r"adaptive query execution|adaptive spark plan|adaptive execution|adaptive|aqe", "aqe"),

    # Scans, filters, columnar
    (r"predicate push ?down|filter push ?down|pushed (?:down )?filters?|pushedfilters|push(?:ed|es)? down"
     r"|pushdown|early filter\w*", "pushdown"),
    (r"columnar to row|columnartorow", "columnartorow"),
    (r"file scan|filescan|table scan|scann?(?:ed|ing|s)?", "scan"),
    (r"csv", "csv"),
    (r"parquet", "parquet"),
    (r"filters?|filtered|filtering|predicates?|where clause", "filter"),

    # Other operators & problems
    (r"(?:python|pandas|arrow) udfs?|batch eval python|arrow eval python|user defined functions?|udfs?", "pythonudf"),
    (r"window(?:ed)?(?: functions?)?", "window"),
    (r"data skew|skew(?:ed|ness)?|hot keys?|imbalanced partitions?", "skew"),
    (r"unions?|concatenat\w*", "union"),
    (r"explod\w*|generate|lateral view", "generate"),
    (r"sampl(?:e|es|ed|ing)", "sample"),
    (r"memory|spill\w*|out of memory|oom", "memory"),
    (r"photon", "photon"),
    (r"hints?", "hint"),

    # Advice rather than observation
    (r"(?:would|could|can|might) (?:avoid|remove|eliminate|reduce|restore|save|help|improve)"
     r"|should be avoided|consider(?:ing)?|recommend\w*|suggest\w*|would|could", "recommend"),
]

_LEXICON = [(re.compile(rf"\b(?:{pattern})\b"), f" {concept.upper()} ") for pattern, concept in LEXICON]
CONCEPTS = {concept for _, concept in LEXICON}

# A specific concept also implies its broader ones (e.g. a sort-merge join is a join).
PARENTS = {
    "sortmergejoin": ["join"],
    "broadcastjoin": ["join", "broadcast", "noshuffle"],
    "shuffledhashjoin": ["join"],
    "nestedloopjoin": ["join"],
    "cartesianjoin": ["join"],
    "semijoin": ["join"],
    "antijoin": ["join"],
    "outerjoin": ["join"],
    "reusedexchange": ["reuse", "shuffle"],
    "countdistinct": ["distinct", "aggregation"],
    "objecthashagg": ["aggregation"],
    "twophaseagg": ["partialagg", "finalagg", "aggregation"],
    "partialagg": ["aggregation"],
    "finalagg": ["aggregation"],
    "globalagg": ["aggregation"],
    "hashpartitioning": ["shuffle"],
    "rangepartitioning": ["shuffle"],
    "roundrobinpartitioning": ["shuffle"],
    "longpipeline": ["pipeline"],
    "narrow": ["pipeline", "noshuffle"],   # narrow dependencies are pipelined without a shuffle
    "wide": ["shuffle", "stageboundary"],  # wide dependencies shuffle and start a new stage
    "stageboundary": ["stage"],
    "localsort": ["sort"],
    "topn": ["sort", "limit"],
}

# Concept pairs with opposite meaning: similar claims that disagree on these do not match.
POLARITY_PAIRS = [
    ("required", "redundant"),
    ("efficient", "inefficient"),
    ("enabled", "disabled"),
    ("ascending", "descending"),
]
OPPOSITES = POLARITY_PAIRS + [("noshuffle", "shuffle")]

# Mutually exclusive alternatives: a join has one strategy, an exchange one partitioning
# scheme. Two claims naming different members of the same family state different facts.
FAMILIES = [
    {"sortmergejoin", "broadcastjoin", "shuffledhashjoin", "nestedloopjoin", "cartesianjoin"},
    {"semijoin", "antijoin", "outerjoin"},
    {"hashpartitioning", "rangepartitioning", "roundrobinpartitioning", "singlepartition"},
    {"expand", "generate"},
    {"csv", "parquet"},
]

NUMBER_WORDS = {
    "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
    "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
}

NEGATIONS = {"no", "not", "never", "without", "nor", "cannot", "neither", "nothing", "unable"}
HEDGES = {"whether"}
NEGATION_WINDOW = 3   # "not a real bottleneck": the negation reaches the first concept within 3 words
HEDGE_WINDOW = 6      # "whether this shuffle is required": the hedge reaches the next polarity concept
POLARITY = {c for pair in POLARITY_PAIRS for c in pair}
_IDENTIFIER = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")   # column names such as customer_id

# Concepts too general to tell two claims' topics apart (almost every plan has them).
GENERIC_CONCEPTS = {"shuffle", "noshuffle", "stage", "join", "aggregation", "sort", "filter", "scan",
                    "pipeline", "limit", "recommend"}

DOMAIN_STOPWORDS = {
    "spark", "sparklens", "plan", "plans", "query", "queries", "job", "jobs", "physical",
    "execution", "execute", "executes", "executed", "operator", "operators", "operation", "operations",
    "detected", "detect", "detects", "perform", "performs", "performed", "use", "uses", "used", "using",
    "select", "selects", "selected", "consider", "may", "might", "could", "would", "should",
    "typically", "usually", "strategy", "data", "dataset", "row", "rows", "result", "results",
    "estimated", "estimate", "expected", "contain", "contains", "containing", "count", "total", "number",
    "run", "runs", "running", "happens", "applied", "apply", "applies", "also", "whether", "does", "doing",
    "determined", "evidence", "rule", "quality", "here", "instead", "e", "g", "i", "etc", "s",
}
STOPWORDS = (set(ENGLISH_STOP_WORDS) | DOMAIN_STOPWORDS) - NEGATIONS

_SUFFIXES = ("ations", "ation", "ating", "ated", "ates", "ings", "ing", "ies", "ied",
             "edly", "est", "ers", "er", "ed", "es", "ly", "s", "e")

_PLAN_ID_RE = re.compile(r"#\d+L?\b|\[?\b(?:plan_)?id=#?\d+\]?")
_CAMEL_LOWER_UPPER = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_CAMEL_ACRONYM = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")

_ABBREVIATIONS = re.compile(r"\b(e\.g|i\.e|etc|vs|approx|cf)\.", re.IGNORECASE)
_DECIMAL_DOT = re.compile(r"(?<=\d)\.(?=\d)")
_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+")
# Connectives that join two facts in one sentence ("X is disabled, so Spark uses Y").
_CLAUSE_BREAK = re.compile(r",\s+so\s+(?!that\b)|,?\s+because\s+|,\s+since\s+|,?\s+but\s+", re.IGNORECASE)
# A claim opening with a pronoun refers to the previous one ("This strategy requires...").
_ANAPHORA = re.compile(r"^(?:this|these|that|those|it|its|they|their|such)\b", re.IGNORECASE)
_NO_ISSUES = re.compile(
    r"^(?:no (?:major |significant |notable )?(?:issues?|findings?|problems?)"
    r"(?: (?:were |are )?(?:found|detected|expected|reported))?|nothing to (?:report|flag))[.!]?$",
    re.IGNORECASE,
)


def _stem(token: str) -> str:
    """Light, dependency-free suffix stripping so inflections share one form."""
    if token.isdigit() or len(token) <= 3:
        return token
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            if suffix == "s" and token.endswith("ss"):
                continue
            stem = token[: -len(suffix)]
            return stem + "y" if suffix in ("ies", "ied") else stem
    return token


def normalize(text: str) -> list[str]:
    """Turns one claim into canonical tokens: domain concepts, stems, numbers, not_ markers."""
    text = _PLAN_ID_RE.sub(" ", text)
    text = re.sub(r"n't\b", " not", text)
    text = _CAMEL_LOWER_UPPER.sub(" ", text)
    text = _CAMEL_ACRONYM.sub(" ", text)
    text = _THOUSANDS.sub("", text)
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    text = " ".join(NUMBER_WORDS.get(word, word) for word in text.split())

    for pattern, concept in _LEXICON:
        text = pattern.sub(concept, text)

    content: list[list] = []            # [token, is_concept]
    markers: list[tuple[str, int]] = []  # (prefix, index of the first content token it can reach)
    for raw in text.split():
        is_concept = raw.isupper()
        token = raw.lower()
        if not is_concept:
            if token in NEGATIONS:
                markers.append(("not", len(content)))
                continue
            if token in HEDGES:
                markers.append(("maybe", len(content)))
                continue
            if token in STOPWORDS:
                continue
            token = _stem(token)
        content.append([token, is_concept])

    for prefix, start in markers:
        if prefix == "not":
            window = content[start:start + NEGATION_WINDOW]
            target = next((c for c in window if c[1]), window[0] if window else None)
        else:
            window = content[start:start + HEDGE_WINDOW]
            target = next((c for c in window if c[1] and c[0] in POLARITY), None)
        if target and "_" not in target[0]:
            target[0] = f"{prefix}_{target[0]}"
            target[1] = False
            if target[0] == "not_shuffle":   # "never shuffled", "does not shuffle" = no shuffle
                target[0] = "noshuffle"
    return [token for token, _ in content]


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------

def _is_marked_concept(token: str) -> bool:
    """'not_bottleneck' / 'maybe_required': a negated or hedged lexicon concept."""
    prefix, _, rest = token.partition("_")
    return prefix in ("not", "maybe") and rest in CONCEPTS


@dataclass
class Claim:
    text: str
    tokens: list[str]
    inherited: tuple[str, ...] = ()   # concepts taken over from the previous sentence via a pronoun

    @property
    def own(self) -> set[str]:
        """Tokens the sentence states itself (without pronoun context)."""
        return set(self.tokens) - set(self.inherited)

    @property
    def concepts(self) -> str:
        """Spark concepts in the claim (plain, negated or hedged); plain ones add the broader concepts they imply."""
        found = []
        for token in self.tokens:
            if token in CONCEPTS:
                found.append(token)
                found.extend(PARENTS.get(token, []))
            elif _is_marked_concept(token):
                found.append(token)
        return " ".join(found)

    @property
    def free(self) -> str:
        """Everything that is not a concept: remaining words and numbers."""
        return " ".join(t for t in self.tokens if t not in CONCEPTS and not _is_marked_concept(t))

    @property
    def numbers(self) -> set[str]:
        return {t for t in self.tokens if t.isdigit()}

    @property
    def stage_counts(self) -> set[str]:
        """Numbers stated as a stage count, e.g. '3 stages'."""
        return {t for t, nxt in zip(self.tokens, self.tokens[1:]) if t.isdigit() and nxt == "stage"}

    @property
    def identifiers(self) -> set[str]:
        """Column names written in snake_case, e.g. customer_id (plural forms folded: product_ids)."""
        return {i[:-1] if i.endswith("s") else i for i in _IDENTIFIER.findall(self.text)}

    @property
    def subjects(self) -> set[str]:
        """The specific Spark things the claim is about (concepts and what they imply, minus generic ones)."""
        found = set(self.concepts.split())
        return found - POLARITY - GENERIC_CONCEPTS


def split_claims(paragraph: str) -> list[Claim]:
    """Splits a paragraph into de-duplicated atomic claims (sentences, split again at causal connectives)."""
    text = " ".join((paragraph or "").split())
    text = _ABBREVIATIONS.sub(lambda m: m.group(1).replace(".", "\0") + "\0", text)
    text = _DECIMAL_DOT.sub("\0", text)

    claims: list[Claim] = []
    seen: set[str] = set()
    parts = [clause for sentence in _SENTENCE_END.split(text) for clause in _CLAUSE_BREAK.split(sentence)]
    previous: list[str] = []
    for part in parts:
        sentence = part.replace("\0", ".").strip(" ;,")
        if not sentence or _NO_ISSUES.match(sentence):
            continue
        tokens = normalize(sentence)
        inherited: list[str] = []
        if _ANAPHORA.match(sentence):
            # Inherit only the previous claim's plain concepts (never its numbers).
            inherited = [t for t in dict.fromkeys(previous) if t in CONCEPTS and t not in tokens]
            tokens += inherited
        previous = tokens
        key = sentence.lower().rstrip(".!?; ")
        if key in seen or not tokens:
            continue
        seen.add(key)
        claims.append(Claim(sentence, tokens, tuple(inherited)))
    return claims


def conflict(a: Claim, b: Claim) -> str:
    """Why claim a (the one being judged) is not backed by a similar-looking claim b ('' if it is)."""
    if (a.stage_counts or b.stage_counts) and not (a.stage_counts & b.stage_counts):
        return "stage count mismatch"
    if a.numbers - b.numbers:
        return "number not backed"
    ta, tb = set(a.tokens), set(b.tokens)
    if ("recommend" in ta) != ("recommend" in tb):
        return "advice vs observation"
    for family in FAMILIES:
        if (a.own & family) - tb:
            return "different alternative"   # a names a join strategy / partitioning / ... that b doesn't back
    if a.identifiers and b.identifiers and not a.identifiers & b.identifiers:
        return "different columns"
    if a.subjects and b.subjects and not a.subjects & b.subjects:
        return "different subject"           # e.g. "AQE is disabled" vs "Broadcasting is disabled"
    # Opposite concepts, a negated concept ("not_x"), or a hedged one ("maybe_x", from "whether x").
    pairs = OPPOSITES + [(c, f"not_{c}") for c in CONCEPTS] + [(c, f"maybe_{c}") for c in POLARITY]
    for positive, negative in pairs:
        if (positive in ta and negative in tb and negative not in ta and positive not in tb) or \
           (negative in ta and positive in tb and positive not in ta and negative not in tb):
            return "polarity conflict"
    return ""


# ---------------------------------------------------------------------------
# Vectorisation & matching
# ---------------------------------------------------------------------------

CHANNELS = ("concepts", "free")
Vector = dict[str, float]


class ClaimVectorizer:
    """TF-IDF (or raw count) vectors for claims, in two channels.

    The concept channel carries the Spark meaning, the free channel the remaining
    wording. IDF is fitted with scikit-learn's TfidfVectorizer on the reference
    (expected) claims only, so the vector space is fixed for a dataset and the
    baseline and later runs are measured the same way. Terms the reference never
    uses get the maximum IDF: unexpected content counts as rare, not as absent.
    """

    def __init__(self, kind: str = "tfidf"):
        self.kind = kind
        self.idf: dict[str, dict[str, float]] = {ch: {} for ch in CHANNELS}
        self.unseen_idf: dict[str, float] = {ch: 1.0 for ch in CHANNELS}

    def fit(self, claims: list[Claim]) -> "ClaimVectorizer":
        if self.kind != "tfidf":
            return self  # CountVectorizer-style: raw term counts, no IDF
        for channel in CHANNELS:
            docs = [getattr(c, channel) for c in claims]
            if channel == "concepts":
                docs += sorted(CONCEPTS)  # every concept is in the vocabulary
            docs = [d for d in docs if d]
            if docs:
                tfidf = TfidfVectorizer(lowercase=False, token_pattern=r"\S+").fit(docs)
                self.idf[channel] = dict(zip(tfidf.get_feature_names_out(), tfidf.idf_))
                self.unseen_idf[channel] = float(tfidf.idf_.max())
        return self

    def vector(self, claim: Claim, channel: str) -> Vector:
        counts = Counter(getattr(claim, channel).split())
        if self.kind != "tfidf":
            return {t: float(n) for t, n in counts.items()}
        idf = self.idf[channel]
        return {t: (1 + math.log(n)) * idf.get(t, self.unseen_idf[channel]) for t, n in counts.items()}

    @staticmethod
    def _cosine(a: Vector, b: Vector) -> float:
        dot = sum(w * b[t] for t, w in a.items() if t in b)
        norm = math.sqrt(sum(w * w for w in a.values())) * math.sqrt(sum(w * w for w in b.values()))
        return dot / norm if norm else 0.0

    @staticmethod
    def _containment(a: Vector, b: Vector) -> float:
        """Share of a's weight whose terms also occur in b (directional)."""
        total = sum(a.values())
        return sum(w for t, w in a.items() if t in b) / total if total else 0.0

    def _blend(self, parts: dict[str, float], present: dict[str, bool]) -> float:
        if present["concepts"] and present["free"]:
            return CONCEPT_WEIGHT * parts["concepts"] + FREE_WEIGHT * parts["free"]
        return parts["concepts"] if present["concepts"] else parts["free"]

    def cosine(self, a: Claim, b: Claim) -> float:
        """Symmetric similarity; a channel counts only when both claims use it."""
        parts = {ch: self._cosine(self.vector(a, ch), self.vector(b, ch)) for ch in CHANNELS}
        return self._blend(parts, {ch: bool(getattr(a, ch) and getattr(b, ch)) for ch in CHANNELS})

    def containment(self, a: Claim, b: Claim) -> float:
        """How much of claim a's content is found in claim b; the channels come from a."""
        parts = {ch: self._containment(self.vector(a, ch), self.vector(b, ch)) for ch in CHANNELS}
        return self._blend(parts, {ch: bool(getattr(a, ch)) for ch in CHANNELS})

    def support(self, predicted: list[Claim], expected: list[Claim]) -> list[list[float]]:
        """Precision side: a predicted claim is backed if it says the same thing as an
        expected claim (cosine) or everything it says is contained in one."""
        return [[max(self.cosine(p, e), self.containment(p, e)) for e in expected] for p in predicted]

    def coverage(self, expected: list[Claim], predicted: list[Claim]) -> list[list[float]]:
        """Recall side: an expected claim is covered only if a predicted claim contains its content."""
        return [[self.containment(e, p) for p in predicted] for e in expected]


@dataclass
class ClaimResult:
    claim: Claim
    matched: bool
    best_match: str
    similarity: float
    reason: str


def _best_matches(claims: list[Claim], others: list[Claim], sim_rows, threshold: float) -> list[ClaimResult]:
    results = []
    for i, claim in enumerate(claims):
        if not others:
            results.append(ClaimResult(claim, False, "", 0.0, "nothing to match"))
            continue
        order = sorted(range(len(others)), key=lambda j: -sim_rows[i][j])
        best = order[0]
        result = ClaimResult(claim, False, others[best].text, float(sim_rows[i][best]), "below threshold")
        for j in order:
            if sim_rows[i][j] < threshold:
                break
            reason = conflict(claim, others[j])
            if not reason:
                result = ClaimResult(claim, True, others[j].text, float(sim_rows[i][j]), "")
                break
            if j == best:
                result.reason = reason
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def f_beta(precision: float, recall: float, beta: float) -> float:
    if precision + recall == 0:
        return 0.0
    b2 = beta * beta
    return (1 + b2) * precision * recall / (b2 * precision + recall)


@dataclass
class RowScore:
    row_id: str
    predicted: list[ClaimResult] = field(default_factory=list)
    expected: list[ClaimResult] = field(default_factory=list)

    @property
    def n_pred(self) -> int:
        return len(self.predicted)

    @property
    def n_exp(self) -> int:
        return len(self.expected)

    @property
    def supported(self) -> int:
        return sum(r.matched for r in self.predicted)

    @property
    def covered(self) -> int:
        return sum(r.matched for r in self.expected)

    @property
    def fp(self) -> int:
        return self.n_pred - self.supported

    @property
    def fn(self) -> int:
        return self.n_exp - self.covered

    @property
    def precision(self) -> float:
        if self.n_pred == 0:
            return 1.0 if self.n_exp == 0 else 0.0
        return self.supported / self.n_pred

    @property
    def recall(self) -> float:
        return 1.0 if self.n_exp == 0 else self.covered / self.n_exp

    @property
    def f1(self) -> float:
        return f_beta(self.precision, self.recall, 1.0)


def score_row(row_id: str, expected: list[Claim], predicted: list[Claim],
              vectorizer: ClaimVectorizer, threshold: float) -> RowScore:
    score = RowScore(row_id)
    if predicted and expected:
        score.predicted = _best_matches(predicted, expected, vectorizer.support(predicted, expected), threshold)
        score.expected = _best_matches(expected, predicted, vectorizer.coverage(expected, predicted), threshold)
    else:
        score.predicted = _best_matches(predicted, [], [], threshold)
        score.expected = _best_matches(expected, [], [], threshold)
    return score


def summarize(rows: list[RowScore]) -> dict:
    n_pred = sum(r.n_pred for r in rows)
    n_exp = sum(r.n_exp for r in rows)
    micro_p = sum(r.supported for r in rows) / n_pred if n_pred else 1.0
    micro_r = sum(r.covered for r in rows) / n_exp if n_exp else 1.0
    n = len(rows) or 1
    macro_p = sum(r.precision for r in rows) / n
    macro_r = sum(r.recall for r in rows) / n
    return {
        "rows": len(rows),
        "expected_claims": n_exp,
        "predicted_claims": n_pred,
        "false_positives": sum(r.fp for r in rows),
        "false_negatives": sum(r.fn for r in rows),
        "micro": {"precision": micro_p, "recall": micro_r, "f1": f_beta(micro_p, micro_r, 1.0)},
        "macro": {"precision": macro_p, "recall": macro_r, "f1": sum(r.f1 for r in rows) / n},
        "final_score": f_beta(micro_p, micro_r, BETA),
    }


# ---------------------------------------------------------------------------
# Dataset I/O
# ---------------------------------------------------------------------------

def load_expected() -> list[dict]:
    if not EXPECTED_CSV.exists():
        sys.exit(f"Error: {EXPECTED_CSV.name} not found.")
    with open(EXPECTED_CSV, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"Error: {EXPECTED_CSV.name} is empty.")
    return rows


def load_predicted() -> dict[str, str]:
    if not PREDICTED_CSV.exists():
        return {}
    with open(PREDICTED_CSV, newline="", encoding="utf-8-sig") as f:
        return {row["id"]: row.get("predicted_outcome") or "" for row in csv.DictReader(f)}


def write_predicted(predictions: dict[str, str], ids: list[str]) -> None:
    with open(PREDICTED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "predicted_outcome"])
        writer.writeheader()
        for row_id in ids:
            writer.writerow({"id": row_id, "predicted_outcome": predictions.get(row_id, "")})


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def engine_version() -> str:
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *ENGINE_PATHS], cwd=ROOT).returncode
        return f"{commit}+uncommitted-engine-changes" if dirty else commit
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_export(_args) -> None:
    """Writes every plan to eval_plans/ for manual `sparklens analyze <file> --eval` runs."""
    rows = load_expected()
    PLANS_DIR.mkdir(exist_ok=True)
    for row in rows:
        (PLANS_DIR / f"{row['id']}.txt").write_text(row["script"], encoding="utf-8")
    print(f"Wrote {len(rows)} plan files to {PLANS_DIR.name}/")

    if PREDICTED_CSV.exists():
        print(f"{PREDICTED_CSV.name} already exists - left untouched.")
    else:
        write_predicted({}, [row["id"] for row in rows])
        print(f"Created {PREDICTED_CSV.name} template with empty predicted_outcome cells.")

    first = rows[0]["id"]
    print("\nFor each plan run, then paste the single output line into its predicted_outcome cell:")
    print(f"  python -m cli.main analyze {PLANS_DIR.name}/{first}.txt --eval")
    print(f"  (or, if installed: sparklens analyze {PLANS_DIR.name}/{first}.txt --eval)")


def _run_cli(plan_file: Path) -> tuple[str, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "cli.main", "analyze", str(plan_file), "--eval"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode != 0 or not lines:
        return "", (proc.stderr.strip().splitlines() or ["no output"])[-1]
    return lines[-1].strip(), ""


def cmd_predict(args) -> None:
    """Fills dataset_predicted.csv by running the exact CLI command of the manual route."""
    rows = load_expected()
    existing = load_predicted()
    if any(v.strip() for v in existing.values()) and not args.force:
        sys.exit(f"{PREDICTED_CSV.name} already has predictions. Re-run with --force to overwrite them.")

    ids = [row["id"] for row in rows]
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for row in rows:
            path = Path(tmp) / f"{row['id']}.txt"
            path.write_text(row["script"], encoding="utf-8")
            files.append(path)
        print(f"Running `python -m cli.main analyze <plan> --eval` on {len(files)} plans...")
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            outputs = list(pool.map(_run_cli, files))

    predictions = {}
    for row_id, (text, error) in zip(ids, outputs):
        predictions[row_id] = text
        if error:
            print(f"  {row_id}: FAILED ({error})")
    write_predicted(predictions, ids)
    print(f"Saved {sum(bool(t) for t, _ in outputs)}/{len(ids)} predictions to {PREDICTED_CSV.name}")


def _config(args) -> dict:
    return {
        "vectorizer": args.vectorizer,
        "threshold": args.threshold,
        "concept_weight": CONCEPT_WEIGHT,
        "free_weight": FREE_WEIGHT,
        "beta": BETA,
    }


def run_evaluation(args) -> tuple[list[RowScore], dict, list[str]]:
    expected_rows = load_expected()
    predicted = load_predicted()
    if not predicted:
        sys.exit(f"Error: {PREDICTED_CSV.name} not found. Run `export` (manual) or `predict` first.")

    skipped = [row["id"] for row in expected_rows if not predicted.get(row["id"], "").strip()]
    unknown = sorted(set(predicted) - {row["id"] for row in expected_rows})
    if unknown:
        print(f"Warning: ids in {PREDICTED_CSV.name} not in {EXPECTED_CSV.name}: {', '.join(unknown)}")
    if skipped:
        print(f"Warning: {len(skipped)} row(s) have no prediction and are excluded: {', '.join(skipped)}")

    scored = [row for row in expected_rows if row["id"] not in skipped]
    expected_claims = {row["id"]: split_claims(row["expected_outcome"]) for row in expected_rows}
    vectorizer = ClaimVectorizer(args.vectorizer).fit(
        [c for claims in expected_claims.values() for c in claims]
    )
    rows = [
        score_row(row["id"], expected_claims[row["id"]], split_claims(predicted[row["id"]]),
                  vectorizer, args.threshold)
        for row in scored
    ]
    return rows, summarize(rows), skipped


def print_report(rows: list[RowScore], summary: dict, args) -> None:
    width = max([len(r.row_id) for r in rows] + [4])
    print(f"\n--- SparkLens rule-engine evaluation ({args.vectorizer}, threshold={args.threshold}) ---\n")
    print(f"{'id':<{width}}  exp pred   FP   FN   prec  recall    f1")
    for r in rows:
        print(f"{r.row_id:<{width}}  {r.n_exp:>3} {r.n_pred:>4} {r.fp:>4} {r.fn:>4}"
              f"  {r.precision:5.2f}  {r.recall:6.2f}  {r.f1:4.2f}")

    micro, macro = summary["micro"], summary["macro"]
    print(f"\nClaims: {summary['expected_claims']} expected, {summary['predicted_claims']} predicted, "
          f"{summary['false_positives']} false positives, {summary['false_negatives']} false negatives")
    print(f"Micro  precision {micro['precision']:.3f}   recall {micro['recall']:.3f}   F1 {micro['f1']:.3f}")
    print(f"Macro  precision {macro['precision']:.3f}   recall {macro['recall']:.3f}   F1 {macro['f1']:.3f}")
    print(f"\nFINAL SCORE (F{BETA}, precision-weighted, 0-1): {summary['final_score']:.3f}")


def write_review(rows: list[RowScore]) -> None:
    """Per-claim verdicts, so every number in the report can be traced to sentences."""
    records = []
    for row in rows:
        for side, results, hit, miss in (("predicted", row.predicted, "TP", "FP"),
                                         ("expected", row.expected, "TP", "FN")):
            for r in results:
                records.append({
                    "id": row.row_id, "side": side, "claim": r.claim.text,
                    "best_match": r.best_match, "similarity": f"{r.similarity:.3f}",
                    "verdict": hit if r.matched else miss, "reason": r.reason,
                })

    with open(REVIEW_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]) if records else ["id"])
        writer.writeheader()
        writer.writerows(records)
    print(f"\nWrote per-claim verdicts to {REVIEW_CSV.name}")


def compare_with_baseline(rows: list[RowScore], summary: dict, config: dict) -> None:
    if not BASELINE_JSON.exists():
        print(f"\nNo {BASELINE_JSON.name} yet - run `python evaluate_engine.py baseline` to freeze one.")
        return
    base = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    print(f"\n--- Change vs baseline ({base['created'][:10]}, engine {base['engine_version']}) ---")
    if base["config"] != config:
        print(f"Warning: scoring config differs from the baseline ({base['config']}); numbers are not comparable.")
        return
    if base["expected_sha256"] != sha256(EXPECTED_CSV):
        print(f"Warning: {EXPECTED_CSV.name} changed since the baseline; numbers are not comparable.")
        return

    old = base["summary"]
    for label, now, then in (
        ("Precision", summary["micro"]["precision"], old["micro"]["precision"]),
        ("Recall", summary["micro"]["recall"], old["micro"]["recall"]),
        ("F1", summary["micro"]["f1"], old["micro"]["f1"]),
        ("Final score", summary["final_score"], old["final_score"]),
    ):
        print(f"{label:<12} {then:.3f} -> {now:.3f}  ({now - then:+.3f})")

    improved, regressed = [], []
    for r in rows:
        before = base["rows"].get(r.row_id)
        if before is None:
            continue
        delta = r.f1 - before["f1"]
        if delta > 1e-9:
            improved.append((r.row_id, before["f1"], r.f1))
        elif delta < -1e-9:
            regressed.append((r.row_id, before["f1"], r.f1))
    print(f"Rows improved: {len(improved)}   regressed: {len(regressed)}")
    for row_id, then, now in regressed:
        print(f"  regressed  {row_id}: F1 {then:.2f} -> {now:.2f}")


def cmd_evaluate(args) -> None:
    rows, summary, _ = run_evaluation(args)
    print_report(rows, summary, args)
    write_review(rows)
    compare_with_baseline(rows, summary, _config(args))


def cmd_baseline(args) -> None:
    rows, summary, skipped = run_evaluation(args)
    if skipped:
        sys.exit("Refusing to save a baseline while predictions are missing.")
    print_report(rows, summary, args)
    write_review(rows)
    validation, _, _ = run_validation(args)
    print(f"\nEvaluator accuracy on {validation['overall']['cases']} known-answer cases: "
          f"{validation['overall']['accuracy']:.1%} (run `validate` for details)")
    baseline = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "engine_version": engine_version(),
        "expected_sha256": sha256(EXPECTED_CSV),
        "predicted_sha256": sha256(PREDICTED_CSV),
        "validation_sha256": sha256(VALIDATION_CSV),
        "config": _config(args),
        "summary": summary,
        "validation": validation,
        "rows": {
            r.row_id: {"expected": r.n_exp, "predicted": r.n_pred, "fp": r.fp, "fn": r.fn,
                       "precision": r.precision, "recall": r.recall, "f1": r.f1}
            for r in rows
        },
    }
    BASELINE_JSON.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved baseline to {BASELINE_JSON.name} (engine {baseline['engine_version']})")


# ---------------------------------------------------------------------------
# Validation suite: known-answer tests for the evaluator itself
# ---------------------------------------------------------------------------
#
# Every case pairs a hypothesis claim with a premise paragraph and an answer that is
# known by construction, so the evaluator's own accuracy is measured without human
# labelling. LLM-written cases (paraphrases, role swaps) come from eval_validation.csv;
# rule-based cases are generated here from the ground truth and the plan text.

VALIDATION_CSV = ROOT / "eval_validation.csv"
VALIDATION_FAILURES_CSV = ROOT / "eval_validation_failures.csv"
DEV_PLAN_LIMIT = 25        # plans 01-25 form the development split, plans 26-50 the held-out test split
TRANSPLANTS_PER_PLAN = 3   # cross-plan cases per plan and direction

# Plan-text evidence for operator-level concepts. A claim that plainly asserts one of these
# concepts is false for a plan whose text has no such operator - no judgement involved.
PLAN_EVIDENCE = {
    "sortmergejoin": r"SortMergeJoin",
    "broadcastjoin": r"BroadcastHashJoin",
    "shuffledhashjoin": r"ShuffledHashJoin",
    "nestedloopjoin": r"BroadcastNestedLoopJoin",
    "cartesianjoin": r"CartesianProduct",
    "semijoin": r"LeftSemi",
    "antijoin": r"LeftAnti",
    "outerjoin": r"(?:Full|Left|Right)Outer",
    "hashpartitioning": r"hashpartitioning\(",
    "rangepartitioning": r"rangepartitioning\(",
    "roundrobinpartitioning": r"RoundRobinPartitioning",
    "reusedexchange": r"ReusedExchange",
    "window": r"\bWindow \(",
    "expand": r"\bExpand \(",
    "generate": r"\bGenerate \(",
    "union": r"\bUnion \(",
    "topn": r"TakeOrderedAndProject",
    "objecthashagg": r"ObjectHashAggregate",
    "countdistinct": r"count\(distinct",
    "pythonudf": r"(?:BatchEval|ArrowEval)Python",
    "photon": r"Photon",
}

# Rewrites that turn a true claim into its opposite (first matching rule wins, case-insensitive).
POLARITY_FLIPS = [
    (r"\bnot a real bottleneck\b", "a real bottleneck"),
    (r"\bnot a bottleneck\b", "a bottleneck"),
    (r"\ba (?:severe|serious) bottleneck\b", "not a bottleneck"),
    (r"\bneither side needs an exchange\b", "both sides need an exchange"),
    (r"\bneeds no shuffle\b", "needs a shuffle"),
    (r"\bno additional exchange\b", "an additional exchange"),
    (r"\bno extra exchange\b", "an extra exchange"),
    (r"\bwith no data movement\b", "with heavy data movement"),
    (r"\bwithout moving data\b", "by moving data"),
    (r"\bwithout a shuffle\b", "with a shuffle"),
    (r"\bwithout shuffling\b", "with shuffling"),
    (r"\bwithout a sort step\b", "with a sort step"),
    (r"\bwith no shuffle\b", "with a shuffle"),
    (r"\bno shuffle\b", "a shuffle"),
    (r"\bnever shuffled\b", "shuffled"),
    (r"\bcannot be broadcast\b", "can be broadcast"),
    (r"\bcannot be coalesced\b", "can be coalesced"),
    (r"\bcannot split\b", "can split"),
    (r"\bnot sorted\b", "sorted"),
    (r"\bis structurally required\b", "is not required"),
    (r"\b(is|are) required\b", r"\1 not required"),
    (r"\bis needed\b", "is not needed"),
    (r"\bunavoidable\b", "avoidable"),
    (r"\bavoidable\b", "unavoidable"),
    (r"\bunnecessary\b", "necessary"),
    (r"\bnecessary\b", "unnecessary"),
    (r"\bredundant\b", "required"),
    (r"\bis enabled\b", "is disabled"),
    (r"\b(is|are) disabled\b", r"\1 enabled"),
    (r"\bturned off\b", "turned on"),
    (r"\bturned on\b", "turned off"),
    (r"\bswitched off\b", "switched on"),
    (r"\bis off\b", "is on"),
    (r"\bdescending\b", "ascending"),
    (r"\bascending\b", "descending"),
    (r"\bvery expensive\b", "cheap"),
    (r"\bmore expensive\b", "cheaper"),
    (r"\bcostly\b", "cheap"),
    (r"\bis cheap\b", "is expensive"),
]

# Swap one Spark concept for a sibling; only used when the plan has no evidence of the new one.
CONCEPT_SWAPS = [
    (r"\bsort[- ]merge join\b", "broadcast hash join", r"BroadcastHashJoin"),
    (r"\bbroadcast nested loop join\b", "sort-merge join", r"SortMergeJoin"),
    (r"\bbroadcast hash joins?\b", "sort-merge join", r"SortMergeJoin"),
    (r"\bshuffled hash join\b", "sort-merge join", r"SortMergeJoin"),
    (r"\bCartesianProduct\b", "BroadcastHashJoin", r"BroadcastHashJoin"),
    (r"\bleft semi\b", "left anti", r"LeftAnti"),
    (r"\bleft anti\b", "left semi", r"LeftSemi"),
    (r"\bfull outer join\b", "left semi join", r"LeftSemi"),
    (r"\bhash-partition", "range-partition", r"rangepartitioning\("),
    (r"\bhash partitioning\b", "range partitioning", r"rangepartitioning\("),
    (r"\brange-partition", "hash-partition", r"hashpartitioning\("),
    (r"\brange partitioning\b", "hash partitioning", r"hashpartitioning\("),
    (r"\bround-robin\b", "range-partitioned", r"rangepartitioning\("),
    (r"\bSinglePartition exchange\b", "RoundRobinPartitioning exchange", r"RoundRobinPartitioning"),
    (r"\bReusedExchange\b", "BroadcastExchange", r"BroadcastExchange"),
    (r"\bObjectHashAggregate\b", "SortAggregate", r"SortAggregate"),
    (r"\bExpand\b", "Generate", r"\bGenerate \("),
    (r"\bGenerate\b", "Expand", r"\bExpand \("),
    (r"\bParquet\b", "CSV", r"Scan csv"),
    (r"\bCSV\b", "Parquet", r"Scan parquet"),
    (r"\bTakeOrderedAndProject\b", "global Sort with a range shuffle", r"rangepartitioning\("),
]

_NUMBER = re.compile(r"\d+(?:,\d{3})*")
# A new SparkLens finding starts after a sentence end with "Title: " (used to reorder findings).
_FINDING_START = re.compile(r"(?<=[.!?])\s+(?=[A-Z][\w /()'-]{2,60}?: )")


@dataclass
class Case:
    category: str
    direction: str          # "support": precision side, "cover": recall side
    row_id: str
    hypothesis: Claim
    premise: list[Claim]
    should_match: bool
    source: str             # "llm" or "rule"

    @property
    def split(self) -> str:
        return "dev" if int(self.row_id[:2]) <= DEV_PLAN_LIMIT else "test"


def _replace(text: str, m: re.Match, replacement: str) -> str:
    if m.group(0)[:1].isupper():
        replacement = replacement[:1].upper() + replacement[1:]
    return text[:m.start()] + replacement + text[m.end():]


def _rewrite(original: Claim, text: str) -> Claim:
    """A rewritten claim keeps whatever context its original inherited from a previous sentence."""
    tokens = normalize(text)
    inherited = [t for t in original.inherited if t not in tokens]
    return Claim(text, tokens + inherited, tuple(inherited))


def _corruptions(text: str, plan: str):
    """Yields (category, corrupted text, changed target) - each corruption makes the claim false."""
    if _NUMBER.search(text):
        bumped = _NUMBER.sub(lambda m: str(int(m.group(0).replace(",", "")) + 1), text)
        yield "number_change", bumped, ("numbers", set(_NUMBER.findall(text.replace(",", ""))))
    for pattern, replacement in POLARITY_FLIPS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            yield "polarity_flip", _replace(text, m, m.expand(replacement)), ("text", m.group(0))
            break
    for pattern, replacement, evidence in CONCEPT_SWAPS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m and not re.search(evidence, plan):
            yield "concept_swap", _replace(text, m, replacement), ("text", m.group(0))
            break


def _appears_elsewhere(target: tuple, other_texts: list[str]) -> bool:
    """True if another claim of the plan states the same thing, so a recall-side label would be unsure."""
    kind, value = target
    if kind == "numbers":
        return any(value & set(_NUMBER.findall(t.replace(",", ""))) for t in other_texts)
    return any(value.lower() in t.lower() for t in other_texts)


def _asserted_operators(claim: Claim) -> list[str]:
    """Operator-level concepts a claim plainly asserts (not negated, hedged, advised or via a pronoun)."""
    tokens = set(claim.tokens)
    if _ANAPHORA.match(claim.text) or "recommend" in tokens or any(_is_marked_concept(t) for t in tokens):
        return []
    return sorted(t for t in tokens if t in PLAN_EVIDENCE)


def _missing_from(concepts: list[str], plan: str) -> list[str]:
    return [c for c in concepts if not re.search(PLAN_EVIDENCE[c], plan)]


def _transplants(ids, claims, plans, paraphrased) -> list[Case]:
    """Claims moved to a plan whose text has no operator for them: must not match."""
    cases = []
    n = len(ids)
    for k, row_id in enumerate(ids):
        # precision side: another plan's claim, judged against this plan's ground truth
        picked = 0
        for step in range(1, n):
            other = ids[(k + 7 * step) % n]          # 7 and 50 are coprime: visits every other plan
            claim = next((c for c in claims[other]
                          if _missing_from(_asserted_operators(c), plans[row_id])), None)
            if claim:
                cases.append(Case("cross_plan", "support", row_id, claim, claims[row_id], False, "rule"))
                picked += 1
            if picked == TRANSPLANTS_PER_PLAN:
                break
        # recall side: this plan's true claim, judged against another plan's (paraphrased) analysis
        picked = 0
        for claim in claims[row_id]:
            operators = _asserted_operators(claim)
            if not operators or _missing_from(operators, plans[row_id]):
                continue
            for step in range(1, n):
                other = ids[(k + 7 * step) % n]
                if paraphrased[other] and _missing_from(operators, plans[other]):
                    premise = split_claims(" ".join(paraphrased[other]))
                    cases.append(Case("cross_plan", "cover", row_id, claim, premise, False, "rule"))
                    picked += 1
                    break
            if picked == TRANSPLANTS_PER_PLAN:
                break
    return cases


def build_validation_cases(expected_rows: list[dict]) -> tuple[list[Case], list[str]]:
    notes = []
    ids = [r["id"] for r in expected_rows]
    plans = {r["id"]: r["script"] for r in expected_rows}
    claims = {r["id"]: split_claims(r["expected_outcome"]) for r in expected_rows}

    records = []
    if VALIDATION_CSV.exists():
        with open(VALIDATION_CSV, newline="", encoding="utf-8-sig") as f:
            records = list(csv.DictReader(f))
    else:
        notes.append(f"{VALIDATION_CSV.name} not found: running rule-based cases only")

    paraphrase_of = {(r["row_id"], r["claim"]): r["rewrite"] for r in records if r["kind"] == "paraphrase"}
    known = {(row_id, c.text) for row_id in ids for c in claims[row_id]}
    stale = sum((r["row_id"], r["claim"]) not in known for r in records)
    paraphrased = {}
    missing = 0
    for row_id in ids:
        texts = [paraphrase_of.get((row_id, c.text)) for c in claims[row_id]]
        missing += texts.count(None)
        paraphrased[row_id] = texts if None not in texts else None
    if missing:
        notes.append(f"{missing} ground-truth claims have no paraphrase in {VALIDATION_CSV.name}")
    if stale:
        notes.append(f"{stale} cases in {VALIDATION_CSV.name} refer to claims no longer in the ground truth")

    cases = []
    for row_id in ids:
        truth, paras = claims[row_id], paraphrased[row_id]
        for i, claim in enumerate(truth):
            if paras:
                cases.append(Case("paraphrase", "support", row_id, _rewrite(claim, paras[i]), truth, True, "llm"))
                cases.append(Case("paraphrase", "cover", row_id, claim,
                                  split_claims(" ".join(paras)), True, "llm"))
            others = [c.text for j, c in enumerate(truth) if j != i]
            for category, corrupted, target in _corruptions(claim.text, plans[row_id]):
                cases.append(Case(category, "support", row_id, _rewrite(claim, corrupted), truth, False, "rule"))
                if paras and not _appears_elsewhere(target, others):
                    premise = split_claims(" ".join(paras[:i] + [corrupted] + paras[i + 1:]))
                    cases.append(Case(category, "cover", row_id, claim, premise, False, "rule"))

    for r in records:
        if r["kind"] != "role_swap" or (r["row_id"], r["claim"]) not in known:
            continue
        original = next(c for c in claims[r["row_id"]] if c.text == r["claim"])
        cases.append(Case("role_swap", "support", r["row_id"], _rewrite(original, r["rewrite"]),
                          claims[r["row_id"]], r["label"] == "match", "llm"))

    cases += _transplants(ids, claims, plans, paraphrased)
    return cases, notes


def _judge(case: Case, vectorizer: ClaimVectorizer, threshold: float) -> ClaimResult:
    if case.direction == "support":
        scores = vectorizer.support([case.hypothesis], case.premise)
    else:
        scores = vectorizer.coverage([case.hypothesis], case.premise)
    return _best_matches([case.hypothesis], case.premise, scores, threshold)[0]


def _invariance(expected_rows, predicted, vectorizer, threshold) -> tuple[int, list[str]]:
    """Reordering, duplicating or re-spacing SparkLens findings must not change a plan's scores."""
    checks, failed = 0, []
    for r in expected_rows:
        text = " ".join(predicted.get(r["id"], "").split())
        if not text:
            continue
        truth = split_claims(r["expected_outcome"])
        findings = [f for f in _FINDING_START.split(text) if f.strip()]
        shuffled = findings[:]
        random.Random(int(r["id"][:2])).shuffle(shuffled)
        variants = {
            "reversed order": " ".join(reversed(findings)),
            "shuffled order": " ".join(shuffled),
            "duplicated findings": " ".join(f for f in findings for _ in (0, 1)),
            "extra whitespace": "\n   ".join(findings),
        }
        base = score_row(r["id"], truth, split_claims(text), vectorizer, threshold)
        for name, variant in variants.items():
            checks += 1
            row = score_row(r["id"], truth, split_claims(variant), vectorizer, threshold)
            if (row.precision, row.recall) != (base.precision, base.recall):
                failed.append(f"{r['id']}: {name}")
    return checks, failed


def _bounds(expected_rows, predicted, vectorizer, threshold) -> dict:
    """Ground truth as prediction must score 1, silence 0, and another plan's output far below real output."""
    ids = [r["id"] for r in expected_rows]
    truth = {r["id"]: split_claims(r["expected_outcome"]) for r in expected_rows}

    def score(texts: dict[str, str]) -> dict:
        return summarize([score_row(i, truth[i], split_claims(texts[i]), vectorizer, threshold) for i in ids])

    ceiling = score({r["id"]: r["expected_outcome"] for r in expected_rows})
    floor = score({i: "No issues found." for i in ids})
    bounds = {
        "ceiling_precision": ceiling["micro"]["precision"],
        "ceiling_recall": ceiling["micro"]["recall"],
        "floor_final": floor["final_score"],
    }
    if all(predicted.get(i, "").strip() for i in ids):
        shuffled = []
        for seed in range(5):
            order = ids[:]
            random.Random(seed).shuffle(order)
            shuffled.append(score({i: predicted[j] for i, j in zip(ids, order)})["final_score"])
        bounds["real_final"] = score(predicted)["final_score"]
        bounds["shuffled_final"] = sum(shuffled) / len(shuffled)
    bounds["passed"] = (bounds["ceiling_precision"] == 1.0 and bounds["ceiling_recall"] == 1.0
                        and bounds["floor_final"] == 0.0
                        and bounds.get("shuffled_final", 0.0) < bounds.get("real_final", 1.0))
    return bounds


def _rates(results: list[tuple[Case, ClaimResult]]) -> dict:
    positives = [(c, r) for c, r in results if c.should_match]
    negatives = [(c, r) for c, r in results if not c.should_match]
    correct = sum(r.matched == c.should_match for c, r in results)
    return {
        "cases": len(results),
        "accuracy": correct / len(results) if results else 1.0,
        "false_accept_rate": sum(r.matched for _, r in negatives) / len(negatives) if negatives else 0.0,
        "false_reject_rate": sum(not r.matched for _, r in positives) / len(positives) if positives else 0.0,
    }


def run_validation(args) -> tuple[dict, list[tuple[Case, ClaimResult]], list[str]]:
    expected_rows = load_expected()
    predicted = load_predicted()
    cases, notes = build_validation_cases(expected_rows)
    vectorizer = ClaimVectorizer(args.vectorizer).fit(
        [c for r in expected_rows for c in split_claims(r["expected_outcome"])]
    )
    results = [(case, _judge(case, vectorizer, args.threshold)) for case in cases]

    groups: dict[str, list] = {}
    for case, result in results:
        groups.setdefault(f"{case.category} / {case.direction}", []).append((case, result))
    checks, failed = _invariance(expected_rows, predicted, vectorizer, args.threshold)
    summary = {
        "overall": _rates(results),
        "dev": _rates([(c, r) for c, r in results if c.split == "dev"]),
        "test": _rates([(c, r) for c, r in results if c.split == "test"]),
        "llm_written": _rates([(c, r) for c, r in results if c.source == "llm"]),
        "rule_based": _rates([(c, r) for c, r in results if c.source == "rule"]),
        "by_category": {name: _rates(items) for name, items in sorted(groups.items())},
        "invariance": {"checks": checks, "passed": checks - len(failed), "failed": failed},
        "bounds": _bounds(expected_rows, predicted, vectorizer, args.threshold),
    }
    return summary, results, notes


def print_validation(summary: dict, args) -> None:
    overall = summary["overall"]
    print(f"\n--- Evaluator validation: {overall['cases']} known-answer cases "
          f"({args.vectorizer}, threshold={args.threshold}) ---\n")
    print(f"{'category / direction':<30} {'cases':>5}  {'accuracy':>8}  {'false-accept':>12}  {'false-reject':>12}")
    for name, rates in summary["by_category"].items():
        print(f"{name:<30} {rates['cases']:>5}  {rates['accuracy']:>8.1%}  "
              f"{rates['false_accept_rate']:>12.1%}  {rates['false_reject_rate']:>12.1%}")
    print()
    for label, key in (("Dev split (plans 01-25)", "dev"), ("Test split (plans 26-50)", "test"),
                       ("LLM-written cases", "llm_written"), ("Rule-based cases", "rule_based")):
        rates = summary[key]
        print(f"{label:<30} {rates['cases']:>5}  {rates['accuracy']:>8.1%}  "
              f"{rates['false_accept_rate']:>12.1%}  {rates['false_reject_rate']:>12.1%}")
    print(f"\nOVERALL ACCURACY: {overall['accuracy']:.1%}   "
          f"false-accept {overall['false_accept_rate']:.1%} (would inflate SparkLens's score)   "
          f"false-reject {overall['false_reject_rate']:.1%} (would deflate it)")

    inv = summary["invariance"]
    print(f"\nInvariance (reorder / duplicate / re-space findings): {inv['passed']}/{inv['checks']} "
          f"{'PASS' if inv['passed'] == inv['checks'] else 'FAIL'}")
    for failure in inv["failed"][:10]:
        print(f"  changed: {failure}")
    b = summary["bounds"]
    line = (f"Bounds: ground truth as prediction P={b['ceiling_precision']:.3f} R={b['ceiling_recall']:.3f}, "
            f"'No issues found.' final={b['floor_final']:.3f}")
    if "real_final" in b:
        line += f", other plans' output {b['shuffled_final']:.3f} < real {b['real_final']:.3f}"
    print(f"{line}  {'PASS' if b['passed'] else 'FAIL'}")


def write_validation_failures(results: list[tuple[Case, ClaimResult]]) -> None:
    failures = [(c, r) for c, r in results if r.matched != c.should_match]
    with open(VALIDATION_FAILURES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["row_id", "split", "category", "direction", "source", "should_match",
                         "evaluator_matched", "score", "hypothesis", "best_premise_match", "reason"])
        for c, r in failures:
            writer.writerow([c.row_id, c.split, c.category, c.direction, c.source, c.should_match,
                             r.matched, f"{r.similarity:.3f}", c.hypothesis.text, r.best_match, r.reason])
    print(f"\nWrote {len(failures)} wrongly judged cases to {VALIDATION_FAILURES_CSV.name}")


def cmd_validate(args) -> None:
    summary, results, notes = run_validation(args)
    for note in notes:
        print(f"Note: {note}")
    print_validation(summary, args)
    write_validation_failures(results)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

# (expected-style wording, engine-style wording): same meaning, different words.
PARAPHRASES = [
    ("Both inputs are shuffled and sorted for a sort-merge join on customer_id.",
     "Sort Merge Join Detected: Spark selected a Sort Merge Join. This strategy usually requires both inputs "
     "to be shuffled and sorted before the join."),
    ("The small customers table is sent to every executor as a broadcast, so the large side is never shuffled.",
     "Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator."),
    ("Adaptive query execution is turned on for this query.",
     "AQE Enabled: Adaptive Query Execution is enabled, allowing Spark to adjust shuffle partitions, "
     "join strategies, and skew handling at runtime based on observed data statistics."),
    ("Rows are hash-partitioned on product_id.",
     "Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors."),
    ("The global ORDER BY range-partitions the rows so every partition holds a contiguous key range.",
     "Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering."),
    ("Every row is funnelled into one partition, so a single task does all the work.",
     "Single Partition Bottleneck: The execution plan contains a SinglePartition exchange, which may "
     "reduce parallelism by processing data in a single partition."),
    ("The job is split into 3 stages.",
     "Estimated Stage Count: The execution plan is expected to contain 3 Spark stage(s)."),
    ("Rows come out ordered by total_amount, highest first.",
     "Sort Operation Detected: Spark sorts the dataset before downstream processing. Sort order: Descending."),
    ("Aggregation happens in two phases: a map-side partial aggregate, then a final merge after the shuffle.",
     "Two-Phase Aggregation: Spark performs a partial (map-side) aggregation followed by a final merge "
     "aggregation."),
    ("The exchange feeding the final aggregate is mandatory for correctness.",
     "Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data "
     "so the final aggregation can combine results across partitions."),
    ("Eight narrow operators are fused into one long pipeline with no shuffle between them.",
     "Complex Transformation Pipeline: A pipeline containing 8 operators executes without an intermediate "
     "shuffle."),
]

# Pairs that share vocabulary but must NOT match.
NON_MATCHES = [
    ("The small customers table is broadcast to every executor.",
     "Sort Merge Join Detected: Spark selected a Sort Merge Join."),
    ("The job is split into 2 stages.",
     "Estimated Stage Count: The execution plan is expected to contain 4 Spark stage(s)."),
    ("This shuffle is avoidable and adds needless network traffic.",
     "Required Shuffle (Aggregation): This exchange is required by the two-phase aggregation strategy."),
    ("Rows are hash-partitioned on product_id.",
     "Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering."),
    ("Adaptive query execution is turned on.",
     "Sort Operation Detected: Spark sorts the dataset before downstream processing."),
    ("The cross join produces a Cartesian product of both inputs.",
     "Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator."),
    ("A Python UDF forces every row through a separate Python worker.",
     "Aggregation: Spark performs an aggregation operation."),
    ("Adaptive query execution is switched off for this query.",
     "AQE Enabled: Adaptive Query Execution is enabled, allowing Spark to adjust shuffle partitions at runtime."),
    ("The final output is sorted in ascending order of order_id.",
     "Sort Operation Detected: Spark sorts the dataset before downstream processing. Sort order: Descending."),
    ("Only one row per partition reaches the exchange, so it is not a real bottleneck.",
     "This may limit parallelism."),
    ("The query has 2 stages.",
     "Exchange Operator: Spark exchanges data between execution stages."),
    ("This exchange is required so rows of one key meet in the same partition.",
     "Whether this exchange is required is determined by ExecutionQualityRule's evidence for this operator."),
    ("The rollup is implemented with an Expand operator that emits each row once per grouping set.",
     "Aggregation: Spark performs an aggregation operation."),
    # A generic claim must not count as covering a specific one that merely mentions the same topic.
    ("The HAVING-style filter on the count runs after the final aggregate.",
     "Aggregation: Spark performs an aggregation operation."),
    ("Rows are hash-partitioned on product_id before the final aggregate.",
     "Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors."),
]


def _pair_match(vectorizer: ClaimVectorizer, expected: str, engine: str, threshold: float) -> tuple[bool, float, str]:
    """Both directions must pass: the engine claim is supported and the expected claim is covered."""
    e, p = split_claims(expected)[0], Claim(engine, normalize(engine))
    score = min(vectorizer.support([p], [e])[0][0], vectorizer.coverage([e], [p])[0][0])
    reason = conflict(e, p)
    return score >= threshold and not reason, score, reason


def cmd_selftest(args) -> None:
    failures = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        failures += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}{'  ' + detail if detail else ''}")

    # Claim splitting
    claims = split_claims("Shuffle Detected: rows move (e.g. by key). Shuffle Detected: rows move (e.g. by key). "
                          "Ratio is 0.5; AQE is on.")
    check("splitter keeps e.g./decimals, splits on ;, drops duplicates", len(claims) == 3,
          str([c.text for c in claims]))
    check("'No issues found.' yields no claims", split_claims("No issues found.") == [])

    # Normalisation
    same = normalize("SortMergeJoin") == normalize("sort-merge join") == normalize("SMJ")
    check("SortMergeJoin / sort-merge join / SMJ normalise identically", same)
    check("'not required' becomes 'redundant'", "redundant" in normalize("this shuffle is not required"))

    # Matching
    reference = [split_claims(e)[0] for e, _ in PARAPHRASES + NON_MATCHES]
    vectorizer = ClaimVectorizer(args.vectorizer).fit(reference)
    for expected, engine in PARAPHRASES:
        ok, sim, reason = _pair_match(vectorizer, expected, engine, args.threshold)
        check(f"match     sim={sim:.2f} {reason:<17} {expected[:60]}", ok)
    for expected, engine in NON_MATCHES:
        ok, sim, reason = _pair_match(vectorizer, expected, engine, args.threshold)
        check(f"no-match  sim={sim:.2f} {reason:<17} {expected[:60]}", not ok)

    # Metric arithmetic: 3 predicted (2 supported), 4 expected (2 covered)
    row = RowScore("toy")
    row.predicted = [ClaimResult(Claim("p", ["p"]), m, "", 0, "") for m in (True, True, False)]
    row.expected = [ClaimResult(Claim("e", ["e"]), m, "", 0, "") for m in (True, True, False, False)]
    summary = summarize([row])
    check("precision 2/3, recall 2/4", abs(row.precision - 2 / 3) < 1e-9 and abs(row.recall - 0.5) < 1e-9)
    expected_f05 = 1.25 * (2 / 3) * 0.5 / (0.25 * (2 / 3) + 0.5)
    check("final score = F0.5 of micro precision/recall", abs(summary["final_score"] - expected_f05) < 1e-9)
    empty = RowScore("empty")
    check("empty expected + empty predicted scores 1.0", empty.precision == 1.0 and empty.recall == 1.0)

    print(f"\n{'All checks passed.' if not failures else f'{failures} check(s) FAILED.'}")
    sys.exit(1 if failures else 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the SparkLens rule engine against the dataset.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("export", help="write eval_plans/<id>.txt and a predicted template for manual CLI runs")

    predict = sub.add_parser("predict", help="fill dataset_predicted.csv by running the CLI (--eval) on each plan")
    predict.add_argument("--force", action="store_true", help="overwrite existing predictions")
    predict.add_argument("--workers", type=int, default=4, help="parallel CLI processes (default 4)")

    for name, help_text in (("evaluate", "score predictions vs expected outcomes"),
                            ("baseline", "evaluate and freeze the result as eval_baseline.json"),
                            ("validate", "measure the evaluator itself on known-answer test cases"),
                            ("selftest", "offline sanity checks of the matcher and metrics")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--vectorizer", choices=["tfidf", "count"], default="tfidf")
        p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                       help=f"minimum similarity for two claims to match (default {DEFAULT_THRESHOLD})")

    args = parser.parse_args()
    {
        "export": cmd_export,
        "predict": cmd_predict,
        "evaluate": cmd_evaluate,
        "baseline": cmd_baseline,
        "validate": cmd_validate,
        "selftest": cmd_selftest,
    }[args.command](args)


if __name__ == "__main__":
    main()
