import os
import sys

from pathvalidate import sanitize_filename
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("prepare_documents").getOrCreate()

def build_docs_from_parquet(parquet_path):
    os.makedirs("data", exist_ok=True)
    limit = int(os.environ.get("DATA_DOC_LIMIT", "100"))
    rows = (
        spark.read.parquet(parquet_path)
        .select("id", "title", "text")
        .limit(limit)
        .collect()
    )
    for row in rows:
        safe_name = sanitize_filename(
            f"{row['id']}_{row['title']}"
        ).replace(" ", "_")
        out_path = f"data/{safe_name}.txt"
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(row["text"])


def build_input_from_docs(src_hdfs, dst_hdfs):
    def parse_doc(item):
        path, content = item
        filename = os.path.basename(path).rsplit(".", 1)[0]
        doc_id, title = filename.split("_", 1)
        clean_text = " ".join(content.split())
        return "\t".join([doc_id, title.replace("_", " "), clean_text])

    rdd = (
        spark.sparkContext
        .wholeTextFiles(src_hdfs.rstrip("/") + "/*")
        .sortBy(lambda x: x[0])
        .map(parse_doc)
        .coalesce(1)
    )
    rdd.saveAsTextFile(dst_hdfs)


if len(sys.argv) == 2:
    build_docs_from_parquet(sys.argv[1])
elif len(sys.argv) == 3:
    build_input_from_docs(sys.argv[1], sys.argv[2])
else:
    print("Usage: prepare_data.py <parquet_path> OR prepare_data.py <src_hdfs> <dst_hdfs>")
    sys.exit(1)

spark.stop()