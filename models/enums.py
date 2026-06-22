from enum import Enum


class OperatorType(str, Enum):
    PROJECT = "Project"
    FILTER = "Filter"
    EXCHANGE = "Exchange"
    SORT = "Sort"
    HASH_AGGREGATE = "HashAggregate"
    SORT_AGGREGATE = "SortAggregate"
    BROADCAST_HASH_JOIN = "BroadcastHashJoin"
    SORT_MERGE_JOIN = "SortMergeJoin"
    SHUFFLE_HASH_JOIN = "ShuffleHashJoin"
    BROADCAST_EXCHANGE = "BroadcastExchange"
    FILE_SCAN = "FileScan"
    UNKNOWN = "Unknown"


class TransformationType(str, Enum):
    NARROW = "Narrow"
    WIDE = "Wide"
    NONE = "None"


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"