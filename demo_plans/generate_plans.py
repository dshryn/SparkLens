from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, count, avg, desc
from contextlib import redirect_stdout

spark = (
    SparkSession.builder
    .appName("SparkLens Demo Plan Generator")
    .master("local[*]")
    .getOrCreate()
)

orders = (
    spark.range(1_000_000)
    .select(
        col("id").alias("order_id"),
        (col("id") % 10_000).alias("customer_id"),
        (col("id") % 100).alias("product_id"),
        ((col("id") % 5000) + 100).cast("double").alias("amount")
    )
)

customers = (
    spark.range(10_000)
    .select(
        col("id").alias("customer_id"),
        (col("id") % 10).alias("country_id")
    )
)

plans = {
    "01_simple_scan": orders.select(
        "order_id",
        "customer_id",
        "amount"
    ),

    "02_filter_aggregate": (
        orders
        .filter(col("amount") > 1000)
        .groupBy("product_id")
        .agg(sum("amount").alias("total_amount"))
    ),

    "03_join": (
        orders
        .join(customers, "customer_id")
        .select(
            orders.order_id,
            orders.amount,
            customers.country_id
        )
    ),

    "04_shuffle": (
        orders
        .groupBy("customer_id")
        .agg(
            count("*").alias("order_count"),
            avg("amount").alias("avg_amount")
        )
    ),

    "05_sort": (
        orders
        .orderBy(desc("amount"))
        .select(
            "order_id",
            "customer_id",
            "amount"
        )
    ),

    "06_complex_pipeline": (
        orders
        .filter(col("amount") > 1000)
        .join(customers, "customer_id")
        .groupBy("country_id")
        .agg(
            sum("amount").alias("total_amount"),
            count("*").alias("order_count")
        )
        .orderBy(desc("total_amount"))
    )
}

for name, df in plans.items():
    print(f"Generating {name}.txt")

    with open(f"{name}.txt", "w", encoding="utf-8") as f:
        with redirect_stdout(f):
            df.explain("formatted")

spark.stop()

print("All 6 formatted Spark plans generated.")