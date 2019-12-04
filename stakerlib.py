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
import tarfile
import shutil
import time
import secrets
import bitcoin
from bitcoin.wallet import P2PKHBitcoinAddress
from bitcoin.core import x
from bitcoin.core import CoreMainParams
from slickrpc import Proxy

if platform.system() != 'Windows':
    import readline

class CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 60,
                       'SCRIPT_ADDR': 85,
                       'SECRET_KEY': 188}

bitcoin.params = CoinParams


# define data dir
def def_data_dir():
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Windows':
        ac_dir = '%s/komodo/' % os.environ['APPDATA']
    return(ac_dir)

# fucntion to define rpc_connection
def def_credentials(chain):
    rpcport = '';
    ac_dir = def_data_dir()
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
            user_input = input(msg)
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
    if platform.system() == 'Windows' or color not in colors:
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


# function to unlock ALL lockunspent UTXOs
def unlockunspent(rpc_connection):
    listlockunspent_result = rpc_connection.listlockunspent()
    unlock_list = []
    for i in listlockunspent_result:
        unlock_list.append(i)
    try:
        lockunspent_result = rpc_connection.lockunspent(True, unlock_list)
    except Exception as e:
        return('Error: lockunspent rpc command failed with ' + str(e))
    return(lockunspent_result)


# iterate addresses list, construct dictionary,
# with amount as value for each address
def sendmany64(rpc_connection, amount):
    chain = rpc_connection.getinfo()['name']
    addresses_dict = {}
    if not os.path.isfile(chain + ".json"):
        return('Error: + ' + chain + '.json not found. Please use importlist to import one ' +
               'or genaddresses to create one.')
    with open(chain + ".json") as key_list:
        json_data = json.load(key_list)
        for i in json_data:
            address = i[3]
            addresses_dict[address] = amount

    # make rpc call, issue transaction
    try:
        sendmany_result = rpc_connection.sendmany("", addresses_dict, 0)
    except Exception as e:
        return('Error: sendmany command failed with ' + str(e) + '\nPlease use [8 | unlock all locked utxos] then try again')
    return(sendmany_result)

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def sendmanyloop(rpc_connection, amount, utxos):
    txid_list = []
    for i in range(int(utxos)):
        sendmany64_txid = sendmany64(rpc_connection, amount, 0)
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
        return('0')
    
    if float(AMOUNT) < float(1):
        return('Error: Cant stake coin amounts less than 1 coin, try again.')
    UTXOS = user_input("Please specify the amount of UTXOs to send to each segid: ", int)
    if UTXOS == 'exit':
        return('0')

    total = float(AMOUNT) * int(UTXOS) * 64
    print('Total amount: ' + str(total))
    if total > balance:
        segidTotal = balance / 64
        return('Error: Total sending is ' + str(total-balance) + ' more than your balance. Try again.' + 
              '\nTotal avalible per segid is: ' + str(segidTotal))

    sendmanyloop_result = sendmanyloop(rpc_connection, AMOUNT, UTXOS)

    # unlock all locked utxos
    unlock_response = unlockunspent(rpc_connection)
    if str(unlock_response).startswith('Error'):
        return(unlock_response)

    for i in sendmanyloop_result:
        print(i)
    print('Success!')

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def RNDsendmanyloop(rpc_connection, amounts):
    txid_list = []
    for amount in amounts:
        time.sleep(1)
        sendmany64_txid = sendmany64(rpc_connection, amount)
        if str(sendmany64_txid).startswith('Error'):
            return(sendmany64_txid)
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

    if not os.path.isfile(chain + ".json"):
        return('Error: ' + chain + '.json not found. Please use importlist to import one ' +
               'or genaddresses to create one.')
    try:
        balance = float(rpc_connection.getbalance())
    except Exception as e:
        return('Error: ' + str(e))

    print('Balance: ' + str(balance))

    while True:
        UTXOS = user_input("Please specify the amount of UTXOs to send to each segid: ", int)
        if UTXOS == 'exit':
            return('0')
        if UTXOS < 3:
            print('Must have more than 3 utxos per segid, try again.')
            continue
        TUTXOS = UTXOS * 64
        print('Total number of UTXOs: ' + str(TUTXOS))
        average = float(balance) / int(TUTXOS)
        print('Average utxo size: ' + str(average))
        variance = user_input('Enter percentage of variance: ', float)
        if variance == 'exit':
            return('0')
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
    print('Please wait....')

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
    if str(sendmanyloop_result).startswith('Error'):
        return(str(sendmanyloop_result))

    # unlock all locked utxos
    unlock_response = unlockunspent(rpc_connection)
    if str(unlock_response).startswith('Error'):
        return(unlock_response)

    for i in sendmanyloop_result:
        print(i)
    return('Success!')

def genaddresses(chain, rpc_connection):
    if os.path.isfile(chain + ".json"):
        return('Error: Already have ' + chain + '.json, move it if you would like to '
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

    # save output to <CHAIN>.json
    f = open(chain + ".json", "w+")
    f.write(json.dumps(segids_array))
    return('Success! ' + chain + '.json created. '
          'THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.')


# import list.json to chain 
def import_list(chain, rpc_connection):
    user_input = input('Please specify a json file to import: ')
    if not os.path.isfile(user_input):
        return('Error: File not found. Make sure you use the full file name. ' +
               'You can use the genaddresses option to generate a new one.')

    with open(user_input) as key_list:
        try:
            json_data = json.load(key_list)
        except Exception as e:
            return('Error: Please ensure this file is a valid json.\n' + str(e))

    for i in json_data[:-1]:
        print(rpc_connection.importprivkey(i[2], "", False))

    print(rpc_connection.importprivkey(json_data[-1][2]))
    # save output to <CHAIN>.json
    f = open(chain + ".json", "w+")
    f.write(json.dumps(json_data))
    return('Success! Your node is now rescanning. ' + 
           'This may take a long amount of time. ' + 
           'You can monitor the progress from the debug.log\n' + 
           chain + '.json created! THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE!')
    
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


def start_daemon(chain, no_pk):
    params = get_chainparams(chain)
    if params == 0:
        return('Error: ' + chain + ' not found in assetchains.json')
    komodod_path = sys.path[0] + '/komodod'
    param_list = [komodod_path]
    if no_pk != 1:
        with open(chain + ".json", 'r') as f:
            list_json = json.load(f)
            mypubkey = list_json[0][1]
        pubkey = '-pubkey=' + mypubkey
        param_list.append(pubkey)
    if not params:
        print('Please move or copy komodod to this directory.')
        sys.exit(0)
    for i in params:
       if i == 'addnode':
           for ip in params[i]:
               param_list.append('-addnode=' + ip)
       else:
           param_list.append('-' + str(i) + '=' + str(params[i]))
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

def is_chain_synced(chain):
    rpc_connection = def_credentials(chain)
    getinfo_result = rpc_connection.getinfo()
    blocks = getinfo_result['blocks']
    longestchain = getinfo_result['longestchain']
    if blocks == longestchain:
        return(0)
    else:
        return([blocks, longestchain])


def restart_daemon(chain, params, rpc_connection):
    magic_check = rpc_connection.getinfo()['p2pport']
    try:
        with open(chain + ".json", 'r') as f:
            list_json = json.load(f)
            mypubkey = list_json[0][1]
    except:
        return('Error: ' + chain + '.json not found. Please use genaddresses or importlist to create it.')
    rpc_connection.stop()
    print('Waiting for daemon to stop, please wait')
    while True:
        try:
            time.sleep(5)
            rpc_connection.getinfo()
            continue
        except Exception as e:
            break
    
    komodod_path = sys.path[0] + '/komodod'
    blocknotify = '-blocknotify=' + sys.path[0] + '/staker.py %s ' + chain
    pubkey = '-pubkey=' + mypubkey
    param_list = [komodod_path]
    for i in params:
       if i == 'addnode':
           for ip in params[i]:
               param_list.append('-addnode=' + ip)
       else:
           param_list.append('-' + str(i) + '=' + str(params[i]))
    param_list.append(blocknotify)
    param_list.append(pubkey)
    proc = subprocess.Popen(param_list, stdout=DEVNULL, stderr=STDOUT) #, preexec_fn=os.setpgrp)
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
    if operating_system == 'Linux' or operating_system == 'Darwin':
        if os.path.isfile("komodod"):
            if not os.path.isfile("assetchains.json"):
                print("No assetchains.json found. Downloading latest from jl777\'s beta branch")
                urllib.request.urlretrieve("https://raw.githubusercontent.com/jl777/komodo/beta/src/assetchains.json", "assetchains.json")
            with open('assetchains.json', 'r') as f:
                asset_json = json.load(f)
                for i in asset_json:
                    ac_names.append(i['ac_name'])
                
                if chain not in ac_names:
                    return(0)
                else:
                    for i in asset_json:
                        if i['ac_name'] == chain:
                            return(i)
        else:
            print('Please copy/move komodod to the same directory as TUIstaker.py')
    else:
        print('This feature is not supported in Windows. Please restart daemon manually') #FIXME should work on OSX just fine, test windows

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

    if os.path.isfile(chain + ".json"):
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


def fetch_bootstrap(chain):
    bootstrap_list = []
    urllib.request.urlretrieve("https://dexstats.info/api/bootstraps.php?version1", "bootstraps.json")
    with open('bootstraps.json', 'r') as f:
        bootstrap_json = json.load(f)
    for bootstrap in bootstrap_json['mirrors']:
        bootstrap_list.append(bootstrap['coin'])
    if chain in bootstrap_list:
        data_dir = def_data_dir()
        chain_dir = data_dir + '/' + chain
        if os.path.isdir(chain_dir + '/blocks') or os.path.isdir(chain_dir + '/chainstate'):
            user_yn = input('You already have a data directory for ' + chain + 
                            '. This will delete the local chain if one exists. ' +
                            'Would you like to continue?(y/n)')
            if not user_yn.startswith('y'):
                return('Error: Please sync the chain manually.') 
        for bootstrap in bootstrap_json['mirrors']:
            if bootstrap['coin'] == chain:
                print('Downloading ' + chain + ' bootstrap from ' + bootstrap['downloadurl'] + ' please wait')
                # FIXME better check to test is downloads fails
                try:
                    urllib.request.urlretrieve(bootstrap['downloadurl'], chain + "-bootstrap.tar.gz")
                except Exception as e:
                    return('Error: Download failed with error ' + str(e))
                if os.path.isdir(chain_dir + '/blocks'):
                    shutil.rmtree(chain_dir + '/blocks')
                if os.path.isdir(chain_dir + '/chainstate'):
                    shutil.rmtree(chain_dir + '/chainstate') 
    else:
        return('Dexstats does not have a bootstrap for this coin. You must sync the chain manually.')


    extract = []
    bootstrap = chain + '-bootstrap.tar.gz'
    if not os.path.isfile(bootstrap):
        return('Error: Bootstrap download failed.')

    tar = tarfile.open(bootstrap, "r:gz")
    for member in tar.getmembers():
        if member.mode != 384:
            perms = ['blocks', 'chainstate', 'blocks/index']
            if member.name in perms:
                if member.mode != 448:
                    return('Error:file ' + member.name + ' has improper file permissions! Report this to Alright')
            else:
                return('Error:file ' + member.name + ' has improper file permissions! Please report this to Alright')
        if member.name.startswith('blocks') or member.name.startswith('chainstate'):
            extract.append(member.name)
        else:
            return('Error: this file should not be here ' + member.name + ' Please report this to Alright.')

    ac_dir = def_data_dir()
    chain_path = ac_dir + '/' + chain
    print('Extracting ' + bootstrap + ' to ' + chain_path + ' , please wait')
    for i in extract:
        tar.extract(i, path=chain_path) 
    user_yn = input('Bootstrap installed. Would you like to delete the tar.gz file?(y/n): ')
    if user_yn.startswith('y'):
        os.remove(bootstrap)
        return('Success! Use the start a chain from assetchains.json option to start the daemon.' +
               'If you found this feature useful, please consider donating to dexstats.info ' +
               '\nRQFwNuhJ5HP1QbfU2wLj8ZUse43LSKrzei')

    else:
        return('Success! Use the start a chain from assetchains.json option to start the daemon.')


# wrapped for Dilithium rpc commands
def dil_wrap(method, params, rpc_connection):
    if method == 'keypair':
        wrapped = '\"[%22rand%22]\"'
    if method == 'sign' or method == 'handleinfo':
        wrapped = '\"[%22' + str(params) + '%22]\"'
    elif method == 'register':
        wrapped = '\"[%22' + str(params[0]) + '%22,%22' + str(params[1]) + '%22]\"'
    elif method == 'verify' or method == 'spend':
        wrapped = '\"[%22' + str(params[0]) + '%22,%22' + str(params[1]) + '%22,%22' + str(params[2]) + '%22]\"'
    elif method == 'send':
        wrapped = '\"[%22' + str(params[0]) + '%22,%22' + str(params[1]) + '%22,' + str(params[2]) + ']\"'
    elif method == 'Qsend':
        wrapped = '\"[%22' + str(params[0]) + '%22,%22' + str(params[1]) + '%22,%22' + str(params[2]) + '%22,' + str(params[3]) + ']\"'
    rpc_result = rpc_connection.cclib(method, '19', wrapped)
    return(rpc_result)


# FIXME check if handle exists, right now it overwrites if same name is used twice
# {'evalcode': 19, 'funcid': 'R', 'name': 'dilithium', 'method': 'register', 'help': 'handle, [hexseed]', 'params_required': 1, 'params_max': 2}
def dil_register(chain, rpc_connection):

    # create dummy conf is one does not exist
    if not os.path.isfile('dil.conf'):
        with open('dil.conf', "w") as f:
            json.dump({}, f)

    user_input = input('please give an abitrary name to register with.' +
                       'This will create a dilithium keypair that is ' +
                       'tied to the current -pubkey: ')
    with open('dil.conf') as file:
        dil_conf = json.load(file)

    params = []
    params.append(user_input)

    # generate random seed key pair
    keypair = dil_wrap('keypair', 0, rpc_connection)
    params.append(keypair['seed'])

    # register with seed from keypair result
    try:
        register_result = dil_wrap('register', params, rpc_connection)
        #rawhex = register_result['hex']
    except Exception as e:
        return('Error: dilithium register method failed with ' + str(e))
    rawhex = register_result['hex']

    #broadcast register transaction
    try:
        txid = rpc_connection.sendrawtransaction(rawhex)
    except Exception as e:
        return('Error: attempting to broadcast register failed with ' + str(e))

    register_result['normal_pubkey'] = rpc_connection.setpubkey()['pubkey'] # FIXME check if -pubkey is set prior to entering dil menu
    register_result['seed'] = keypair['seed']
    register_result['pubkey'] = keypair['pubkey']
    register_result['privkey'] = keypair['privkey']
    print(register_result['handle'])
    handle = register_result['handle']

    try:
        dil_conf[handle] = register_result
    except:
        dil_dict = {}
        dil_conf[handle] = register_result

    with open('dil.conf', "w") as f:
        json.dump(dil_conf, f)
    return('Success!\npkaddr: ' + register_result['pkaddr'] + 
           '\nskaddr: ' + register_result['skaddr'] + '\ntxid: ' + register_result['txid'])


# ask user to select a handle from dil.conf, outputs selected handled
def handle_select(msg, rpc_connection, show_balance):
    with open('dil.conf') as file:
        dil_conf = json.load(file)
    count = 0
    handle_list = []
    for i in dil_conf:
        if show_balance == 1: # FIXME this could definitely display balances in a better format
            balances = dil_balance(rpc_connection)
            try:
                print(str(count) + ' | ' + i + ' balance:' + str(balances[i]))
            except:
                print(str(count) + ' | ' + i + ' balance:0')
        else:
            print(str(count) + ' | ' + i)
        handle_list.append(i)
        count += 1
    handle_entry = user_inputInt(0,len(dil_conf)-1, msg)
    return(handle_list[handle_entry]) 


# list dilithium handles
def list_handles():
    try:
        with open('dil.conf') as file:
            dil_conf = json.load(file)
    except Exception as e:
        return('Error: verify failed with: ' + str(e) + '\nPlease use the register command if you haven\'t already')
    result_dict = {}
    for i in dil_conf:
        result_dict[i] = dil_conf[i]['txid']
    return(result_dict)


# function to decode dil send OP_RETURN, returns register txid / 'destpubtxid'
def decode_dil_send(txid, rpc_connection):
    tx = rpc_connection.getrawtransaction(txid, 1)
    scriptPubKey = tx['vout'][-1]['scriptPubKey']['hex']
    ba = bytearray.fromhex(endian_flip(scriptPubKey))
    decode = rpc_connection.decodeccopret(scriptPubKey)
    if decode['OpRets'][0]['eval_code'] == '0x13' and decode['OpRets'][0]['function'] == 'x':
        register_txid = ''.join(format(x, '02x') for x in ba)[:64]
        return(register_txid)


# Dilithium listunspent for handles saved in dil.conf
def dil_listunspent(rpc_connection, mine):
    address_dict = {}
    # use handles saved in dil.conf
    if mine == 1:
        try:
            with open('dil.conf') as f:
                dil_conf = json.load(f)
        except Exception as e:
            return('Error: verify failed with: ' + str(e) + ' Please use the register command if you haven\'t already')
        # get our CC address and our CC address's UTXOs
        CC_address = rpc_connection.cclibaddress('19')['myCCAddress(CClib)']

    # use a user specified handle
    elif mine == 0:
        u_input = input('Please specify a handle: ')
        handleinfo_result = dil_wrap('handleinfo', u_input, rpc_connection)
        try:
            pubkey = handleinfo_result['pubkey']
            destpubtxid = handleinfo_result['destpubtxid']
        except:
            return('Error: Handle not found')
        CC_address = rpc_connection.cclibaddress('19', pubkey)['PubkeyCCaddress(CClib)']
        dil_conf = {}
        dil_conf[u_input] = {'txid': destpubtxid}

    # no user input, use arg 3 as handle
    else:
        handleinfo_result = dil_wrap('handleinfo', mine, rpc_connection)
        try:
            pubkey = handleinfo_result['pubkey']
            destpubtxid = handleinfo_result['destpubtxid']
        except:
            return('Error: Handle not found')
        CC_address = rpc_connection.cclibaddress('19', pubkey)['PubkeyCCaddress(CClib)']
        dil_conf = {}
        dil_conf[mine] = {'txid': destpubtxid}
        

    address_dict['addresses'] = [CC_address]
    CC_txids = rpc_connection.getaddressutxos(address_dict)

    txids = []
    result_dict = {}
    for i in dil_conf:
        result_dict[i] = []

    # iterate over CC address UTXOs
    for CC_utxo in CC_txids:        
        tx = rpc_connection.getrawtransaction(CC_utxo['txid'], 1)
        height = tx['height']
        
        # check if UTXO has an OP_RETURN, decode OP_RETURN with decodeccopret rpc command 
        if tx['vout'][-1]['scriptPubKey']['type'] == 'nulldata':
            OP_hex = tx['vout'][-1]['scriptPubKey']['hex']
            decode = rpc_connection.decodeccopret(OP_hex)
            bigend_OP = endian_flip(OP_hex)

            # check if UTXO is Dilithium 'send' command
            if decode['OpRets'][0]['eval_code'] == '0x13' and decode['OpRets'][0]['function'] == 'x':
                #print(tx['vout'][-1]['scriptPubKey']['hex'])
                from_address = []
                for vin in tx['vin']:
                    if not vin['address'] in from_address:
                        from_address.append(vin['address'])
                txids.append(CC_utxo['txid'])

                # get the 'destpubtxid' of UTXO
                register_txid = decode_dil_send(CC_utxo['txid'], rpc_connection)
                # iterate over saved handles, if 'destpubtxid' matches, save UTXO to handle's list
                for handle in dil_conf:
                    if decode_dil_send(CC_utxo['txid'], rpc_connection) == dil_conf[handle]['txid']:
                        txid_dict = {'txid': CC_utxo['txid'],
                                     'value': tx['vout'][0]['valueSat'] / 100000000,
                                     'vout': CC_utxo['outputIndex'],
                                     'funcid': 'x',
                                     'height': height,
                                     'received_from': from_address}
                        result_dict[handle].append(txid_dict)

            # check if UTXO is Dilithium 'Qsend' command
            if decode['OpRets'][0]['eval_code'] == '0x13' and decode['OpRets'][0]['function'] == 'Q':
                for handle in dil_conf:
                    # the 'destpubtxid' of sender will always be bigend_OP[-76:-12] for Qsend txs
                    from_handle = handle_get(bigend_OP[-76:-12], rpc_connection)
                    # the beginning of bigend_OP will begin with 'destpubtxid' of each 
                    # output or 32 null bytes if output is to a normal R address
                    vout_length = len(tx['vout']) - 1
                    # slice bigend_OP, regex 'destpubtxid' of each output
                    raw_register_txids = bigend_OP[:64*vout_length]
                    register_txids = re.findall('.{1,64}', raw_register_txids)
                    register_txids.reverse()

                    # if a saved handle owns a CC address UTXO, save UTXO to handle's list
                    if dil_conf[handle]['txid'] in register_txids:
                        vout_positions = list_pos(register_txids, dil_conf[handle]['txid'])
                        for i in vout_positions:
                            if i == CC_utxo['outputIndex']:
                                value = tx['vout'][CC_utxo['outputIndex']]['valueSat'] / 100000000
                                txid_dict = {'txid': CC_utxo['txid'],
                                             'value': value,
                                             'vout': i,
                                             'funcid': 'Q',
                                             'height': height,
                                             'received_from': from_handle}
                                result_dict[handle].append(txid_dict)

    return(result_dict)


# {'evalcode': 19, 'funcid': 'x', 'name': 'dilithium', 'method': 'send', 'help': 'handle pubtxid amount', 'params_required': 3, 'params_max': 3}
def dil_send(chain, rpc_connection):
    user_yn = input('Would you like to deposit coins to an external handle? ' + 
                    ' If you select no, the local handles saved in dil.conf ' + 
                    'will be used(y/n):')
    if user_yn.startswith('y'):
        handle = input('Please input a handle to send to: ')
        pubtxid = dil_wrap('handleinfo', handle, rpc_connection)['destpubtxid']

    else:
        try:
            with open('dil.conf') as f:
                dil_conf = json.load(f)
        except Exception as e:
            return('Error: failed with: ' + str(e) + 
                   ' Please use the register command if you haven\'t already')

        # FIXME add a warning here if normal_pubkey is not own by current wallet
        handle_entry = handle_select("Select handle to deposit coins to: ", rpc_connection, 0)
        print('handle_e', handle_entry)
        handle = dil_conf[handle_entry]['handle']
        pubtxid = dil_conf[handle_entry]['txid']

    params = []
    balance = rpc_connection.getbalance()
    print('Current balance: ' + str(balance))
    send_amount = selectRangeFloat(0,balance, 'Please specify the amount to deposit: ')
    params.append(handle)
    params.append(pubtxid)
    params.append(send_amount)
    result = dil_wrap('send', params, rpc_connection)
    # FIXME log all sends to dil.log 
    if 'error' in result:
        return('Error: dilthium send broadcast failed with ' + str(result['error']))
    rawhex = result['hex']
    txid = rpc_connection.sendrawtransaction(rawhex)
    return('Success! Sent ' + str(send_amount) + ' to ' + handle + '(' + pubtxid + ')' +
           '\ntxid: ' + txid)


# cclib Qsend 19 \"[%22mypubtxid%22,%22<hexseed>%22,%22<destpubtxid>%22,0.777,%22<destpubtxid>%22,0.777,%22<destpubtxid>%22,0.777,%22<destpubtxid>%22,0.777]\"
# {'evalcode': 19, 'funcid': 'Q', 'name': 'dilithium', 'method': 'Qsend', 'help': "mypubtxid hexseed/'mypriv' destpubtxid,amount, ...", 'params_required': 4, 'params_max': 66}
def dil_Qsendmany(chain, rpc_connection):
    try:
        with open('dil.conf') as f:
            dil_conf = json.load(f)
    except Exception as e:
        return('Error: failed with: ' + str(e) + ' Please use the register command if you haven\'t already')

    handle_entry = handle_select("Select handle to send coins from: ", rpc_connection, 1) 
    output_length = user_inputInt(0,63, 'Please specify amount of outputs[0-63]: ')
    outputs = []
    for i in range(output_length):
        dum_dict = {}
        user_output = input('Please specify a dilithium handle or R address for output ' + str(i) + ': ')
        user_amount = input('Please specify amount to send to ' + user_output + ': ')
        try:
            user_output_check = addr_convert('3c', user_output)
            if user_output_check != user_output:
                return('Error: Wrong address prefix format, must use R address')
            destination = rpc_connection.validateaddress(user_output)['scriptPubKey']
        except Exception as y:
            try:
                destination = dil_wrap('handleinfo', user_output, rpc_connection)['destpubtxid']
            except Exception as e:
                return('Error: Handle not found or invalid R address ' + user_output)
                
        dum_dict['dest'] = destination
        dum_dict['amount'] = user_amount
        outputs.append(dum_dict)
    wrapped = '\"[\"' + dil_conf[handle_entry]['txid'] + '\",\"' + dil_conf[handle_entry]['seed'] + '\",\"'
    for i in outputs[:-1]:
        wrapped = wrapped + i['dest'] + '\",\"' + i['amount'] + '\",\"'
    wrapped = wrapped + outputs[-1]['dest'] + '\",\"' + outputs[-1]['amount'] + '\"]\"'
    Qsend_result = rpc_connection.cclib('Qsend', '19', wrapped)
    try:
        rawhex = Qsend_result['hex']
    except Exception as e:
        return('Error: Qsend method failed with error: ' + str(Qsend_result['error']))
    # FIXME this should ask user to confirm amounts before sending
    try:
        decoderawtx_result = rpc_connection.decoderawtransaction(rawhex)
    except Exception as e:
        return('Error: Qsend method returned hex, but decode failed. Please report this to Alright. ' + str(e))

    txid = rpc_connection.sendrawtransaction(rawhex)
    return('Success! txid: ' + txid)


# cclib Qsend 19 \"[%22mypubtxid%22,%22<hexseed>%22,%22<destpubtxid>%22,0.777]\"
# {'evalcode': 19, 'funcid': 'Q', 'name': 'dilithium', 'method': 'Qsend', 'help': "mypubtxid hexseed/'mypriv' destpubtxid,amount, ...", 'params_required': 4, 'params_max': 66}
def dil_Qsend(chain, rpc_connection):
    try:
        with open('dil.conf') as f:
            dil_conf = json.load(f)
    except Exception as e:
        return('Error: failed with: ' + str(e) + ' Please use the register command if you haven\'t already')

    params = []

    # FIXME add a warning here if normal_pubkey is not own by current wallet
    handle_entry = handle_select("Select handle to send coins from: ", rpc_connection, 1) 
    user_output = input('Please input a handle or R address to send coins to: ')
    try:
        user_output_check = addr_convert('3c', user_output)
        if user_output_check != user_output:
            return('Error: Wrong address prefix format, must use R address')
        destination = rpc_connection.validateaddress(user_output)['scriptPubKey']
    except Exception as y:
        try:
            destination = dil_wrap('handleinfo', user_output, rpc_connection)['destpubtxid']
        except Exception as e:
            return('Error: Handle not found or invalid R address ' + user_output)
    send_amount = input('Please specify amount to send: ')
    params.append(dil_conf[handle_entry]['txid'])
    params.append(dil_conf[handle_entry]['seed'])
    params.append(destination)
    params.append(send_amount)
    result = dil_wrap('Qsend', params, rpc_connection) # FIXME this is failing if you do it without waiting for confs
    try:
        if result['result'] != 'success':
            return('Error: Qsend failed with: ' + result['error'])
    except Exception as e:
        return('Error: Qsend rpc rpc command fail with: ' + str(e) + ' ' + str(result))
    try:
        rawtx = result['hex']
    except Exception as e:
        return('Error: Qsend rpc command failed with: ' + str(e))
    try:
        result_txid = rpc_connection.sendrawtransaction(rawtx)
    except Exception as e:
        return('Error: Qsend broadcast failed with: ' + str(e) + '\n' + rawtx)
    return('Success! ' + result_txid)


# function to get handle from register txid
def handle_get(register_txid, rpc_connection):
    tx = rpc_connection.getrawtransaction(register_txid, 1)
    OP_ret = tx['vout'][-1]['scriptPubKey']['hex']
    byte_length = OP_ret[12:14]
    byte_length_int = int(byte_length, 16)
    x = (byte_length_int * 2) + 14
    return(bytes.fromhex(OP_ret[14:x]).decode('utf-8'))


# endian flip a string
def endian_flip(string):
    ba = bytearray.fromhex(string)
    ba.reverse()
    flipped = ''.join(format(x, '02x') for x in ba)
    return(flipped)


def dil_balance(rpc_connection):
    listunspent_result = dil_listunspent(rpc_connection, 1)
    balance_dict = {}
    for handle in listunspent_result:
        for utxo in listunspent_result[handle]:
            try:
                balance_dict[handle] += utxo['value'] * 100000000
            except:
                balance_dict[handle] = utxo['value'] * 100000000
    for i in balance_dict:
        balance_dict[i] = balance_dict[i] / 100000000

    return(balance_dict)

# get balance of arbitrary dilithium handle
def dil_external_balance(rpc_connection):
    handle = input('Please specify a handle: ')
    result = dil_listunspent(rpc_connection, handle)
    balance_sat = 0
    if str(result).startswith('Error'):
        return(result)
    for utxo in result[handle]:
        balance_sat += utxo['value'] * 100000000
    return(str(balance_sat / 100000000))


# output string's positions in a list given the list and string
def list_pos(input_list, input_string):
    count = 0 
    positions = []
    for i in input_list:
        if input_list[count] == input_string:
            positions.append(count)
        count += 1
    return(positions)


# function to list dilithium handles asscoiated with an arbitary pubkey
def dil_pubkey_handles(rpc_connection):
    pubkey = input('Please specify a pubkey: ')
    try:
        pubkey_check = P2PKHBitcoinAddress.from_pubkey(x(pubkey))
    except Exception as e:
        return('Error: ' + str(e))

    cclibaddress_result = rpc_connection.cclibaddress('19', pubkey)
    CC_address = cclibaddress_result['PubkeyCCaddress(CClib)']
    address_dict = {}
    address_dict['addresses'] = [CC_address]
    handle_list = []
    CC_txids = rpc_connection.getaddresstxids(address_dict)
    for txid in CC_txids:
        tx = rpc_connection.getrawtransaction(txid, 2)
        try:
            OP_ret = tx['vout'][-1]['scriptPubKey']['hex']
        except:
            break
        decode_result = rpc_connection.decodeccopret(OP_ret)
        try:
            if decode_result['OpRets'][0]['function'] == 'R':
                handle_list.append(handle_get(txid, rpc_connection))
        except:
            break
    return(handle_list)


def my_stakes(rpc_connection):
    days = input('Please specify amount of days(1 day = 1440 blocks): ')
    try:
        days = int(days)
    except:
        return('Error: days must be integer')
    if days <= 0:
        return('Error: days must be positive')
    address = input('Please specify address(press enter to use current -pubkey address): ')
    if address == '':
        try:
            address = rpc_connection.setpubkey()['address']
        except Exception as e:
            return('Error: -pubkey not set ' + str(e))
    try:
        address_check = addr_convert('3c', address)
        if address_check != address:
            return('Error: Invalid address must be R address')
    except Exception as e:
        return('Error: Invalid address ' + str(e))
    address_dict = {}
    address_dict['addresses'] = [address]

    txids = rpc_connection.getaddresstxids(address_dict)
    height = int(rpc_connection.getinfo()['blocks'])
    count = 1
    counts = []
    txs = []
    total = 0

    print('Please wait...')
    for txid in txids:
        tx = rpc_connection.getrawtransaction(txid, 2)
        try:
            dum = tx['vin'][0]['coinbase']
            txs.append(tx)
        except:
            continue

    for i in range(1,int(days)):
        upper = 1440*i
        lower = 1440*(i-1)
        for tx in txs:
            if height - lower >= tx['height'] >= height - upper:
                count += 1
                total += tx['vout'][0]['valueSat']
        counts.append(count)
        print('day' + str(i) + ' count:' + str(count) + ' range: ' + str(height-lower) + '-' + str(height-upper))
        count = 0

    print('Average:', sum(counts) / (len(counts)))
    print('Total:', total / 100000000)
    input('Press enter to return to menu')
    return('')


# determine average amount of coins used to stake for N blocks
def average_stake(rpc):
    block_count = input('Please specify amount of previous blocks: ')
    try:
        block_count = int(block_count)
    except:
        return('Error: blocks must be integer')
    if block_count <= 0:
        return('Error: blocks must be positive')
    print('Please wait...')

    height = int(rpc.getinfo()['blocks'])

    if block_count > height:
        block_count = height

    start_height = height - block_count
    staked_count = 0
    total = 0
    for i in range(start_height, height+1):
        block = rpc.getblock(str(i), 2)
        if block['segid'] != -1:
            staked_count += 1
            total += block['tx'][-1]['vout'][0]['valueZat']
    total_coin = total/100000000
    average = total_coin / staked_count
    print('\nAmount of staked blocks in range ' + str(start_height) + '-' + str(height) + ': ' + str(staked_count))
    print('Average amount to stake a block: ' + str(average))
    input('\n[press enter to return to menu]')
    return('')


def top_stakers(rpc_connection, to_from):
    try:
        block_count = int(input('Please specify amount of previous blocks: '))
    except:
        return('Error: blocks must be integer')
    if block_count <= 0:
        return('Error: blocks must be positive')

    height = int(rpc_connection.getinfo()['blocks'])

    if block_count > height:
        block_count = height

    yn = input('Include addresses with a single stake?(y/n): ')
    if yn.startswith('y'):
        yn = 'y'
    else:
        yn = 'n'

    print('Please wait...\n')
    staked_blocks = []
    staked_from = {}
    mined_to = {}
    for i in range(height-block_count,height):
        block = rpc_connection.getblock(str(i), 2)
        if block['segid'] != -1:
             staked_blocks.append(block)
    for block in staked_blocks:
        staked_from_address = block['tx'][-1]['vout'][-1]['scriptPubKey']['addresses'][0]
        mined_to_address = block['tx'][0]['vout'][0]['scriptPubKey']['addresses'][0]
        if not staked_from_address in staked_from:
             staked_from[staked_from_address] = 1
        else:
             staked_from[staked_from_address] += 1
        if not mined_to_address in mined_to:
             mined_to[mined_to_address] = 1
        else:
             mined_to[mined_to_address] += 1
    if to_from:
        select = mined_to
    else:
        select = staked_from
    s = [(k, select[k]) for k in sorted(select, key=select.get, reverse=True)]
    for k, v in s:
        if yn == 'y':
            print(k, v)
        else:
            if v != 1:
                print(k, v)
    input('\n[press enter to return to menu]')
    return('')


def my_utxo_average(rpc):
    listunspent = rpc.listunspent()
    total = 0
    for i in listunspent:
        total += int(i['amount']*100000000+0.000000004999)
    total = total / 100000000
    average = total/len(listunspent)
    print('\nTotal: ' + str(total))
    print('Amount of UTXOs: ' + str(len(listunspent)))
    print('Average: ' + str(average))
    input('\n[press enter to return to menu]')
    return('')

# function to sum balance of each segid
def segid_balance(rpc_connection):
    print('Please wait...')
    result_dict = {}
    for i in range(64):
        result_dict[i] = 0
    snapshot = rpc_connection.getsnapshot()
    for address in snapshot['addresses']:
        result_dict[address['segid']] += float(address['amount']) * 100000000
    for i in result_dict:
         print(str(i) + ' ' + str(result_dict[i] / 100000000))
    input('\n[press enter to return to menu]')
    return('')

# find any address that has ever staked a block to specified address, sum balances
def estimate_stake_balance(rpc):
    address = input('Please specify address: ')
    if address == '':
        try:
            address = rpc.setpubkey()['address']
        except Exception as e:
            return('Error: -pubkey not set ' + str(e))
    try:
        address_check = addr_convert('3c', address)
        if address_check != address:
            return('Error: Invalid address must be R address')
    except Exception as e:
        return('Error: Invalid address ' + str(e))

    print('Please wait...\n')

    staked_from = [address]
    addresstxids = rpc.getaddresstxids({"addresses": [address]})
    total_staked = 0
    staked_block_count = 0

    for txid in addresstxids:
        tx = rpc.getrawtransaction(txid, 2)
        if 'coinbase' in tx['vin'][0]:
            try:
                block = rpc.getblock(str(tx['height']), 2)
            except Exception as e:
                print(e)
                continue
            if block['segid'] == -1:
                continue
            staked_block_count += 1
            total_staked += tx['vout'][0]['valueSat']
            staked_address = block['tx'][-1]['vout'][0]['scriptPubKey']['addresses'][0]
            if not staked_address in staked_from:
                staked_from.append(staked_address)

    utxos = rpc.getaddressutxos({"addresses": staked_from})
    total = 0
    total = rpc.getaddressbalance({"addresses": staked_from})['balance']

    total = total/100000000

    print('Total addresses: ' + str(len(staked_from)))
    print('Total staked blocks: ' + str(staked_block_count))
    print('Total staked amount: ' + str(total_staked/100000000))
    print('Total estimated balance: ' + str(total))
    print('Total UTXOs: ' + str(len(utxos)))
    print('Average UTXO size: ' + str(total/len(utxos)))
    input('\n[press enter to return to menu]')
    return('')
