import csv
import json
import warnings
from pathlib import Path

# Suppress HuggingFace/transformers warnings for clean output
warnings.filterwarnings("ignore")

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    print("Error: sentence-transformers is required.")
    print("Please install it using: pip install sentence-transformers scikit-learn")
    exit(1)

from services.pipeline import AnalysisPipeline

# Configuration
EXPECTED_CSV = "dataset_expected.csv"
PREDICTED_CSV = "dataset_predicted.csv"

def load_expected_dataset(csv_path: str) -> list[dict]:
    """Loads the expected dataset which contains id, script, and expected_outcome."""
    data = []
    path = Path(csv_path)
    if not path.exists():
        return data
        
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def generate_predictions():
    """Runs the SparkLens engine on scripts directly from the expected CSV."""
    expected_data = load_expected_dataset(EXPECTED_CSV)
    if not expected_data:
        print(f"Error: {EXPECTED_CSV} not found or empty.")
        return

    predictions = []
    pipeline = AnalysisPipeline()
    
    for row in expected_data:
        plan_id = row["id"]
        script = row["script"]
        print(f"Analyzing {plan_id}...")
        
        try:
            # Run the deterministic engine programmatically
            # (Use enable_ai=False to just test the rule engine's findings)
            result = pipeline.run(script, enable_ai=False)
            
            # Extract findings into a textual summary
            findings = result.analysis.report.findings
            if findings:
                predicted_text = " ".join([f"{f.title}: {f.description}" for f in findings])
            else:
                predicted_text = "No issues found."
            
            predictions.append({
                "id": plan_id,
                "predicted_outcome": predicted_text
            })
            
        except Exception as e:
            print(f"Failed to analyze {plan_id}: {e}")
            predictions.append({
                "id": plan_id,
                "predicted_outcome": ""
            })

    # Save predictions to CSV
    with open(PREDICTED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "predicted_outcome"])
        writer.writeheader()
        writer.writerows(predictions)
        
    print(f"Saved {len(predictions)} predictions to {PREDICTED_CSV}")

def evaluate():
    """Compares expected vs predicted outcomes using semantic embeddings."""
    expected_data = load_expected_dataset(EXPECTED_CSV)
    
    predicted_dict = {}
    if Path(PREDICTED_CSV).exists():
        with open(PREDICTED_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                predicted_dict[row["id"]] = row["predicted_outcome"]
    
    if not expected_data or not predicted_dict:
        print("Error: Missing expected or predicted datasets.")
        return

    print("\nLoading AI model for semantic evaluation (this takes a few seconds)...")
    # all-MiniLM-L6-v2 is a fast, lightweight embedding model for semantic similarity
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    total_score = 0.0
    count = 0
    
    print("\n--- Semantic Evaluation Results ---\n")
    
    for row in expected_data:
        doc_id = row["id"]
        expected_text = row["expected_outcome"]
        predicted_text = predicted_dict.get(doc_id)
        
        if predicted_text is None:
            print(f"{doc_id}: Prediction missing")
            continue
            
        # If both are effectively empty/clean, perfect match
        if (not expected_text.strip() or "no issues" in expected_text.lower()) and \
           (not predicted_text.strip() or "no issues" in predicted_text.lower()):
            score = 1.0
        elif not expected_text.strip() or not predicted_text.strip():
            score = 0.0
        else:
            # Generate embeddings
            embeddings = model.encode([expected_text, predicted_text])
            # Compute cosine similarity between the embeddings
            score = float(util.cos_sim(embeddings[0], embeddings[1])[0][0])
            # Clip negative scores to 0 (sometimes very unrelated texts go slightly negative)
            score = max(0.0, score)
            
        print(f"{doc_id}: Semantic Similarity Score = {score:.4f}")
        total_score += score
        count += 1
        
    if count > 0:
        avg_score = total_score / count
        print(f"\nAverage Semantic Score: {avg_score:.4f}")
        print("(Scores range from 0.0 to 1.0. A score > 0.7 usually indicates the same semantic meaning!)")
    else:
        print("No matches found to evaluate.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "predict":
        generate_predictions()
    elif len(sys.argv) > 1 and sys.argv[1] == "evaluate":
        evaluate()
    elif len(sys.argv) > 1 and sys.argv[1] == "all":
        generate_predictions()
        evaluate()
    else:
        print("Usage:")
        print("  python evaluate_engine.py predict   # Generate dataset_predicted.csv")
        print("  python evaluate_engine.py evaluate  # Score predictions vs expected")
        print("  python evaluate_engine.py all       # Do both sequentially")
