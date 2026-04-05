import re
import sys

for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    parts = line.split("\t", 2)
    if len(parts) < 3:
        continue
    doc_id, title, content = parts
    tokens = re.findall(r"[a-z0-9]+", content.lower())
    print(f"{doc_id}\t{title}\t{len(tokens)}")