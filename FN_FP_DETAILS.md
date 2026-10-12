# FN and FP Details

Generated from the final `evaluation/eval_review.csv` for commit `57c35f3`.

## FN counts by reason

| Reason | Count |
|---|---:|
| advice vs observation | 1 |
| below threshold | 82 |
| different alternative | 16 |
| different subject | 1 |
| number not backed | 12 |

## All false negatives

| Plan id | Expected claim | Best match | Similarity | Reason |
|---|---|---|---:|---|
| 26_cartesian_product | crossJoin with broadcasting disabled produces a CartesianProduct between orders and customer segments. | Cartesian Product Detected: A cartesian product should be avoided unless the cross join is truly intended. | 0.490 | advice vs observation |
| 01_range_projection | The plan is a simple projection over a generated range of order ids. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 02_filter_projection | A filter on amount is applied directly on top of the range source, before any other work. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 03_limit | Results are capped by a CollectLimit of 20 rows | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 03_limit | only the first rows are fetched to the driver. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 04_union_two_sources | Two range sources are combined with a Union, which concatenates their partitions without moving data. | Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | 0.211 | below threshold |
| 05_sort_within_partitions | Rows are sorted by amount in ascending order within each partition only. | Sort Operation Detected: The sort is local to each partition and the plan contains no shuffle. | 0.429 | below threshold |
| 06_long_narrow_pipeline | The explode (Generate) turns each input row into 2 rows before the later filters. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 08_groupby_multi_agg_aqe_off | the shuffle keeps a fixed 200 partitions that cannot be coalesced at runtime. | Static Shuffle Partitions: The shuffle keeps a static 200 partitions. | 0.323 | below threshold |
| 09_distinct | distinct() is executed as a hash aggregate on product_id with no aggregate functions, first locally per partition and then globally. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.193 | below threshold |
| 09_distinct | The shuffle hash-partitions by product_id and is structurally required to remove duplicates across partitions. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.426 | below threshold |
| 10_count_distinct | countDistinct is planned as 2 rounds of aggregation: first deduplicating customer and product pairs, then counting them per customer. | Aggregation: Spark performs an aggregation operation. | 0.210 | below threshold |
| 10_count_distinct | This needs 2 shuffles, one hash-partitioned on customer_id and product_id and one on customer_id alone. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.255 | below threshold |
| 10_count_distinct | The extra exchange makes a distinct count more expensive than a plain count. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.188 | below threshold |
| 11_global_sum | The total is a global aggregation with no grouping keys, computed as partial sums per partition followed by a final sum. | Two-Phase Aggregation: Spark performs a partial (map-side) aggregation followed by a final aggregation across the shuffle boundary. | 0.434 | below threshold |
| 11_global_sum | Partial results are gathered into a single partition through a SinglePartition exchange. | Single Partition Detected: Spark repartitions all data into a single partition. | 0.441 | below threshold |
| 12_having_then_order | A second exchange range-partitions the filtered rows for the global ORDER BY on n in descending order. | Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering. | 0.428 | below threshold |
| 13_collect_list | Collecting whole lists per key keeps every product_id in memory and can be memory-heavy for customers with many orders. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.000 | below threshold |
| 14_rollup | The rollup is implemented with an Expand operator that emits each row once per grouping set, 3 copies here, before aggregation. | Aggregation: Spark performs an aggregation operation. | 0.163 | below threshold |
| 15_cube_aqe_off | cube() expands every row into 4 grouping-set copies through Expand before counting. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.000 | below threshold |
| 16_repartition_then_groupby_same_key | Because the data is already distributed on the grouping key, the aggregation reuses that partitioning and no additional exchange is added. | Aggregation: Spark performs an aggregation operation. | 0.282 | below threshold |
| 16_repartition_then_groupby_same_key | Both aggregation phases run after the shuffle | Aggregation: Spark performs an aggregation operation. | 0.448 | below threshold |
| 16_repartition_then_groupby_same_key | no map-side partial aggregation reduces the volume that is shuffled. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.188 | below threshold |
| 17_broadcast_join_auto | The main job runs as 1 stage, with the broadcast built separately. | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 0.443 | below threshold |
| 19_sort_merge_join_small_side | Broadcasting is switched off | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 19_sort_merge_join_small_side | The customers side has only 10,000 rows | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 19_sort_merge_join_small_side | a broadcast hash join would avoid both shuffles and sorts. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.260 | below threshold |
| 20_sort_merge_join_two_large | orders and events are both large | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 20_sort_merge_join_two_large | neither input is small enough to broadcast. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.128 | below threshold |
| 21_shuffled_hash_join_hint | The shuffle_hash hint selects a shuffled hash join, with the customers side used to build the in-memory hash table. | AQE Enabled: Adaptive Query Execution is enabled, allowing Spark to adjust shuffle partitions, join strategies, and skew handling at runtime based on observed data statistics. | 0.176 | below threshold |
| 21_shuffled_hash_join_hint | Both sides are hash-partitioned on customer_id and joined without a sort step. | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | 0.290 | below threshold |
| 21_shuffled_hash_join_hint | The exchanges are required so that equal keys land in the same partition. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.311 | below threshold |
| 22_left_semi_broadcast | The left semi join keeps orders whose customer_id exists in the filtered customers set. | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 0.186 | below threshold |
| 22_left_semi_broadcast | No shuffle of the orders table is needed. | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 0.361 | below threshold |
| 23_left_anti_sort_merge | The left anti join returns orders without a matching customer in the filtered segment. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.153 | below threshold |
| 23_left_anti_sort_merge | The filtered customers side is small | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 23_left_anti_sort_merge | broadcasting it would remove the shuffle of the large orders side. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 25_non_equi_join | Spark falls back to a broadcast nested loop join. | AQE Enabled: Adaptive Query Execution is enabled, allowing Spark to adjust shuffle partitions, join strategies, and skew handling at runtime based on observed data statistics. | 0.260 | below threshold |
| 25_non_equi_join | Every order row is compared against every broadcast products row, which is costly and scales with the product of both input sizes. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 25_non_equi_join | The small products side is broadcast | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 25_non_equi_join | no shuffle is needed. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 26_cartesian_product | Every pair of rows is emitted | Cartesian Product Detected: A cartesian product should be avoided unless the cross join is truly intended. | 0.000 | below threshold |
| 26_cartesian_product | the output size is the product of both inputs and very expensive. | Cartesian Product Detected: A cartesian product should be avoided unless the cross join is truly intended. | 0.000 | below threshold |
| 28_join_then_agg_same_key | With broadcasting disabled, orders and customers are joined with a sort-merge join on customer_id. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.414 | below threshold |
| 28_join_then_agg_same_key | The aggregation by customer_id reuses the join's partitioning | Required Shuffle (Join): Spark inserts this shuffle to co-locate join keys on the same partition, which is required by the selected join strategy. | 0.289 | below threshold |
| 28_join_then_agg_same_key | no extra exchange is added for it. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 29_join_then_agg_other_key_aqe_off | Grouping by country_id needs a new hash partitioning, adding a third exchange after the join. | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | 0.400 | below threshold |
| 29_join_then_agg_other_key_aqe_off | Broadcasting the small customers table would remove the 2 join shuffles. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 30_self_join_reused_exchange | Both sides come from the same filtered orders subquery | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 30_self_join_reused_exchange | Spark reuses the first shuffle through a ReusedExchange instead of shuffling the data twice. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.171 | below threshold |
| 33_repartition_round_robin | repartition(64) triggers a round-robin shuffle that spreads rows evenly across 64 partitions. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.347 | below threshold |
| 33_repartition_round_robin | No operator in this plan needs that distribution | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.000 | below threshold |
| 33_repartition_round_robin | the shuffle is avoidable unless later work needs rebalanced partitions. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.242 | below threshold |
| 34_repartition_by_column | it is unnecessary here. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.289 | below threshold |
| 35_repartition_by_range | not sorted within partitions. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.250 | below threshold |
| 37_coalesce_to_one | The status filter is applied directly on the range source. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 37_coalesce_to_one | coalesce(1) merges all partitions into a single partition without a shuffle. | Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | 0.195 | below threshold |
| 37_coalesce_to_one | This limits parallelism to one task even though no exchange appears in the plan. | Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | 0.139 | below threshold |
| 38_top_n | ORDER BY amount DESC with LIMIT 10 is planned as a TakeOrderedAndProject top-N. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 38_top_n | Each partition keeps only its top 10 rows, which avoids a full global sort and range shuffle. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 38_top_n | The results come back ordered by amount descending. | Estimated Stage Count: The plan runs as 1 stage. | 0.000 | below threshold |
| 39_sort_then_groupby | the earlier sort is redundant. | Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering. | 0.299 | below threshold |
| 39_sort_then_groupby | Removing the orderBy would eliminate one shuffle and one full sort. | Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering. | 0.316 | below threshold |
| 40_sort_merge_join_then_orderby | broadcasting is disabled. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 40_sort_merge_join_then_orderby | A third shuffle range-partitions the joined rows for the final ORDER BY amount descending. | Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering. | 0.446 | below threshold |
| 40_sort_merge_join_then_orderby | The small customers table could be broadcast to remove the 2 join shuffles. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 41_window_partitioned_rank | row_number over a window partitioned by customer_id requires hash-partitioning the rows by customer_id. | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | 0.392 | below threshold |
| 41_window_partitioned_rank | Within each partition, rows are sorted by customer_id and amount descending before the Window operator ranks them. | Sort Operation Detected: Spark sorts the dataset before downstream processing. | 0.194 | below threshold |
| 41_window_partitioned_rank | The shuffle is required so each customer's orders sit in one partition. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.325 | below threshold |
| 42_window_without_partition | The window has no PARTITION BY clause | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.000 | below threshold |
| 42_window_without_partition | Adding a partition key to the window would restore parallelism. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.042 | below threshold |
| 42_window_without_partition | cannot split a SinglePartition exchange. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.188 | below threshold |
| 43_etl_filter_join_agg_sort | The amount filter is applied right after the orders range, before the join. | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 0.333 | below threshold |
| 44_etl_shuffle_heavy_aqe_off | The amount filter runs directly on the orders source before the join. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.333 | below threshold |
| 44_etl_shuffle_heavy_aqe_off | Broadcasting the small customers side would remove 2 of the shuffles. | Sort Merge Join Detected: Spark selected a Sort Merge Join. | 0.000 | below threshold |
| 44_etl_shuffle_heavy_aqe_off | none of the shuffles can be coalesced or switched to a broadcast join at runtime. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.178 | below threshold |
| 45_multi_shuffle_chain | the first repartition is redundant. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.289 | below threshold |
| 46_union_then_agg | Two filtered scans of orders are combined with a Union before aggregation. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.254 | below threshold |
| 46_union_then_agg | Using one filter with both status values would avoid scanning the orders source twice. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.000 | below threshold |
| 47_explode_then_agg | explode turns every order into 3 rows through a Generate operator. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.000 | below threshold |
| 50_photon_broadcast_join_agg_sort | This is a Databricks Photon plan in which every operator runs natively in Photon. | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 0.000 | below threshold |
| 50_photon_broadcast_join_agg_sort | it is not a bottleneck. | Single Partition Detected: Spark repartitions all data into a single partition. | 0.414 | below threshold |
| 50_photon_broadcast_join_agg_sort | The shuffle between the merge and final aggregation hash-partitions by value into 16 partitions and is required by the aggregation. | Merge Aggregation: Spark merges intermediate aggregation results received from upstream partitions. | 0.448 | below threshold |
| 06_long_narrow_pipeline | The plan is a long pipeline of 11 narrow operators, mixing filters, projections, an explode and a sample. | Complex Transformation Pipeline: 11 narrow operators are fused into one long pipeline with no shuffle. | 0.542 | different alternative |
| 08_groupby_multi_agg_aqe_off | The exchange hash-partitions rows on customer_id and is needed for the final aggregation. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.601 | different alternative |
| 12_having_then_order | The first exchange hash-partitions on customer_id and is required by the aggregation. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.559 | different alternative |
| 14_rollup | Expand inflates the data volume that goes into the partial aggregate and the shuffle. | This reduces the volume of data shuffled and is the expected, efficient strategy for this aggregation. | 0.552 | different alternative |
| 14_rollup | The exchange hash-partitions on status, product_id and the grouping id, and is required for the final sum. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.559 | different alternative |
| 15_cube_aqe_off | The hash-partitioned exchange on the grouping columns is required by the aggregation. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.585 | different alternative |
| 23_left_anti_sort_merge | Both inputs are hash-partitioned and sorted on customer_id, and these shuffles are required by the join. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.544 | different alternative |
| 39_sort_then_groupby | Revenue per product is computed with partial and final aggregation around the hash-partitioned exchange. | This exchange is required by the two-phase aggregation strategy and is not an optimization target. | 0.631 | different alternative |
| 40_sort_merge_join_then_orderby | Both join inputs are hash-partitioned on customer_id and sorted, and these shuffles are required by the join. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.579 | different alternative |
| 43_etl_filter_join_agg_sort | Revenue per country_id is computed with partial and final hash aggregation around a hash-partitioned exchange. | This exchange is required by the two-phase aggregation strategy and is not an optimization target. | 0.641 | different alternative |
| 44_etl_shuffle_heavy_aqe_off | Grouping by country_id adds another hash-partitioned shuffle with partial and final aggregation. | This exchange is required by the two-phase aggregation strategy and is not an optimization target. | 0.641 | different alternative |
| 46_union_then_agg | The hash-partitioned exchange on product_id is required by the aggregation. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.559 | different alternative |
| 47_explode_then_agg | The partial aggregation after the explode shrinks the data to one row per tag and partition before shuffling. | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 0.528 | different alternative |
| 48_csv_scan_filter_agg | The CSV file is read with a file scan whose amount predicate is pushed down to the scan. | Early Filter / Filter Pushdown: The filter is applied immediately after the scan or source, before any shuffle or join. | 0.564 | different alternative |
| 48_csv_scan_filter_agg | Revenue per region is computed with partial and final aggregation around a hash-partitioned exchange that is required by the grouping. | This exchange is required by the two-phase aggregation strategy and is not an optimization target. | 0.656 | different alternative |
| 49_parquet_scan_filter_join | Both inputs are Parquet file scans, and the dwell_ms predicate is pushed down into the clicks scan. | Early Filter / Filter Pushdown: The filter is applied immediately after the scan or source, before any shuffle or join. | 0.564 | different alternative |
| 07_groupby_sum | Spark can coalesce the shuffle partitions at runtime. | AQE Enabled: Adaptive Query Execution is enabled, allowing Spark to adjust shuffle partitions, join strategies, and skew handling at runtime based on observed data statistics. | 0.467 | different subject |
| 07_groupby_sum | Rows are hash-partitioned by product_id into 200 shuffle partitions. | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | 0.750 | number not backed |
| 16_repartition_then_groupby_same_key | The explicit repartition(64, customer_id) hash-partitions the raw rows by customer_id. | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | 0.750 | number not backed |
| 18_broadcast_hint_aqe_off | A broadcast hint makes Spark use a broadcast hash join with the 100-row products table as the build side. | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 0.567 | number not backed |
| 19_sort_merge_join_small_side | These 2 shuffles are required by the sort-merge join strategy. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.584 | number not backed |
| 20_sort_merge_join_two_large | Each side is hash-partitioned into 200 partitions and sorted on the join key. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.532 | number not backed |
| 27_three_way_broadcast | The 2 broadcasts are built as separate jobs. | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 0.750 | number not backed |
| 34_repartition_by_column | repartition(customer_id) hash-partitions all rows by customer_id into 200 partitions. | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | 0.750 | number not backed |
| 35_repartition_by_range | repartitionByRange(16, amount) range-partitions rows into 16 partitions of contiguous amount values. | Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering. | 0.750 | number not backed |
| 36_repartition_to_one | repartition(1) shuffles every order into a single partition. | Single Partition Detected: Spark repartitions all data into a single partition. | 0.750 | number not backed |
| 40_sort_merge_join_then_orderby | The plan contains 3 sort operators, 2 for the merge join and 1 for the global ordering. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.750 | number not backed |
| 44_etl_shuffle_heavy_aqe_off | The plan contains 4 shuffle exchanges. | This strategy usually requires both inputs to be shuffled and sorted before the join. | 0.750 | number not backed |
| 45_multi_shuffle_chain | repartition(32, product_id) shuffles all rows by product_id first. | Shuffle Detected: A shuffle exchange redistributes data across partitions. | 0.750 | number not backed |

## All false positives

| Plan id | Predicted claim | Best match | Similarity | Reason |
|---|---|---|---:|---|
| 05_sort_within_partitions | Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | Because the sort is local to each partition, the plan contains no shuffle. | 0.222 | below threshold |
| 09_distinct | Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. | Partial deduplication before the exchange reduces how many rows are shuffled. | 0.302 | below threshold |
| 10_count_distinct | Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | This needs 2 shuffles, one hash-partitioned on customer_id and product_id and one on customer_id alone. | 0.382 | below threshold |
| 10_count_distinct | This exchange is required by the two-phase aggregation strategy and is not an optimization target. | This needs 2 shuffles, one hash-partitioned on customer_id and product_id and one on customer_id alone. | 0.287 | below threshold |
| 10_count_distinct | This reduces the volume of data shuffled and is the expected, efficient strategy for this aggregation. | This needs 2 shuffles, one hash-partitioned on customer_id and product_id and one on customer_id alone. | 0.218 | below threshold |
| 10_count_distinct | Two-Phase Aggregation: Spark performs a partial (map-side) aggregation followed by a final aggregation across the shuffle boundary. | This needs 2 shuffles, one hash-partitioned on customer_id and product_id and one on customer_id alone. | 0.251 | below threshold |
| 11_global_sum | Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. | Only one partial row per input partition reaches that exchange | 0.434 | below threshold |
| 11_global_sum | This can concentrate work into one task and limit parallelism. | Partial results are gathered into a single partition through a SinglePartition exchange. | 0.432 | below threshold |
| 12_having_then_order | Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. | Orders are counted per customer_id with a partial count before the shuffle and a final count after it. | 0.434 | below threshold |
| 14_rollup | Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. | Expand inflates the data volume that goes into the partial aggregate and the shuffle. | 0.306 | below threshold |
| 16_repartition_then_groupby_same_key | Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. | Both aggregation phases run after the shuffle | 0.282 | below threshold |
| 26_cartesian_product | Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | crossJoin with broadcasting disabled produces a CartesianProduct between orders and customer segments. | 0.000 | below threshold |
| 27_three_way_broadcast | Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | Both joins are broadcast hash joins: customers is broadcast for the first join and countries for the second. | 0.631 | different alternative |
| 28_join_then_agg_same_key | Required Shuffle (Join): Spark inserts this shuffle to co-locate join keys on the same partition, which is required by the selected join strategy. | The aggregation by customer_id reuses the join's partitioning | 0.339 | below threshold |
| 28_join_then_agg_same_key | This exchange is not an optimization target. | With broadcasting disabled, orders and customers are joined with a sort-merge join on customer_id. | 0.354 | below threshold |
| 29_join_then_agg_other_key_aqe_off | Multiple Sort Operations: Multiple sort operations are present in the execution plan. | Orders and customers are joined with a sort-merge join, shuffling both sides by customer_id. | 0.000 | below threshold |
| 29_join_then_agg_other_key_aqe_off | Sort Operation Detected: Spark sorts the dataset before downstream processing. | Orders and customers are joined with a sort-merge join, shuffling both sides by customer_id. | 0.000 | below threshold |
| 30_self_join_reused_exchange | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | Spark reuses the first shuffle through a ReusedExchange instead of shuffling the data twice. | 0.318 | below threshold |
| 30_self_join_reused_exchange | Required Shuffle (Join): Spark inserts this shuffle to co-locate join keys on the same partition, which is required by the selected join strategy. | The self-join on customer_id is executed as a sort-merge join. | 0.388 | below threshold |
| 30_self_join_reused_exchange | Static Shuffle Partitions: The shuffle keeps a static 200 partitions. | Spark reuses the first shuffle through a ReusedExchange instead of shuffling the data twice. | 0.750 | number not backed |
| 37_coalesce_to_one | Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | coalesce(1) merges all partitions into a single partition without a shuffle. | 0.187 | below threshold |
| 38_top_n | Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | ORDER BY amount DESC with LIMIT 10 is planned as a TakeOrderedAndProject top-N. | 0.000 | below threshold |
| 44_etl_shuffle_heavy_aqe_off | Static Shuffle Partitions: The shuffle keeps a static 200 partitions. | With broadcasting disabled, the join becomes a sort-merge join that shuffles and sorts both sides on customer_id. | 0.750 | number not backed |
| 45_multi_shuffle_chain | Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | repartition(32, product_id) shuffles all rows by product_id first. | 0.444 | below threshold |
| 47_explode_then_agg | Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. | The partial aggregation after the explode shrinks the data to one row per tag and partition before shuffling. | 0.311 | below threshold |
| 47_explode_then_agg | This reduces the volume of data shuffled and is the expected, efficient strategy for this aggregation. | The partial aggregation after the explode shrinks the data to one row per tag and partition before shuffling. | 0.370 | below threshold |
| 50_photon_broadcast_join_agg_sort | This can concentrate work into one task and limit parallelism. | Only the small broadcast side goes through the SinglePartition exchange | 0.418 | below threshold |

## 15 plans with lowest F1

| Plan id | Expected claims | Predicted claims | FP | FN | F1 |
|---|---:|---:|---:|---:|---:|
| 37_coalesce_to_one | 4 | 2 | 1 | 3 | 0.333 |
| 38_top_n | 4 | 2 | 1 | 3 | 0.333 |
| 10_count_distinct | 6 | 12 | 4 | 3 | 0.462 |
| 26_cartesian_product | 5 | 3 | 1 | 3 | 0.500 |
| 16_repartition_then_groupby_same_key | 7 | 8 | 1 | 4 | 0.545 |
| 14_rollup | 6 | 12 | 1 | 3 | 0.600 |
| 25_non_equi_join | 7 | 2 | 0 | 4 | 0.600 |
| 40_sort_merge_join_then_orderby | 9 | 15 | 0 | 5 | 0.615 |
| 44_etl_shuffle_heavy_aqe_off | 10 | 22 | 1 | 5 | 0.625 |
| 03_limit | 4 | 2 | 0 | 2 | 0.667 |
| 05_sort_within_partitions | 3 | 3 | 1 | 1 | 0.667 |
| 06_long_narrow_pipeline | 4 | 2 | 0 | 2 | 0.667 |
| 21_shuffled_hash_join_hint | 6 | 7 | 0 | 3 | 0.667 |
| 23_left_anti_sort_merge | 8 | 13 | 0 | 4 | 0.667 |
| 28_join_then_agg_same_key | 8 | 15 | 2 | 3 | 0.667 |

## Sentence-template TP/FP counts

| Sentence template | TP | FP |
|---|---:|---:|
| Multi-Stage Aggregation: Multiple aggregation operators are present, indicating a multi-stage aggregation pipeline. | 12 | 6 |
| Narrow Pipeline: All operators are narrow and are fused into a single pipeline with no shuffle. | 4 | 4 |
| Hash Partitioning Detected: Spark redistributes rows using hash partitioning across executors. | 26 | 2 |
| Required Shuffle (Join): Spark inserts this shuffle to co-locate join keys on the same partition, which is required by the selected join strategy. | 7 | 2 |
| Static Shuffle Partitions: The shuffle keeps a static 200 partitions. | 4 | 2 |
| This can concentrate work into one task and limit parallelism.: This can concentrate work into one task and limit parallelism. | 2 | 2 |
| This reduces the volume of data shuffled and is the expected, efficient strategy for this aggregation.: This reduces the volume of data shuffled and is the expected, efficient strategy for this aggregation. | 15 | 2 |
| Broadcast Hash Join Detected: Spark selected a Broadcast Hash Join for this operator. | 6 | 1 |
| Multiple Sort Operations: Multiple sort operations are present in the execution plan. | 8 | 1 |
| Required Shuffle (Aggregation): Spark inserts this shuffle to redistribute partially aggregated data so the final aggregation can combine results across partitions. | 16 | 1 |
| Sort Operation Detected: Spark sorts the dataset before downstream processing. | 17 | 1 |
| This exchange is not an optimization target.: This exchange is not an optimization target. | 8 | 1 |
| This exchange is required by the two-phase aggregation strategy and is not an optimization target.: This exchange is required by the two-phase aggregation strategy and is not an optimization target. | 16 | 1 |
| Two-Phase Aggregation: Spark performs a partial (map-side) aggregation followed by a final aggregation across the shuffle boundary. | 16 | 1 |
| A full outer join cannot be broadcast.: A full outer join cannot be broadcast. | 1 | 0 |
| AQE Disabled: Adaptive Query Execution is turned off for this plan. | 7 | 0 |
| AQE Enabled: Adaptive Query Execution is enabled, allowing Spark to adjust shuffle partitions, join strategies, and skew handling at runtime based on observed data statistics. | 34 | 0 |
| Aggregation: Spark performs an aggregation operation. | 19 | 0 |
| Cartesian Product Detected: A cartesian product should be avoided unless the cross join is truly intended. | 1 | 0 |
| Complex Transformation Pipeline: 11 narrow operators are fused into one long pipeline with no shuffle. | 1 | 0 |
| Early Filter / Filter Pushdown: The filter is applied immediately after the scan or source, before any shuffle or join. | 2 | 0 |
| Estimated Stage Count: The plan runs as 1 stage. | 15 | 0 |
| Estimated Stage Count: The plan runs as 2 stages. | 20 | 0 |
| Estimated Stage Count: The plan runs as 3 stages. | 10 | 0 |
| Estimated Stage Count: The plan runs as 4 stages. | 4 | 0 |
| Estimated Stage Count: The plan runs as 5 stages. | 1 | 0 |
| Exchange Operator: Spark exchanges data between execution stages. | 34 | 0 |
| Final Aggregation: Spark performs the final aggregation after combining intermediate results. | 1 | 0 |
| Merge Aggregation: Spark merges intermediate aggregation results received from upstream partitions. | 1 | 0 |
| Multiple Shuffle Operations: Multiple shuffle exchanges are present in the execution plan. | 15 | 0 |
| Partial Aggregation: Spark performs a local aggregation before redistributing data. | 1 | 0 |
| Range Partitioning Detected: Spark redistributes rows using range partitioning to preserve ordering. | 10 | 0 |
| Shuffle Detected: A shuffle exchange redistributes data across partitions. | 35 | 0 |
| Shuffle Read: Spark reads data produced by a previous shuffle stage. | 1 | 0 |
| Shuffle Write: Spark writes shuffle data for downstream stages. | 1 | 0 |
| Single Partition Bottleneck: A single-partition exchange was detected. | 4 | 0 |
| Single Partition Detected: Spark repartitions all data into a single partition. | 4 | 0 |
| Sort Merge Join Detected: Spark selected a Sort Merge Join. | 9 | 0 |
| Sort Operation Detected: The sort is local to each partition and the plan contains no shuffle. | 1 | 0 |
| Sort order: Ascending. | 5 | 0 |
| Sort order: Descending. | 4 | 0 |
| Stage Boundary Detected: This Exchange represents a shuffle boundary between Spark execution stages. | 35 | 0 |
| This may limit parallelism.: This may limit parallelism. | 4 | 0 |
| This strategy is typically efficient when one side of the join is sufficiently small to broadcast.: This strategy is typically efficient when one side of the join is sufficiently small to broadcast. | 7 | 0 |
| This strategy usually requires both inputs to be shuffled and sorted before the join.: This strategy usually requires both inputs to be shuffled and sorted before the join. | 9 | 0 |
