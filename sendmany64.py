#!/usr/bin/env python3
import sys
import json
from stakerlib import def_credentials

    
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
        sendmany64_txid = sendmany64(rpc_connection, AMOUNT)
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


sendmanyloop_result = sendmanyloop(rpc_connection, AMOUNT, UTXOS)
# unlock all locked utxos
unlockunspent(rpc_connection)
for i in sendmanyloop_result:
    print(i)
print('Success!')
