# Rule Engine Results

## Final metrics

| Precision | Recall | F1 | F0.5 | Claims | FP | FN |
|---:|---:|---:|---:|---:|---:|---:|
| 0.948 | 0.699 | 0.805 | 0.885 | 521 | 27 | 95 |

Reference target: precision 0.651, recall 0.611, F0.5 0.643.

## Evaluation log

# Rule Engine Evaluation Log

All evaluations use the unchanged evaluator and 50-plan dataset. Regressed
plans are compared with the immediately preceding kept commit.

| Change | Commit | Precision | Recall | F1 | F0.5 | Claims produced | FP | FN | Regressed plan ids | Result |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 7fe0adc | 0.738 | 0.614 | 0.670 | 0.709 | 576 | 151 | 122 | 02_filter_projection, 06_long_narrow_pipeline | kept |
| 2 | 78dd0e6 | 0.840 | 0.614 | 0.709 | 0.782 | 506 | 81 | 122 | 02_filter_projection, 06_long_narrow_pipeline | kept |
| 3 | 5245b3e | 0.896 | 0.611 | 0.726 | 0.819 | 479 | 50 | 123 | 06_long_narrow_pipeline | kept |
| 4 | d50dbac | 0.916 | 0.611 | 0.733 | 0.833 | 467 | 39 | 123 | 06_long_narrow_pipeline | kept |
| 5 | dbb4423 | 0.932 | 0.611 | 0.738 | 0.843 | 457 | 31 | 123 | none | kept |
| 6 | f0040cd | 0.928 | 0.617 | 0.741 | 0.843 | 475 | 34 | 121 | none | kept |
| 7 | 44153d4 | 0.926 | 0.649 | 0.763 | 0.853 | 488 | 36 | 111 | none | kept |
| 8 | 40a3071 | 0.928 | 0.649 | 0.764 | 0.854 | 486 | 35 | 111 | none | kept |
| 9 | 66980d0 | 0.944 | 0.639 | 0.762 | 0.862 | 478 | 27 | 114 | none | kept |
| 10 | 73258d4 | 0.944 | 0.639 | 0.762 | 0.862 | 478 | 27 | 114 | none | kept |
| 11 | 57c35f3 | 0.944 | 0.646 | 0.767 | 0.864 | 480 | 27 | 112 | none | kept |
| 12 | ba6b817 | 0.941 | 0.652 | 0.770 | 0.864 | 488 | 29 | 110 | none | kept |
| 13 | 87c5a3f | 0.940 | 0.687 | 0.794 | 0.876 | 521 | 31 | 99 | none | kept |
| 14 | 28919d7 | 0.881 | 0.712 | 0.788 | 0.841 | 563 | 67 | 91 | none | reverted |
| 15 | ca67dc4 | 0.948 | 0.687 | 0.796 | 0.881 | 517 | 27 | 99 | none | kept |
| 16 | e8b4e0d | 0.948 | 0.699 | 0.805 | 0.885 | 521 | 27 | 95 | none | kept |
| 17 | 40f52b6 | 0.948 | 0.690 | 0.799 | 0.882 | 519 | 27 | 98 | none | reverted |


## Final sentence-template TP/FP

| Sentence template | TP | FP |
|---|---|---|
| Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline.. | 12 | 6 |
| Both inputs are hash-partitioned and sorted on customer_id, and these shuffles are required by the join. | 6 | 2 |
| Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors.. | 26 | 2 |
| Required Shuffle (Join): Spark inserts this shuffle to co-locate join keys on the same partition, which is required by the selected join strategy.. | 7 | 2 |
| Static Shuffle Partitions: The shuffle keeps a static 200 partitions.. | 4 | 2 |
| This can concentrate work into one task and limit parallelism. | 2 | 2 |
| This reduces the volume of data shuffled and is the expected, efficient strategy for this aggregation. | 15 | 2 |
| Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator.. | 6 | 1 |
| Multiple Sort Operations: Multiple sort operations are present in the execution plan.. | 8 | 1 |
| Partial and final aggregation run around the hash-partitioned exchange on customer_id. | 3 | 1 |
| Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions.. | 16 | 1 |
| Sort Operation Detected: Spark sorts the dataset before downstream processing.. | 17 | 1 |
| The hash-partitioned exchange on customer_id is required by the aggregation. | 4 | 1 |
| This exchange is not an optimization target. | 8 | 1 |
| This exchange is required by the two-phase aggregation strategy and is not an optimization target. | 16 | 1 |
| Two-Phase Aggregation: Spark performs a partial (map-side) aggregation followed by a final aggregation across the shuffle boundary.. | 16 | 1 |
| A full outer join cannot be broadcast. | 1 | 0 |
| AQE Disabled: Adaptive Query Execution is turned off for this plan.. | 7 | 0 |
| AQE Enabled: Adaptive Query Execution is enabled, allowing Spark to adjust shuffle partitions, join strategies, and skew handling at runtime based on observed data statistics.. | 34 | 0 |
| Aggregation: Spark performs an aggregation operation.. | 19 | 0 |
| Cartesian Product Detected: A cartesian product should be avoided unless the cross join is truly intended.. | 1 | 0 |
| Complex Transformation Pipeline: 11 narrow operators are fused into one long pipeline with no shuffle.. | 1 | 0 |
| Each partition keeps only its top 10 rows, which avoids a full global sort and range shuffle. | 1 | 0 |
| Early Filter / Filter Pushdown: The filter is applied immediately after the scan or source, before any shuffle or join.. | 2 | 0 |
| Estimated Stage Count: The plan runs as 1 stage.. | 15 | 0 |
| Estimated Stage Count: The plan runs as 2 stages.. | 20 | 0 |
| Estimated Stage Count: The plan runs as 3 stages.. | 10 | 0 |
| Estimated Stage Count: The plan runs as 4 stages.. | 4 | 0 |
| Estimated Stage Count: The plan runs as 5 stages.. | 1 | 0 |
| Exchange Operator: Spark exchanges data between execution stages.. | 34 | 0 |
| Final Aggregation: Spark performs the final aggregation after combining intermediate results.. | 1 | 0 |
| Limit Detected: Results are capped by a CollectLimit of 20 rows.. | 1 | 0 |
| Merge Aggregation: Spark merges intermediate aggregation results received from upstream partitions.. | 1 | 0 |
| Multiple Shuffle Operations: Multiple shuffle exchanges are present in the execution plan.. | 15 | 0 |
| Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle.. | 4 | 0 |
| Only the first rows are fetched to the driver. | 1 | 0 |
| Partial Aggregation: Spark performs a local aggregation before redistributing data.. | 1 | 0 |
| Partial and final aggregation run around the hash-partitioned exchange on country_id. | 3 | 0 |
| Partial and final aggregation run around the hash-partitioned exchange on customer_id and product_id. | 1 | 0 |
| Partial and final aggregation run around the hash-partitioned exchange on product_id. | 4 | 0 |
| Partial and final aggregation run around the hash-partitioned exchange on region. | 1 | 0 |
| Partial and final aggregation run around the hash-partitioned exchange on status, product_id and spark_grouping_id. | 2 | 0 |
| Partial and final aggregation run around the hash-partitioned exchange on tag. | 1 | 0 |
| Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering.. | 10 | 0 |
| Shuffle Detected: A shuffle exchange redistributes data across partitions.. | 35 | 0 |
| Shuffle Read: Spark reads data produced by a previous shuffle stage.. | 1 | 0 |
| Shuffle Write: Spark writes shuffle data for downstream stages.. | 1 | 0 |
| Single Partition Bottleneck: A single-partition exchange was detected.. | 4 | 0 |
| Single Partition Detected: Spark repartitions all data into a single partition.. | 4 | 0 |
| Sort Merge Join Detected: Spark selected a Sort Merge Join.. | 9 | 0 |
| Sort Operation Detected: The sort is local to each partition and the plan contains no shuffle.. | 1 | 0 |
| Sort order: Ascending.. | 5 | 0 |
| Sort order: Descending.. | 4 | 0 |
| Stage Boundary Detected: This Exchange represents a shuffle boundary between Spark execution stages.. | 35 | 0 |
| The hash-partitioned exchange on country_id is required by the aggregation. | 3 | 0 |
| The hash-partitioned exchange on customer_id and product_id is required by the aggregation. | 1 | 0 |
| The hash-partitioned exchange on product_id is required by the aggregation. | 4 | 0 |
| The hash-partitioned exchange on region is required by the aggregation. | 1 | 0 |
| The hash-partitioned exchange on status, product_id and spark_grouping_id is required by the aggregation. | 2 | 0 |
| The hash-partitioned exchange on tag is required by the aggregation. | 1 | 0 |
| This may limit parallelism. | 4 | 0 |
| This strategy is typically efficient when one side of the join is sufficiently small to broadcast. | 7 | 0 |
| This strategy usually requires both inputs to be shuffled and sorted before the join. | 9 | 0 |
| Top-N Detected: ORDER BY with LIMIT 10 is planned as a TakeOrderedAndProject top-N.. | 1 | 0 |
