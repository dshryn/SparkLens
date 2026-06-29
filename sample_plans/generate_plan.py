from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("SparkLens Test").master("local[*]").getOrCreate()

df = spark.range(1000).withColumnRenamed("id", "id")
df2 = spark.range(1000).withColumnRenamed("id", "id")

result = df.join(df2, "id").groupBy("id").count().orderBy("count")

result.explain(mode="formatted")
