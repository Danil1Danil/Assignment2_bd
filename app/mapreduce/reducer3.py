import sys
from collections import defaultdict

counts = defaultdict(int)
doc_lens = defaultdict(int)

for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    parts = line.split("\t", 2)
    if len(parts) < 3:
        continue
    record_type, key, value = parts
    if record_type == "VOCAB":
        counts[key] += 1
    elif record_type == "STATS":
        doc_lens[key] += int(value)

for term, df in sorted(counts.items()):
    print(f"VOCAB\t{term}\t{df}")

total_len = sum(doc_lens.values())
doc_count = len(doc_lens)
if doc_count > 0:
    print(f"STATS\tdoc_count\t{doc_count}")
    print(f"STATS\tavg_doc_len\t{total_len / doc_count}")