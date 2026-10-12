# SparkLens Analysis Report

## Executive Summary

AI explanation disabled.

## Findings

### Broadcast Hash Join Detected
Severity: **Low**
Operator: **BroadcastHashJoin**

Spark selected a Broadcast Hash Join for this operator. This strategy is typically efficient when one side of the join is sufficiently small to broadcast.

### Sort Merge Join Detected
Severity: **Medium**
Operator: **SortMergeJoin**

Spark selected a Sort Merge Join. This strategy usually requires both inputs to be shuffled and sorted before the join.

### Broadcast Hash Join Detected
Severity: **Low**
Operator: **BroadcastHashJoin**

Spark selected a Broadcast Hash Join for this operator. This strategy is typically efficient when one side of the join is sufficiently small to broadcast.

### Broadcast Hash Join Detected
Severity: **Low**
Operator: **BroadcastHashJoin**

Spark selected a Broadcast Hash Join for this operator. This strategy is typically efficient when one side of the join is sufficiently small to broadcast.

### Shuffle Detected
Severity: **Medium**
Operator: **Exchange**

A shuffle exchange redistributes data across partitions. Whether this shuffle is required, expected, or an optimization opportunity is determined by ExecutionQualityRule's evidence for this operator.

### Shuffle Detected
Severity: **Medium**
Operator: **Exchange**

A shuffle exchange redistributes data across partitions. Whether this shuffle is required, expected, or an optimization opportunity is determined by ExecutionQualityRule's evidence for this operator.

### Shuffle Detected
Severity: **Medium**
Operator: **Exchange**

A shuffle exchange redistributes data across partitions. Whether this shuffle is required, expected, or an optimization opportunity is determined by ExecutionQualityRule's evidence for this operator.

### Shuffle Detected
Severity: **Medium**
Operator: **Exchange**

A shuffle exchange redistributes data across partitions. Whether this shuffle is required, expected, or an optimization opportunity is determined by ExecutionQualityRule's evidence for this operator.

### Exchange Operator
Severity: **Medium**
Operator: **Exchange**

Spark exchanges data between execution stages. Whether this exchange is required is determined by ExecutionQualityRule's evidence for this operator.

### Exchange Operator
Severity: **Medium**
Operator: **Exchange**

Spark exchanges data between execution stages. Whether this exchange is required is determined by ExecutionQualityRule's evidence for this operator.

### Exchange Operator
Severity: **Medium**
Operator: **Exchange**

Spark exchanges data between execution stages. Whether this exchange is required is determined by ExecutionQualityRule's evidence for this operator.

### Exchange Operator
Severity: **Medium**
Operator: **Exchange**

Spark exchanges data between execution stages. Whether this exchange is required is determined by ExecutionQualityRule's evidence for this operator.

### Aggregation
Severity: **Low**
Operator: **HashAggregate**

Spark performs an aggregation operation.

### Aggregation
Severity: **Low**
Operator: **HashAggregate**

Spark performs an aggregation operation.

### Aggregation
Severity: **Low**
Operator: **HashAggregaterd**

Spark performs an aggregation operation.

### Aggregation
Severity: **Low**
Operator: **HashAggregate**

Spark performs an aggregation operation.

### Sort Operation Detected
Severity: **Medium**
Operator: **Sort**

Spark sorts the dataset before downstream processing.

### Sort Operation Detected
Severity: **Medium**
Operator: **Sort**

Spark sorts the dataset before downstream processing.

### Stage Boundary Detected
Severity: **Low**
Operator: **Exchange**

This Exchange represents a shuffle boundary between Spark execution stages.

### Stage Boundary Detected
Severity: **Low**
Operator: **Exchange**

This Exchange represents a shuffle boundary between Spark execution stages.

### Stage Boundary Detected
Severity: **Low**
Operator: **Exchange**

This Exchange represents a shuffle boundary between Spark execution stages.

### Stage Boundary Detected
Severity: **Low**
Operator: **Exchange**

This Exchange represents a shuffle boundary between Spark execution stages.

### Estimated Stage Count
Severity: **Low**

SparkLens estimates 5 execution stage(s) from 4 shuffle boundary Exchange operator(s).

### Multiple Shuffle Operations
Severity: **Medium**

Multiple shuffle exchanges are present in the execution plan.

### Multiple Sort Operations
Severity: **Medium**

Multiple sort operations are present in the execution plan.

### Multi-Stage Aggregation
Severity: **Low**

Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline.

## Execution Overview

Operators: 32
Edges: 0
Root Nodes: 32
Leaf Nodes: 32
Findings: 26

## Execution Statistics

Stages: 5
Joins: 4
Broadcast Joins: 3
Shuffles: 4
Exchanges: 6
Aggregations: 4
Sorts: 2
Filters: 4
Scans: 6
Max Depth: 1
Complexity: VERY_HIGH (63.0)

## AI Explanation

Only deterministic analysis was executed.
