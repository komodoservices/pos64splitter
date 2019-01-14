#!/usr/bin/env python3
import sys
import json
import os.path
import stakerlib

if os.path.isfile("list.json"):
    print('Already have list.json, move it if you would like to '
          'generate another set.You can use importlist.py script to import'
          ' the already existing list.py to a given chain.')
    sys.exit(0)

CHAIN = input('Please specify chain:')

# create rpc_connection
try:
    rpc_connection = stakerlib.def_credentials(CHAIN)
except Exception as e:
    sys.exit(e)
    
# fill a list of sigids with matching segid address data
segids = {}
while len(segids.keys()) < 64:
    genvaldump_result = stakerlib.genvaldump(rpc_connection)
    segid = genvaldump_result[0]
    if segid in segids:
        pass
    else:
        segids[segid] = genvaldump_result

# convert dictionary to array
segids_array = []
for position in range(64):
    segids_array.append(segids[position])

# save output to list.py
print('Success! list.json created. '
      'THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.')
f = open("list.json", "w+")
f.write(json.dumps(segids_array))
