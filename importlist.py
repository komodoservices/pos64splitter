#!/usr/bin/env python3
import os
import sys
import kmdrpc
import json

if not os.path.isfile("list.json"):
    sys.exit('No list.json file present. Use genaddresses.py script to generate one.')

CHAIN = input('Please specify chain to import list.json keys to:')

with open('list.json') as key_list:
    json_data = json.load(key_list)
    for i in json_data:
        print(i[3])
        kmdrpc.importprivkey_rpc(CHAIN, i[2])
