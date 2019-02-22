#!/usr/bin/env python3

import platform
import os
import re
import json
import random
import base58
import binascii
import hashlib
import sys
import os.path
import subprocess
from subprocess import DEVNULL, STDOUT, check_call
import urllib.request
import time
from slickrpc import Proxy


# fucntion to define rpc_connection
def def_credentials(chain):
    rpcport = '';
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Windows':
        ac_dir = '%s/komodo/' % os.environ['APPDATA']
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
            print("check " + coin_config_file)
            exit(1)

    return (Proxy("http://%s:%s@127.0.0.1:%d" % (rpcuser, rpcpassword, int(rpcport))))


def user_inputInt(low,high, msg):
    while True:
        user_input = input(msg)
        if user_input == ('q' or 'quit'):
            print('Exiting...')
            sys.exit(0)
        try:
            number = int(user_input)
        except ValueError:
            print("integer only, try again")
            continue
        if low <= number <= high:
            return number
        else:
            print("input outside range, try again")

def selectRangeFloat(low,high, msg):
    while True:
        try:
            number = float(user_input)
        except ValueError:
            print("integer only, try again")
            continue
        if low <= number <= high:
            return number
        else:
            print("input outside range, try again")

def user_input(display, input_type):
    u_input = input(display)
    if u_input == 'q':
        print('Exiting to previous menu...\n')
        return('exit')

    if input_type == float:
        try:
            return(float(u_input))
        except Exception as e:
            print(e)
            return('exit')

    if input_type == int:
        try:
            return(int(u_input))
        except Exception as e:
            print(e)
            return('exit')
    else:
        return(u_input)
    

# generate address, validate address, dump private key
def genvaldump(rpc_connection):
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


def colorize(string, color):
    colors = {
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'green': '\033[92m',
        'red': '\033[91m'
    }
    if color not in colors:
        return string
    else:
        return colors[color] + string + '\033[0m'


# function to convert any address to different prefix 
# also useful for validating an address, use '3c' for prefix for validation
def addr_convert(prefix, address):
    rmd160_dict = {}
    ripemd = base58.b58decode_check(address).hex()[2:]
    net_byte = prefix + ripemd
    bina = binascii.unhexlify(net_byte)
    sha256a = hashlib.sha256(bina).hexdigest()
    binb = binascii.unhexlify(sha256a)
    sha256b = hashlib.sha256(binb).hexdigest()
    hmmmm = binascii.unhexlify(net_byte + sha256b[:8])
    final = base58.b58encode(hmmmm)
    return(final.decode())


# FIXME don't sys.exit from TUI
# function to unlock ALL lockunspent UTXOs
def unlockunspent(rpc_connection):
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


# iterate addresses list, construct dictionary,
# with amount as value for each address
def sendmany64(rpc_connection, amount):
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
def sendmanyloop(rpc_connection, amount, utxos):
    txid_list = []
    for i in range(int(utxos)):
        sendmany64_txid = sendmany64(rpc_connection, amount)
        txid_list.append(sendmany64_txid)
        getrawtx_result = rpc_connection.getrawtransaction(sendmany64_txid, 1)
        lockunspent_list = []
        # find change output, lock all other outputs
        for vout in getrawtx_result['vout']:
            if vout['value'] != float(amount):
                change_output = vout['n']
            else:
                output_dict = {
                    "txid": sendmany64_txid,
                    "vout": vout['n']
                    }
                lockunspent_list.append(output_dict)
        lockunspent_result = rpc_connection.lockunspent(False, lockunspent_list)
    return(txid_list)

def sendmany64_TUI(chain, rpc_connection):
    balance = float(rpc_connection.getbalance())
    print('Balance: ' + str(balance))

    AMOUNT = user_input('Please specify the size of UTXOs: ', float)
    if AMOUNT == 'exit':
        return(0)
    
    if float(AMOUNT) < float(1):
        return('Error: Cant stake coin amounts less than 1 coin, try again.')
    UTXOS = user_input("Please specify the amount of UTXOs to send to each segid: ", int)
    if UTXOS == 'exit':
        return(0)

    total = float(AMOUNT) * int(UTXOS) * 64
    print('Total amount: ' + str(total))
    if total > balance:
        segidTotal = balance / 64
        return('Error: Total sending is ' + str(total-balance) + ' more than your balance. Try again.' + 
              '\nTotal avalible per segid is: ' + str(segidTotal))

    sendmanyloop_result = sendmanyloop(rpc_connection, AMOUNT, UTXOS)
    # unlock all locked utxos
    unlockunspent(rpc_connection)
    for i in sendmanyloop_result:
        print(i)
    print('Success!')

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def RNDsendmanyloop(rpc_connection, amounts):
    txid_list = []
    for amount in amounts:
        sendmany64_txid = sendmany64(rpc_connection, amount)
        txid_list.append(sendmany64_txid)
        getrawtx_result = rpc_connection.getrawtransaction(sendmany64_txid, 1)
        lockunspent_list = []
        # find change output, lock all other outputs
        for vout in getrawtx_result['vout']:
            if vout['value'] != float(amount):
                change_output = vout['n']
            else:
                output_dict = {
                    "txid": sendmany64_txid,
                    "vout": vout['n']
                    }
                lockunspent_list.append(output_dict)
        lockunspent_result = rpc_connection.lockunspent(False, lockunspent_list)
    return(txid_list)

def RNDsendmany_TUI(chain, rpc_connection):

    try:
        balance = float(rpc_connection.getbalance())
    except Exception as e:
        return('Error: ' + str(e))

    print('Balance: ' + str(balance))

    while True:
        UTXOS = user_input("Please specify the amount of UTXOs to send to each segid: ", int)
        if UTXOS == 'exit':
            return(0)
        if UTXOS < 3:
            print('Must have more than 3 utxos per segid, try again.')
            continue
        TUTXOS = UTXOS * 64
        print('Total number of UTXOs: ' + str(TUTXOS))
        average = float(balance) / int(TUTXOS)
        print('Average utxo size: ' + str(average))
        variance = user_input('Enter percentage of variance: ', float)
        if variance == 'exit':
            return(0)
        minsize = round(float(average) * (1-(variance/100)),2)
        if minsize < 1:
            print('Cant stake coin amounts less than 1 coin, try again.')
            continue
        maxsize = round(average + float(average) * (variance/100),2)
        print('Min size: ' + str(minsize))
        print('Max size: ' + str(maxsize))
        ret = input('Are you happy with these?(y/n): ').lower()
        if ret.startswith('y'):
            break

    total = 0
    totalamnt = 0
    AMOUNTS = []
    finished = False

    while finished == False:
        for i in range(UTXOS):
            amnt = round(random.uniform(minsize,maxsize),2)
            totalamnt += amnt * 64
            AMOUNTS.append(amnt)
            if totalamnt > balance-0.1:
                totalamnt = 0
                AMOUNTS.clear()
                break
        if totalamnt > balance-2:
            finished = True

    sendmanyloop_result = RNDsendmanyloop(rpc_connection, AMOUNTS)
    # unlock all locked utxos
    unlockunspent(rpc_connection)
    for i in sendmanyloop_result:
        print(i)
    print('Success!')

def genaddresses(chain, rpc_connection): # FIXME don't print in start script
    if os.path.isfile("list.json"):
        return('Error: Already have list.json, move it if you would like to '
              'generate another set.You can use importlist.py script to import'
              ' the already existing list.py to a given chain.')
    
    # fill a list of sigids with matching segid address data
    segids = {}
    while len(segids.keys()) < 64:
        genvaldump_result = genvaldump(rpc_connection)
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
    f = open("list.json", "w+")
    f.write(json.dumps(segids_array))
    return('Success! list.json created. '
          'THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.')

# FIXME make this rescan only on 64th import
# import list.json to chain 
def import_list(chain, rpc_connection):
    if not os.path.isfile("list.json"):
        return('Error: No list.json file present. Use genaddresses.py script to generate one.')

    with open('list.json') as key_list:
        json_data = json.load(key_list)
        for i in json_data:
            print(i[3])
            rpc_connection.importprivkey(i[2])
    print('Success!')
    
def extract_segid(_segid,unspents):
    ret = []
    for unspent in unspents:
        if unspent['segid'] == _segid:
            unspent['amount'] = float(unspent['amount'])
            ret.append(unspent)
    return(ret)

def withdraw_TUI(chain, rpc_connection):

    def unlockunspent2():
        try:
            listlockunspent_result = rpc_connection.listlockunspent()
        except Exception as e:
            print(e)
            withdraw_TUI(chain, rpc_connection)
        unlock_list = []
        for i in listlockunspent_result:
            unlock_list.append(i)
        try:
            lockunspent_result = rpc_connection.lockunspent(True, unlock_list)
        except Exception as e:
            print(e)
            withdraw_TUI(chain, rpc_connection)
        return(lockunspent_result)

    balance = float(rpc_connection.getbalance())
    print('Balance: ' + str(balance))

    address = input('Please specify address to withdraw to: ')
    try:
        address_check = addr_convert('3c', address)
    except Exception as e:
        print('invalid address:', str(e) + '\n')
        withdraw_TUI(chain, rpc_connection)

    if address_check != address:
        print('Wrong address format, must use an R address')
        withdraw_TUI(chain, rpc_connection)
    
    user_input = input("Please specify the percentage of balance to lock: ")
    try:
        PERC = int(user_input)
    except:
        print('Error: must be whole number')
        withdraw_TUI(chain, rpc_connection)
    
    if PERC < 1:
        print('Error: Cant lock 0%.')
        withdraw_TUI(chain, rpc_connection)

    # get listunspent
    try:        
        listunspent_result = rpc_connection.listunspent()
    except Exception as e:
        return('Error: ' + str(e))

    # sort into utxos per segid.
    segids = []

    for i in range(0,63):
        segid = extract_segid(i, listunspent_result)
        segids.append(segid)

    lockunspent_list = []
    # Sort it by value and confirms. We want to keep large and old utxos. So largest and oldest at top.
    # When the wallet has small number of utxo per segid ( < 10 )the percentage should be static 50, other % give unexpected results.
    for segid in segids:
        # likley some improvment here age vs. size ? 
        # there should maybe be a utxo score, that includes age and size and locks utxos with highest score.
        segid = sorted(segid, key=lambda x : (-x['amount'], -x['confirmations']))
        numutxo = int(len(segid) * (PERC/100))
        i = 0
        for unspent in segid:
            output_dict = {
                "txid": unspent['txid'],
                "vout": unspent['vout']
                }
            lockunspent_list.append(output_dict)
            i = i + 1
            if i >= numutxo:
                break

    # Lock % defined of each segids utxos.
    lockunspent_result = rpc_connection.lockunspent(False, lockunspent_list)

    # get listunspent
    try:        
        listunspent_result = rpc_connection.listunspent()
    except Exception as e:
        return('Error: ' + str(e))
    totalbalance = 0
    for unspent in listunspent_result:
        totalbalance = float(totalbalance) + float(unspent['amount'])

    balance = rpc_connection.getbalance()
    if totalbalance == balance:
        print('Balance available to send: ' + str(totalbalance))
    else:
        print('Balance available to send: ' + str(totalbalance))
        
    print('Balance available to send: ' + str(totalbalance))
        
    amount = float(input('Amount? '))
    if amount < 0 or amount > totalbalance:
        unlockunspent2()
        return('Error: Too poor!')
        
    print('Sending ' + str(amount) + ' to ' + address)
    ret = input('Are you happy with these? ').lower()
    if ret.startswith('n'):
        unlockunspent2()
        print('You are not happy?')
        return(0)

    # send coins.
    txid_result = rpc_connection.sendtoaddress(address, amount)

    # unlock all locked utxos
    unlockunspent2()
    return('Success: ' + txid_result)


def start_daemon(chain):
    params = get_chainparams(chain)
    if params == 0:
        return('Error: ' + chain + ' not found in assetchains.json')# FIXME
    print(params)
    komodod_path = sys.path[0] + '/komodod'
    param_list = [komodod_path]
    with open('list.json', 'r') as f:
        list_json = json.load(f)
        mypubkey = list_json[0][1]
    pubkey = '-pubkey=' + mypubkey
    for i in params:
       if i == 'addnode':
           for ip in params[i]:
               param_list.append('-addnode=' + ip)
       else:
           param_list.append('-' + i + '=' + params[i])
    param_list.append(pubkey)
    proc = subprocess.Popen(param_list, stdout=DEVNULL, stderr=STDOUT, preexec_fn=os.setpgrp)
    print('Waiting for daemon to respond, please wait')
    while True:
        time.sleep(10)
        try:
            rpc_connection = def_credentials(chain)
            rpc_connection.getinfo()
            break
        except Exception as e:
            continue
    return(0)

def restart_daemon(chain, params, rpc_connection):
    magic_check = rpc_connection.getinfo()['p2pport']
    with open('list.json', 'r') as f:
        list_json = json.load(f)
        mypubkey = list_json[0][1]
    print(magic_check)
    rpc_connection.stop()
    print('Waiting for daemon to stop, please wait')
    while True:
        try:
            rpc_connection.getinfo()
            continue
        except Exception as e:
            break
    
    komodod_path = sys.path[0] + '/komodod'
    blocknotify = '-blocknotify=' + sys.path[0] + '/staker.py %s ' + chain
    pubkey = '-pubkey=' + mypubkey
    param_list = [komodod_path]
    for i in params:
       param_list.append('-' + i + '=' + params[i])
    param_list.append(blocknotify)
    param_list.append(pubkey)
    proc = subprocess.Popen(param_list, stdout=DEVNULL, stderr=STDOUT, preexec_fn=os.setpgrp)
    #check_call(param_list, stdout=DEVNULL, stderr=STDOUT)
    #subprocess.run(param_list, shell=False, stdout=None, stderr=None, timeout=1)
    print('Waiting for daemon to respond, please wait')
    while True:
        time.sleep(10)
        try:
            rpc_connection = def_credentials(chain)
            rpc_connection.getinfo()
            break
        except Exception as e:
            continue
    magic = rpc_connection.getinfo()['p2pport']
    if magic != magic_check:
        return('Error: Daemon started with different p2p port. Please verify that the parameters in assetchains.json are correct')
    return('Daemon restarted succesfully!')

    

def get_chainparams(chain):
    operating_system = platform.system()
    ac_names = []
    if operating_system == 'Linux':
        if os.path.isfile("komodod"):
            if not os.path.isfile("assetchains.json"):
                print("No assetchains.json found. Downloading latest from jl777\'s beta branch")
                urllib.request.urlretrieve("https://raw.githubusercontent.com/jl777/komodo/beta/src/assetchains.json", "assetchains.json")
            with open('assetchains.json', 'r') as f:
                asset_json = json.load(f)
                #for lol in asset_json:
                    #ac_names.append(i['ac_name'])
                #if chain in ac_names:
                for i in asset_json:
                    ac_names.append(i['ac_name'])
                
                if chain not in ac_names:# FIXME
                    return(0)
                else:
                    for i in asset_json:
                        if i['ac_name'] == chain:
                            return(i)
        else:
            print('Please copy/move komodod to the same directory as TUIstaker.py')
    else:
        print('Linux is the only supported OS right now. Please restart daemon manually')

def createchain(chain, rpc_connection):
    def blockcount():
        while True:
            time.sleep(10)
            getinfo_result = rpc_connection.getinfo()
            if getinfo_result['blocks'] > 1:
                rpc_connection.setgenerate(False)
                return(0)

    getinfo_result = rpc_connection.getinfo()
    print(getinfo_result['name'])
    #if user_yn.startswith('y'):
     #   import_list(chain, rpc_connection)
    #else:
     #   return('Error: must import a list.json to begin.')

    params = get_chainparams(chain)# FIXME
    if params == 0:
        return('Error: chain not in assetchains.json')

    if 'ac_script' in params:
        return('Error: This script is incompatible with ac_script. ' +
                'You must fund this node then use RNDsendmany instead.')

    if 'ac_pubkey' in params:
        return('Error: ' + str(params))

    if getinfo_result['blocks'] != 0:
        return('Error: must be used on a new chain')

    peers = rpc_connection.getpeerinfo()
    if not peers:
        return('Error: No peers found, please connect your node to at least one other peer.')

    if 'eras' in getinfo_result:
        return('Error: This script is incompatible with ac_eras chains. Please use genaddresses then RNDsendmany after block 100 instead.')


    def sendtoaddress(chain, rpc_connection):
        address = input("Please specify address to withdraw coins to. It must not be owned by this node: ")
        try:
            address_check = addr_convert('3c', address)
        except Exception as e:
            print('invalid address:', str(e) + '\n')
            sendtoaddress(chain, rpc_connection)
        if address_check != address:
            print('Wrong address format, must use an R address')
            sendtoaddress(chain, rpc_connection)
        amount = input("Please specify the amount of coins to send: ")
        sendtoaddress_result = rpc_connection.sendtoaddress(address_check, amount)
        print(sendtoaddress_result)

    if os.path.isfile("list.json"):
        user_yn = input('Existing list.json found, would you like to import it?(y/n): ').lower()
        if user_yn.startswith('y'):
            import_list(chain, rpc_connection)
        else:
            return('Error: must import a list.json to begin.')

    else:
        print('Generating list.json, please wait...')
        genaddresses(chain, rpc_connection)



    print('Mining blocks 1 and 2, please wait')
    rpc_connection.setgenerate(True, 2)

    blockcount()

    balance = rpc_connection.getbalance()
    #if genaddresses(chain, rpc_connection) == 1:
    ret = input('Would you like to stake the full premine?(y/n): ').lower()
    if not ret.startswith('y'):
        print('Balance: ' + str(rpc_connection.getbalance()))
        sendtoaddress(chain, rpc_connection)
    RNDsendmany_TUI(chain, rpc_connection)
    restart_daemon(chain, params, rpc_connection)
    rpc_connection.setgenerate(True, 0)
    return('Your node has now begun staking. Ensure that at least one other node is mining.')

