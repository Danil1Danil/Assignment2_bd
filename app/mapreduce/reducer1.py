import sys

for line in sys.stdin:
    line = line.rstrip("\n")
    if line:
        sys.stdout.write(line + "\n")