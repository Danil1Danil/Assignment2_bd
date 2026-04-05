import math
import re
import sys

from cassandra.cluster import Cluster
from pyspark.sql import SparkSession

K1 = 1.5
B = 0.75

spark = SparkSession.builder.appName("bm25_search").getOrCreate()
sc = spark.sparkContext
sc.setLogLevel("ERROR")

raw_query = " ".join(sys.argv[1:])
query_terms = list(set(re.findall(r"[a-z0-9]+", raw_query.lower())))

cluster = Cluster(["cassandra-server"], port=9042)
session = cluster.connect("search_engine")
session.default_timeout = 60

# Read corpus stats
stats = {
    row.stat_name: float(row.stat_value)
    for row in session.execute("SELECT * FROM corpus_stats")
}
N = stats["doc_count"]
avg_dl = stats["avg_doc_len"]

# Collect postings for all query terms
postings_data = []
seen_docs = set()

for term in query_terms:
    vocab_row = session.execute(
        "SELECT doc_freq FROM vocabulary WHERE term=%s", (term,)
    ).one()
    if vocab_row is None:
        continue

    df = vocab_row.doc_freq
    idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

    for entry in session.execute(
        "SELECT doc_id, term_freq FROM index_entries WHERE term=%s", (term,)
    ):
        postings_data.append((entry.doc_id, entry.term_freq, idf))
        seen_docs.add(entry.doc_id)

# Fetch doc metadata
doc_meta = {}
for doc_id in seen_docs:
    row = session.execute(
        "SELECT title, doc_len FROM documents WHERE doc_id=%s", (doc_id,)
    ).one()
    if row:
        doc_meta[doc_id] = (row.title, row.doc_len)

cluster.shutdown()

# Compute BM25 scores using Spark RDD
def bm25_score(record):
    doc_id, tf, idf = record
    dl = doc_meta[doc_id][1]
    numerator = tf * (K1 + 1)
    denominator = tf + K1 * (1 - B + B * dl / avg_dl)
    return (doc_id, idf * numerator / denominator)

results = (
    sc.parallelize(postings_data)
    .map(bm25_score)
    .reduceByKey(lambda a, b: a + b)
    .takeOrdered(10, key=lambda x: -x[1])
)

print("\n=== Top 10 Results ===")
for rank, (doc_id, score) in enumerate(results, 1):
    title = doc_meta[doc_id][0] if doc_id in doc_meta else "Unknown"
    print(f"{rank}. [{doc_id}] {title}  (score: {score:.4f})")

spark.stop()