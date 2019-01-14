import platform
import os
import re
import json
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
    return (output)

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
