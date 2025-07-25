#!/bin/env python

import collections
import sys

permFiles = sorted(sys.argv[1:])
compMap = collections.defaultdict(lambda:["-"]*len(permFiles))
for i, arg in enumerate(permFiles):
  for perm in open(arg):
      compMap[perm.strip()][i] = "+"

print("Permission;", "; ".join(permFiles))
for perm, files in sorted(compMap.items(), key=lambda key: -key[1].count("+")):
  print("%s %s" % ("".join(files), perm))
