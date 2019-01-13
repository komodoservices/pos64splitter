#!/usr/bin/env python3
import sys
import json
import re
import os
import platform
import pprint
from slickrpc import Proxy

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
    
# function to unlock ALL lockunspent UTXOs
def unlockunspent():
    try:
        listlockunspent_result = rpc_connection.listlockunspent()
    except Exception as e:
        sys.exit(e)
    unlock_list = []
    for i in listlockunspent_result:
        unlock_list.append(i)
    try:
        lockunspent_result = rpc_connection.lockunspent(True, unlock_list)
    except Exception as e:
        sys.exit(e)
    return(lockunspent_result)
    
def extract_segid(_segid,unspents):
    ret = []
    for unspent in unspents:
        if unspent['segid'] == _segid:
            unspent['amount'] = float(unspent['amount'])
            ret.append(unspent)
    return(ret)

CHAIN = input('Please specify chain: ')
try:
    rpc_connection = def_credentials(CHAIN)
except Exception as e:
    sys.exit(e)
balance = float(rpc_connection.getbalance())
print('Balance: ' + str(balance))

PERC = int(input("Please specify the percentage of balance to lock: "))
if PERC < 1:
    sys.exit('Cant lock 0%. Exiting.')

# get listunspent
try:        
    listunspent_result = rpc_connection.listunspent()
except Exception as e:
    sys.exit(e)

# sort into utxos per segid.
segids = []
pp = pprint.PrettyPrinter(indent=4)

for i in range(0,63):
    segid = extract_segid(i, listunspent_result)
    segids.append(segid)

lockunspent_list = []
# Sort it by value and confirms. We want to keep large and old utxos. So largest and oldest at top.
for segid in segids:
    segid = sorted(segid, key=lambda x : (-x['amount'], -x['confirmations'], )) # ? likley some improvment here age vs. size ? this mightr work better if your utxos are mostly the same size. ;)
    numutxo = len(segid) * (PERC/100)
    i = 0
    for unspent in segid:
        output_dict = {
            "txid": unspent['txid'],
            "vout": unspent['vout']
            }
        lockunspent_list.append(output_dict)
        i = i + 1
        if i == int(numutxo):
            break

# Lock % defined of each segids utxos.
lockunspent_result = rpc_connection.lockunspent(False, lockunspent_list)

# get listunspent
try:        
    listunspent_result = rpc_connection.listunspent()
except Exception as e:
    sys.exit(e)
totalbalance = 0
for unspent in listunspent_result:
    totalbalance = float(totalbalance) + float(unspent['amount'])
    
print('Balance avalibe to send: ' + str(totalbalance))

address = input('Address? ')
if len(address) != 34:
    sys.ext('invalid address')  # ? can be improved 
    
amount = float(input('Amount? '))
if amount < 0 or amount > totalbalance:
    sys.exit('Too poor!')
    
print('Sending ' + amount + ' to ' + address)
ret = input('Are you happy with these? ').lower()
if ret.startswith('n'):
    sys.exit('You are not happy?')


# send coins.
txid_result = rpc_connection.sendtoaddress(address, amount)

# unlock all locked utxos
unlockunspent()
print('Success: ' + txid_result)
