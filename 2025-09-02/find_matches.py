#!/usr/bin/env python3
import json
import os
import rapidfuzz
import sys
from datasketch import MinHash, MinHashLSH
from multiprocessing import Pool, cpu_count

nprocs = cpu_count()
verA = [os.path.join(sys.argv[1], x) for x in os.listdir(sys.argv[1])]
verB = [os.path.join(sys.argv[2], x) for x in os.listdir(sys.argv[2])]


def calcMH(data, num_perm=128, shingle_size=5):
    m = MinHash(num_perm=num_perm)
    for i in range(len(data) - shingle_size + 1):
        shingle = data[i : i + shingle_size]
        m.update(shingle)
    return m


print(f"Loading all files into memory: {len(verA + verB)}", flush=True)
content = {p: open(p, "rb").read() for p in verA + verB}

print("Calculating hashes", flush=True)
pairs = {}
lsh = MinHashLSH(threshold=0.5, num_perm=128)
with Pool(nprocs) as pool:
    hashes = pool.map(calcMH, [content[p] for p in verA + verB])
    for i, h in enumerate(hashes):
        if i < len(verA):
            lsh.insert(verA[i], h)
            continue
        matches = lsh.query(h)
        if matches:
            pairs[verB[i - len(verA)]] = matches

print("Performing comparisons")


def bestMatch(data):
    verB = data[0]
    toCompare = data[1]
    result = (None, 0)
    for tc in toCompare:
        tcRate = rapidfuzz.fuzz.ratio(content[verB], content[tc])
        if tcRate > result[1]:
            result = (tc, tcRate)
    return verB, result[0], result[1]


matches = []
with Pool(nprocs) as pool:
    matches = pool.map(bestMatch, pairs.items())

result = []
for verB, verA, rate in matches:
    result.append(
        {
            "rate": rate,
            "verA": verA,
            "verB": verB,
        }
    )

with open(sys.argv[3], "w") as f:
    json.dump(result, f)
print("Done")
