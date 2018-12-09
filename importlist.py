#!/usr/bin/env python3
import os
import sys
import kmdrpc

if not os.path.isfile("list.py"):
    sys.exit('No list.py file present. Use genaddresses.py script to generate one.')

from list import segids

CHAIN = input('Please specify chain to import list.py keys to:')

for e in segids:
    kmdrpc.importprivkey_rpc(CHAIN, e[2])
