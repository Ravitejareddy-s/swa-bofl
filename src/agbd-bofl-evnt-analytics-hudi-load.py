import pyspark
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from awsglue.job import Job
from awsglue.context import GlueContext

spark = SparkSession.builder.config(
    "spark.serializer", "org.apache.spark.serializer.KryoSerializer"
).getOrCreate()

sc = spark.sparkContext
glueContext = GlueContext(sc)
job = Job(glueContext)


df = glueContext.create_dynamic_frame.from_catalog(
    database="datalake_dev1_agbd",
    table_name="curatedsecure_bag_on_flight_leg_state_v1_prqt",
    additional_options={"useCatalogSchema": "true", "useSparkDataSource": "true"},
)

df = df.toDF()
df.show()
