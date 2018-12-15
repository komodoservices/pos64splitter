#!/usr/bin/env python3
import re
import os
import requests
import json
import platform
import sys
from conf import CoinParams
import bitcoin
from bitcoin.wallet import P2PKHBitcoinAddress
from bitcoin.core import x

bitcoin.params = CoinParams

# define function that fetchs rpc creds from .conf
def def_credentials(chain):
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Win64':
        ac_dir = "dont have windows machine now to test"
    # define config file path
    if chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
    #define rpc creds
    with open(coin_config_file, 'r') as f:
        #print("Reading config file for credentials:", coin_config_file)
        for line in f:
            l = line.rstrip()
            if re.search('rpcuser', l):
                rpcuser = l.replace('rpcuser=', '')
            elif re.search('rpcpassword', l):
                rpcpassword = l.replace('rpcpassword=', '')
            elif re.search('rpcport', l):
                rpcport = l.replace('rpcport=', '')
    return('http://' + rpcuser + ':' + rpcpassword + '@127.0.0.1:' + rpcport)

# define function that posts json data
def post_rpc(url, payload, auth=None):
    try:
        r = requests.post(url, data=json.dumps(payload), auth=auth)
        rpc_result = json.loads(r.text)
        if rpc_result['result'] == None:
            print(str(payload['method']) + ' rpc call failed with ' + str(rpc_result['error']))
            sys.exit(0)
        else:
            return(rpc_result['result'])
    except Exception as e:
        raise Exception("Couldn't connect to " + url + ": ", e)

# Return current -pubkey=
def getpubkey_rpc(chain):
    getinfo_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "getinfo",
        "params": []}
    getinfo_result = post_rpc(def_credentials(chain), getinfo_payload)

    return(getinfo_result['pubkey'])

# function to unlock ALL lockunspent UTXOs
def unlockunspent(CHAIN):
    listlockunspent_result = listlockunspent_rpc(CHAIN)
    unlock_list = []
    for i in listlockunspent_result['result']:
        unlock_list.append(i)

    lockunspent_result = lockunspent_rpc(CHAIN, True, unlock_list)
    return(lockunspent_result)

# VANILLA RPC

def sendrawtx_rpc(chain, rawtx):
    sendrawtx_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "sendrawtransaction",
        "params": [rawtx]}
    return(post_rpc(def_credentials(chain), sendrawtx_payload))

def sendmany_rpc(chain, addresses_dict):
    sendmany_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "sendmany",
        "params": ["", addresses_dict]}
    return(post_rpc(def_credentials(chain), sendmany_payload))

def getrawtransaction_rpc(chain, rawtx):
    getrawtransaction_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "getrawtransaction",
        "params": [rawtx, 1]}
    return(post_rpc(def_credentials(chain), getrawtransaction_payload))

def createrawtransaction_rpc(chain, input_dict, output_dict):
    createrawtransaction_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "createrawtransaction",
        "params": [input_dict, output_dict]}
    return(post_rpc(def_credentials(chain), createrawtransaction_payload))

def signrawtransaction_rpc(chain, rawtx):
    signrawtransaction_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "signrawtransaction",
        "params": [rawtx]}
    return(post_rpc(def_credentials(chain), signrawtransaction_payload))

def validateaddress_rpc(chain, address):
    validateaddress_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "validateaddress",
        "params": [address]}
    return(post_rpc(def_credentials(chain), validateaddress_payload))

def dumpprivkey_rpc(chain, address):
    dumpprivkey_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "dumpprivkey",
        "params": [address]}
    return(post_rpc(def_credentials(chain), dumpprivkey_payload))

def importprivkey_rpc(chain, privkey):
    importprivkey_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "importprivkey",
        "params": [privkey]}
    return(post_rpc(def_credentials(chain), importprivkey_payload))

def getnewaddress_rpc(chain):
    getnewaddress_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "getnewaddress",
        "params": []}
    return(post_rpc(def_credentials(chain), getnewaddress_payload))

def validateaddress_rpc(chain, address):
    validateaddress_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "validateaddress",
        "params": [address]}
    return(post_rpc(def_credentials(chain), validateaddress_payload))

def getbestblockhash_rpc(chain):
    getbestblockhash_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "getbestblockhash",
        "params": []}
    return(post_rpc(def_credentials(chain), getbestblockhash_payload))

def getblock_rpc(chain, block, verbosity):
    getblock_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "getblock",
        "params": [block, verbosity]}
    return(post_rpc(def_credentials(chain), getblock_payload))

def lockunspent_rpc(chain, lock_bool, txid_list):
    lockunspent_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "lockunspent",
        "params": [lock_bool, txid_list]}
    return(post_rpc(def_credentials(chain), lockunspent_payload))

def listlockunspent_rpc(chain):
    listlockunspent_payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": "listlockunspent",
        "params": []}
    return(post_rpc(def_credentials(chain), listlockunspent_payload))
