#!/usr/bin/env python3
import os
import sys
import json
from staker import def_credentials

if not os.path.isfile("list.json"):
    sys.exit('No list.json file present. Use genaddresses.py script to generate one.')

CHAIN = input('Please specify chain to import list.json keys to:')

rpc_connection = def_credentials(CHAIN)

with open('list.json') as key_list:
    json_data = json.load(key_list)
    for i in json_data:
        print(i[3])
        rpc_connection.importprivkey(i[2])

