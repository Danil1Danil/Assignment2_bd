import sys

for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    parts = line.split("\t", 2)
    if len(parts) < 3:
        continue
    # line is from /indexer/index: term \t doc_id \t tf
    # emit term once per doc to count df
    # emit doc_len for stats
    term, doc_id, tf = parts
    print(f"VOCAB\t{term}\t1")
    print(f"STATS\t{doc_id}\t{tf}")