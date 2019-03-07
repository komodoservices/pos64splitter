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
import readline # FIXME not supported on windows
from slickrpc import Proxy


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
        sendmany_result = rpc_connection.sendmany("", addresses_dict)
    except Exception as e:
        return('Error: sendmany command failed with ' + str(e))
    return('Success! ' + sendmany_result)

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

    # save output to list.py
    f = open(chain + ".json", "w+")
    f.write(json.dumps(segids_array))
    return('Success! ' + chain + '.json created. '
          'THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.')

# FIXME make this rescan only on 64th import
# import list.json to chain 
def import_list(chain, rpc_connection):
    user_input = input('Please specify a json file to import: ')
    if not os.path.isfile(user_input):
        return('Error: File not found. Make sure you use the full file name. ' +
               'You can use the genaddresses option to generate a new one.')

    # FIXME add check to see if it's actually json
    with open(user_input) as key_list:
        json_data = json.load(key_list)
        for i in json_data:
            print(i[3])
            rpc_connection.importprivkey(i[2])
    return('Success!')
    
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
        return('Error: ' + chain + ' not found in assetchains.json')# FIXME
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
           param_list.append('-' + i + '=' + params[i])
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
           param_list.append('-' + i + '=' + params[i])
    param_list.append(blocknotify)
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
                return('Error:file ' + member.name + ' has improper file permissions! Please report this to Alright2')
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

# cclib keypair 19 \"[%22rand%22]\"
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
    print(method, '19', wrapped)
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
                       'This will create a dilithium privkey that is ' +
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
    balances = dil_balance(rpc_connection)
    for i in dil_conf:
        if show_balance == 1: # FIXME this could definitely display balances in a better format
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


# function to decode dil send OP_RETURN, returns register txid
def decode_dil_send(txid, rpc_connection):
    tx = rpc_connection.getrawtransaction(txid, 1)
    scriptPubKey = tx['vout'][-1]['scriptPubKey']['hex']
    decode = rpc_connection.decodeccopret(scriptPubKey)
    ba = bytearray.fromhex(scriptPubKey)
    ba.reverse()
    decode = rpc_connection.decodeccopret(scriptPubKey)
    if decode['OpRets'][0]['eval_code'] == '0x13' and decode['OpRets'][0]['function'] == 'x': # FIXME add other eval codes
        register_txid = ''.join(format(x, '02x') for x in ba)[:64]
        return(register_txid)


def decode_dil_Qsend(txid, rpc_connection):
    CC_address = rpc_connection.cclibaddress('19')['myCCaddress']
    getrawtx_result = rpc_connection.getrawtransaction(txid, 2)
    scriptPubKey = getrawtx_result['vout'][-1]['scriptPubKey']['hex']
    op_return = endian_flip(scriptPubKey)
    decode_result = rpc_connection.decodeccopret(scriptPubKey)

    if decode_result['OpRets'][0]['eval_code'] == '0x13' and decode_result['OpRets'][0]['function'] == 'Q':
        for vout in getrawtx_result['vout']:
            try:
                #print('vfefewf',vout)
                if vout['scriptPubKey']['addresses'][0] == CC_address['myCCaddress']:
                    print(vout)
                    print(scriptPubkey)
            except Exception as e:
                print(e)
        #print(op_return)
        print('\nvout -2 dil change output',op_return[:64])
        print(getrawtx_result['vout'][-2])
        print('\nvout -3 payment to recipient', op_return[64:128])
        print(getrawtx_result['vout'][-3])
        print('register_txid input',op_return[-76:-12])
        print('txid',txid)
        

def dil_listunspent(chain, rpc_connection):
    try:
        with open('dil.conf') as f:
            dil_conf = json.load(f)
    except Exception as e:
        return('Error: verify failed with: ' + str(e) + ' Please use the register command if you haven\'t already')

    CC_address = rpc_connection.cclibaddress('19')
    address_dict = {}
    address_dict['addresses'] = [CC_address['myCCaddress']]
    CC_utxos = []
    CC_txids = rpc_connection.getaddressutxos(address_dict)
    for i in CC_txids:
        CC_utxos.append(i['txid'])
    register_txids = []
    txids = []
    result_dict = {}
    for i in dil_conf:
        result_dict[i] = []

    for CC_txid in CC_utxos:
        tx = rpc_connection.getrawtransaction(CC_txid, 1)
        for vout in tx['vout']:
            if vout['scriptPubKey']['type'] == 'nulldata':
                OP_hex = vout['scriptPubKey']['hex']
                decode = rpc_connection.decodeccopret(OP_hex)
                bigend_OP = endian_flip(OP_hex)
                if decode['OpRets'][0]['eval_code'] == '0x13' and decode['OpRets'][0]['function'] == 'x':
                    #print(tx['vout'][-1]['scriptPubKey']['hex'])
                    txids.append(CC_txid)
                    register_txid = decode_dil_send(CC_txid, rpc_connection)
                    register_txids.append(register_txid)
                    for handle in dil_conf:
                        if decode_dil_send(CC_txid, rpc_connection) == dil_conf[handle]['txid']:
                            txid_dict = {'txid': CC_txid, 'value': tx['vout'][0]['value'], 'vout': 0} #FIXME check if this send is always vout 0
                            result_dict[handle].append(txid_dict)

                if decode['OpRets'][0]['eval_code'] == '0x13' and decode['OpRets'][0]['function'] == 'Q':
                    for handle in dil_conf:
                        #print('vout -2',bigend_OP[:64])
                        #print(dil_conf[handle]['txid'])
                        #print('vout -3',bigend_OP[64:128])
                        if dil_conf[handle]['txid'] == bigend_OP[:64]:# FIXME can't hardcode these, need to think of a better solution for multi vout Qsends
                            tx['vout'][-2]['value']
                            txid_dict = {'txid': CC_txid, 'value': tx['vout'][-2]['value'], 'vout': 1}
                            result_dict[handle].append(txid_dict)
                        if dil_conf[handle]['txid'] == bigend_OP[64:128]:
                            tx['vout'][-3]['value']
                            txid_dict = {'txid': CC_txid, 'value': tx['vout'][-2]['value'], 'vout': 0}
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
            return('Error: failed with: ' + str(e) + ' Please use the register command if you haven\'t already')

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

# function to create a p2pkh scriptpubkey from arbitrary address
def createraw_dummy(address, rpc_connection):
    dummy_input = [{'txid': 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 'vout': 0}]
    output = {address: 0.01}
    createraw_result = rpc_connection.createrawtransaction(dummy_input, output)
    decoderaw_result = rpc_connection.decoderawtransaction(createraw_result)
    return(decoderaw_result['vout'][0]['scriptPubKey']['hex'])


# {'evalcode': 19, 'funcid': 'y', 'name': 'dilithium', 'method': 'spend', 'help': 'sendtxid scriptPubKey [hexseed]', 'params_required': 2, 'params_max': 3}
def dil_spend(chain, rpc_connection):
    try:
        with open('dil.conf') as f:
            dil_conf = json.load(f)
    except Exception as e:
        return('Error: verify failed with: ' + str(e) + ' Please use the register command if you haven\'t already')


    handle = handle_select('\nPlease select handle to send from: ', rpc_connection, 1)
    utxo_list = dil_listunspent(chain, rpc_connection)[handle]
    if not utxo_list:
        return('Error: can\'t find q utxo for selected handle. You must send t -> q first.')
    user_address = input('Please input an R address to send coins to: ')
    try:
        address_check = addr_convert('3c', user_address)
    except Exception as e:
        return('Error: invalid address ' + str(e))

    if address_check != user_address:
        return('Error: Wrong address format, must use an R address')
    count = 0 
    for i in utxo_list:
        print(str(count) + ' | ' + str(i))
        count += 1
    utxo = user_inputInt(0,len(utxo_list), '\nPlease select a q utxo to spend: ')
    params = []
    params.append(utxo_list[utxo]['txid'])
    params.append(createraw_dummy(user_address, rpc_connection))
    params.append(dil_conf[handle]['seed'])
    result = dil_wrap('spend', params, rpc_connection)
    try:
        rawhex = result['hex']
    except Exception as e:
        return('Error: dilthium spend rpc failed with: ' + str(e))
    try:
        txid = rpc_connection.sendrawtransaction(rawhex)
    except Exception as e:
        return('Error: broadcasting spend tx failed with: ' + str(e))
    return('Success! ' + txid)


# cclib Qsend 19 \"[%22mypubtxid%22,%22<hexseed>%22,%22<destpubtxid>%22,0.777]\"
# {'evalcode': 19, 'funcid': 'Q', 'name': 'dilithium', 'method': 'Qsend', 'help': "mypubtxid hexseed/'mypriv' destpubtxid,amount, ...", 'params_required': 4, 'params_max': 66}
def dil_Qsend(chain, rpc_connection):
    try:
        with open('dil.conf') as f:
            dil_conf = json.load(f)
    except Exception as e:
        return('Error: failed with: ' + str(e) + ' Please use the register command if you haven\'t already')
    params = []
    count = 0

    # FIXME add a warning here if normal_pubkey is not own by current wallet
    handle_entry = handle_select("Select handle to send coins from: ", rpc_connection, 1) 
    send_to_handle = input('Please input a handle to send coins to: ')
    
    handleinfo_result = dil_wrap('handleinfo', send_to_handle, rpc_connection)
    try:
        destpubtxid = handleinfo_result['destpubtxid']
    except Exception as e:
        return('Error: did not find handle ' + str(e))
    send_amount = input('Please specify amount to send: ')
    params.append(dil_conf[handle_entry]['txid'])
    params.append(dil_conf[handle_entry]['seed'])
    params.append(destpubtxid)
    params.append(send_amount)
    result = dil_wrap('Qsend', params, rpc_connection) # FIXME this is failing if you do it without waiting for confs
    if result['result'] != 'success':
        return('Error: Qsend failed with: ' + result['error'])
    try:
        rawtx = result['hex']
    except Exception as e:
        return('Error: Qsend rpc command failed with: ' + str(e))
    try:
        result_txid = rpc_connection.sendrawtransaction(rawtx)
    except Exception as e:
        return('Error: Qsend broadcast failed with: ' + str(e))
    return('Success! ' + result_txid)


# endian flip a string
def endian_flip(string):
    ba = bytearray.fromhex(string)
    ba.reverse()
    flipped = ''.join(format(x, '02x') for x in ba)
    return(flipped)


def dil_balance(rpc_connection):
    CC_address = rpc_connection.cclibaddress('19')
    address_dict = {}
    address_dict['addresses'] = [CC_address['myCCaddress']]

    CC_utxos = []
    CC_txid_info = rpc_connection.getaddressutxos(address_dict)
    for i in CC_txid_info:
        CC_utxos.append(i['txid'])

    balances = {}
    register_txids = []

    for CC_txid in CC_utxos:
        tx = rpc_connection.getrawtransaction(CC_txid, 1)
        for vout in tx['vout']:
            if vout['scriptPubKey']['type'] == 'nulldata':
                OP_hex = vout['scriptPubKey']['hex']
                decode = rpc_connection.decodeccopret(OP_hex)
                if decode['OpRets'][0]['eval_code'] == '0x13' and decode['OpRets'][0]['function'] == 'x': # FIXME add other eval codes
                    #print(tx['vout'][-1]['scriptPubKey']['hex'])
                    lilend = tx['vout'][-1]['scriptPubKey']['hex']
                    register_txid = endian_flip(lilend)[:64]
                    register_txids.append(register_txid)
                    if register_txid in balances:
                        balances[register_txid] += tx['vout'][0]['valueSat']
                    else:
                        balances[register_txid] = tx['vout'][0]['valueSat']
                elif decode['OpRets'][0]['eval_code'] == '0x13' and decode['OpRets'][0]['function'] == 'Q':
                    #print(tx['vout'][-1]['scriptPubKey']['hex'])
                    OP_ret = tx['vout'][-1]['scriptPubKey']['hex']
                    for tx_vout in tx['vout']:
                        try:
                            if tx_vout['scriptPubKey']['addresses'] in addresses_dict:
                                print(tx_vout['scriptPubKey']['addresses'][0])
                        except Exception as e:
                            pass

                    
                   
                    

    try:
        with open('dil.conf') as file:
            dil_conf = json.load(file)
    except Exception as e:
        return(balances) # FIXME divide by COIN

    final_balances = {}
    registered = {}

    # if handle is saved in dil_conf, show handle in place of register txid
    for handle in dil_conf:
        register_txid = dil_conf[handle]['txid']
        if dil_conf[handle]['txid'] in balances:
            registered[register_txid] = handle

    for txid in balances:
        if txid in registered:
            final_balances[registered[txid]] = balances[txid] / 100000000
        else:
            final_balances[txid] = balances[txid] / 100000000
    return(final_balances)

