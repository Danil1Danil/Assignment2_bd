import subprocess
import sys

from cassandra.cluster import Cluster

base = sys.argv[1] if len(sys.argv) > 1 else "/indexer"

cluster = Cluster(["cassandra-server"], port=9042)
session = cluster.connect()
session.default_timeout = 60

# Setup keyspace and tables
session.execute("DROP KEYSPACE IF EXISTS search_engine")
session.execute("""
    CREATE KEYSPACE search_engine
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
""")
session.set_keyspace("search_engine")

session.execute("""
    CREATE TABLE documents (
        doc_id text PRIMARY KEY,
        title text,
        doc_len int
    )
""")
session.execute("""
    CREATE TABLE index_entries (
        term text,
        doc_id text,
        term_freq int,
        PRIMARY KEY (term, doc_id)
    )
""")
session.execute("""
    CREATE TABLE vocabulary (
        term text PRIMARY KEY,
        doc_freq int
    )
""")
session.execute("""
    CREATE TABLE corpus_stats (
        stat_name text PRIMARY KEY,
        stat_value text
    )
""")

ins_doc = session.prepare(
    "INSERT INTO documents (doc_id, title, doc_len) VALUES (?, ?, ?)"
)
ins_index = session.prepare(
    "INSERT INTO index_entries (term, doc_id, term_freq) VALUES (?, ?, ?)"
)
ins_vocab = session.prepare(
    "INSERT INTO vocabulary (term, doc_freq) VALUES (?, ?)"
)
ins_stat = session.prepare(
    "INSERT INTO corpus_stats (stat_name, stat_value) VALUES (?, ?)"
)


def read_hdfs(path):
    return subprocess.check_output(
        ["hdfs", "dfs", "-cat", path], text=True
    ).splitlines()


# Load documents
for line in read_hdfs(f"{base}/docs/part-*"):
    if not line.strip():
        continue
    doc_id, title, doc_len = line.split("\t")
    session.execute(ins_doc, (doc_id, title, int(doc_len)))

# Load index entries
for line in read_hdfs(f"{base}/index/part-*"):
    if not line.strip():
        continue
    term, doc_id, tf = line.split("\t")
    session.execute(ins_index, (term, doc_id, int(tf)))

# Load vocab and stats from combined output
for line in read_hdfs(f"{base}/vocab_and_stats/part-*"):
    if not line.strip():
        continue
    parts = line.split("\t")
    if parts[0] == "VOCAB":
        _, term, df = parts
        session.execute(ins_vocab, (term, int(df)))
    elif parts[0] == "STATS":
        _, name, value = parts
        session.execute(ins_stat, (name, value))

# Print counts for verification
for table in ["documents", "index_entries", "vocabulary", "corpus_stats"]:
    cnt = session.execute(f"SELECT COUNT(*) FROM {table}").one().count
    print(f"{table}: {cnt} rows")

cluster.shutdown()