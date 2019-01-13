#!/usr/bin/env python3
import sys
import json
import re
import os
import platform
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

CHAIN = input('Please specify chain: ')
try:
    rpc_connection = def_credentials(CHAIN)
except Exception as e:
    sys.exit(e)
balance = float(rpc_connection.getbalance())
print('Balance: ' + str(balance))

AMOUNT = input("Please specify the size of UTXOs: ")
if AMOUNT < 1:
    sys.exit('Cant stake coin amounts less than 1 coin, try again.')
UTXOS = input("Please specify the amount of UTXOs to send to each segid: ")
total = float(AMOUNT) * int(UTXOS) * 64
print('Total amount: ' + str(total))
if total > balance:
    print('Total sending is ' + str(total-balance) + ' more than your balance. Try again.')
    segidTotal = balance / 64
    sys.exit('Total avalible per segid is: ' + str(segidTotal))

# iterate addresses list, construct dictionary,
# with amount as value for each address
def sendmany64(amount):
    addresses_dict = {}
    with open('list.json') as key_list:
        json_data = json.load(key_list)
        for i in json_data:
            address = i[3]
            addresses_dict[address] = amount

    # make rpc call, issue transaction
    sendmany_result = rpc_connection.sendmany("", addresses_dict)
    return(sendmany_result)

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def sendmanyloop(amount, utxos):
    txid_list = []
    for i in range(int(utxos)):
        sendmany64_txid = sendmany64(AMOUNT)
        txid_list.append(sendmany64_txid)
        getrawtx_result = rpc_connection.getrawtransaction(sendmany64_txid, 1)
        lockunspent_list = []
        # find change output, lock all other outputs
        for vout in getrawtx_result['vout']:
            if vout['value'] != float(AMOUNT):
                change_output = vout['n']
            else:
                output_dict = {
                    "txid": sendmany64_txid,
                    "vout": vout['n']
                    }
                lockunspent_list.append(output_dict)
        lockunspent_result = rpc_connection.lockunspent(False, lockunspent_list)
    return(txid_list)

sendmanyloop_result = sendmanyloop(AMOUNT, UTXOS)
# unlock all locked utxos
unlockunspent()
for i in sendmanyloop_result:
    print(i)
print('Success!')
