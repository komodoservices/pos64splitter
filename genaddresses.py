#!/usr/bin/env python3
import json
import requests
import sys
import kmdrpc
import os.path

if os.path.isfile("list.py"):
    sys.exit('Already have list.py, move it if you would like to generate another set. You can use importlist.py script to import the already existing list.py to a given chain.')

CHAIN = input('Please specify chain:')

# generate address, validate address, dump private key
def genvaldump():
    # get new address
    getnewaddress_result = kmdrpc.getnewaddress_rpc(CHAIN)
    address = getnewaddress_result['result']
    # validate address
    validateaddress_result = kmdrpc.validateaddress_rpc(CHAIN, address)
    segid = validateaddress_result['result']['segid']
    pubkey = validateaddress_result['result']['pubkey']
    address = validateaddress_result['result']['address']
    # dump private key for the address
    dumpprivkey_result = kmdrpc.dumpprivkey_rpc(CHAIN, address)
    privkey = dumpprivkey_result['result']
    # function output
    output = [segid, pubkey, privkey, address]
    return(output)


# fill a list of sigids with matching segid address data
segids = {}
while len(segids.keys()) < 64:
    genvaldump_result = genvaldump()
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
print('Success! list.py created. THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.')
f = open("list.py","w+")
f.write("segids = " + str(json.dumps(segids_array)))
