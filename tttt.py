from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

df = (
    spark.range(1000000)
    .withColumn("customer_id", F.col("id") % 1000)
    .withColumn("amount", (F.col("id") % 500) + 100)
    .filter(F.col("amount") > 250)
    .groupBy("customer_id")
    .agg(F.sum("amount").alias("total_amount"))
)

df.explain(mode="formatted")