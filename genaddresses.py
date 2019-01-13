#!/usr/bin/env python3
import sys
import json
import re
import os
import platform
from slickrpc import Proxy
import os.path

if os.path.isfile("list.json"):
    print('Already have list.json, move it if you would like to '
          'generate another set.You can use importlist.py script to import'
          ' the already existing list.py to a given chain.')
    sys.exit(0)

CHAIN = input('Please specify chain:')

def def_credentials(chain):
    rpcport ='';
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Win64':
        ac_dir = "dont have windows machine now to test"
    if chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
    with open(coin_config_file, 'r') as f:
        for line in f:
            l = line.rstrip()
            if re.search('rpcuser', l):
                rpcuser = l.replace('rpcuser=', '')
            elif re.search('rpcpassword', l):
                rpcpassword = l.replace('rpcpassword=', '')
            elif re.search('rpcport', l):
                rpcport = l.replace('rpcport=', '')
    if len(rpcport) == 0:
        if chain == 'KMD':
            rpcport = 7771
        else:
            print("rpcport not in conf file, exiting")
            print("check "+coin_config_file)
            exit(1)
    
    return(Proxy("http://%s:%s@127.0.0.1:%d"%(rpcuser, rpcpassword, int(rpcport))))

# generate address, validate address, dump private key
def genvaldump():
    # get new address
    address = rpc_connection.getnewaddress()
    # validate address
    validateaddress_result = rpc_connection.validateaddress(address)
    segid = validateaddress_result['segid']
    pubkey = validateaddress_result['pubkey']
    address = validateaddress_result['address']
    # dump private key for the address
    privkey = rpc_connection.dumpprivkey(address)
    # function output
    output = [segid, pubkey, privkey, address]
    return(output)

# create rpc_connection
try:
    rpc_connection = def_credentials(CHAIN)
except Exception as e:
    sys.exit(e)
    
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
print('Success! list.json created. '
      'THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.')
f = open("list.json", "w+")
f.write(json.dumps(segids_array))
