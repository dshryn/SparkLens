# Rule Engine Results

## Final metrics

The final engine is commit `40a3071`.

| Metric | Final | Required baseline | Delta |
|---|---:|---:|---:|
| Precision | 0.928 | 0.651 | +0.277 |
| Recall | 0.649 | 0.611 | +0.038 |
| F1 | 0.764 | 0.630 | +0.134 |
| F0.5 | 0.854 | 0.643 | +0.211 |

The final run produced 486 claims, with 35 false positives and 111 false
negatives. The complete per-change log is in [EVAL_LOG.md](./EVAL_LOG.md).

## Final predicted-claim template counts

Templates are grouped by title prefix and first sentence, and sorted by false
positives descending. TP and FP counts are based on the final
`eval_review.csv`.

| Sentence template | TP | FP |
|---|---:|---:|
| Early Filter / Filter Pushdown: The filter is applied immediately after the scan or source, before any shuffle or join. | 2 | 8 |
| Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. | 12 | 6 |
| Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | 4 | 4 |
| Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | 26 | 2 |
| Required Shuffle (Join): Spark inserts this shuffle to co-locate join keys on the same partition, which is required by the selected join strategy. | 7 | 2 |
| Static Shuffle Partitions: The shuffle keeps a static 200 partitions. | 4 | 2 |
| This can concentrate work into one task and limit parallelism. | 2 | 2 |
| This reduces the volume of data shuffled and is the expected, efficient strategy for this aggregation. | 15 | 2 |
| Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 6 | 1 |
| Multiple Sort Operations: Multiple sort operations are present in the execution plan. | 8 | 1 |
| Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 16 | 1 |
| Sort Operation Detected: Spark sorts the dataset before downstream processing. | 17 | 1 |
| This exchange is not an optimization target. | 8 | 1 |
| This exchange is required by the two-phase aggregation strategy and is not an optimization target. | 16 | 1 |
| Two-Phase Aggregation: Spark performs a partial (map-side) aggregation followed by a final aggregation across the shuffle boundary. | 16 | 1 |

## Top 15 missed categories

Categories use the expected claim's title-like prefix and first sentence, with
one representative example.

| Expected type/pattern | Count | Plan | Example |
|---|---:|---|---|
| broadcast hash join build side | 1 | 18_broadcast_hint_aqe_off | A broadcast hint makes Spark use a broadcast hash join with the 100-row products table as the build side. |
| cartesian join warning | 1 | 26_cartesian_product | A cartesian product should be avoided unless the cross join is truly intended. |
| full outer join broadcast limitation | 1 | 24_full_outer_join | A full outer join cannot be broadcast |
| second range-partition exchange | 1 | 12_having_then_order | A second exchange range-partitions the filtered rows for the global ORDER BY on n in descending order. |
| final ORDER BY range partition | 1 | 40_sort_merge_join_then_orderby | A third shuffle range-partitions the joined rows for the final ORDER BY amount descending. |
| window partition key restores parallelism | 1 | 42_window_without_partition | Adding a partition key to the window would restore parallelism. |
| reused grouping partitioning | 1 | 16_repartition_then_groupby_same_key | Because the data is already distributed on the grouping key, the aggregation reuses that partitioning and no additional exchange is added. |
| aggregation phases after shuffle | 1 | 16_repartition_then_groupby_same_key | Both aggregation phases run after the shuffle |
| Parquet predicate pushdown | 1 | 49_parquet_scan_filter_join | Both inputs are Parquet file scans, and the dwell_ms predicate is pushed down into the clicks scan. |
| required hash-partitioned sort-merge inputs | 1 | 23_left_anti_sort_merge | Both inputs are hash-partitioned and sorted on customer_id, and these shuffles are required by the join. |
| required join shuffles after ordering | 1 | 40_sort_merge_join_then_orderby | Both join inputs are hash-partitioned on customer_id and sorted, and these shuffles are required by the join. |
| shuffled hash join without sort | 1 | 21_shuffled_hash_join_hint | Both sides are hash-partitioned on customer_id and joined without a sort step. |
| reused filtered subquery | 1 | 30_self_join_reused_exchange | Both sides come from the same filtered orders subquery |
| broadcast disabled | 1 | 19_sort_merge_join_small_side | Broadcasting is switched off |
| broadcast removes shuffles | 1 | 44_etl_shuffle_heavy_aqe_off | Broadcasting the small customers side would remove 2 of the shuffles. |

## Top 15 false-positive categories

Categories use the predicted claim's title-like prefix and first sentence, with
one representative example.

| Produced type/pattern | Count | Plan | Example |
|---|---:|---|---|
| filter pushdown | 8 | 02_filter_projection | Early Filter / Filter Pushdown: The filter is applied immediately after the scan or source, before any shuffle or join. |
| multi-stage aggregation | 6 | 09_distinct | Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. |
| narrow pipeline | 4 | 05_sort_within_partitions | Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. |
| hash partitioning | 2 | 30_self_join_reused_exchange | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. |
| required join shuffle | 2 | 28_join_then_agg_same_key | Required Shuffle (Join): Spark inserts this shuffle to co-locate join keys on the same partition, which is required by the selected join strategy. |
| static shuffle partitions | 2 | 30_self_join_reused_exchange | Static Shuffle Partitions: The shuffle keeps a static 200 partitions. |
| single-partition bottleneck explanation | 2 | 11_global_sum | This can concentrate work into one task and limit parallelism. |
| efficient aggregation explanation | 2 | 10_count_distinct | This reduces the volume of data shuffled and is the expected, efficient strategy for this aggregation. |
| broadcast hash join | 1 | 27_three_way_broadcast | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. |
| multiple sorts | 1 | 29_join_then_agg_other_key_aqe_off | Multiple Sort Operations: Multiple sort operations are present in the execution plan. |
| required aggregation shuffle | 1 | 10_count_distinct | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. |
| sort operation | 1 | 29_join_then_agg_other_key_aqe_off | Sort Operation Detected: Spark sorts the dataset before downstream processing. |
| required exchange explanation | 1 | 28_join_then_agg_same_key | This exchange is not an optimization target. |
| two-phase exchange explanation | 1 | 10_count_distinct | This exchange is required by the two-phase aggregation strategy and is not an optimization target. |
| two-phase aggregation explanation | 1 | 10_count_distinct | Two-Phase Aggregation: Spark performs a partial (map-side) aggregation followed by a final aggregation across the shuffle boundary. |

## Regressions versus `c7daf3c`

I created a detached temporary worktree at `c7daf3c` and ran its CLI
evaluation over all 50 plans with `--eval`, then compared its predicted
claims with the final snapshot. No plan regressed versus that baseline, so
there are no lost or added claims to list.

| Plan id | Claims lost | Claims added |
|---|---|---|
| none | none | none |
