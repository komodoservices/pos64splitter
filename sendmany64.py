#!/usr/bin/env python3
import sys
import json
import stakerlib

CHAIN = input('Please specify chain: ')
try:
    rpc_connection = stakerlib.def_credentials(CHAIN)
except Exception as e:
    sys.exit(e)
balance = float(rpc_connection.getbalance())
print('Balance: ' + str(balance))

AMOUNT = input("Please specify the size of UTXOs: ")
if int(AMOUNT) < 1:
    sys.exit('Cant stake coin amounts less than 1 coin, try again.')
UTXOS = input("Please specify the amount of UTXOs to send to each segid: ")
total = float(AMOUNT) * int(UTXOS) * 64
print('Total amount: ' + str(total))
if total > balance:
    print('Total sending is ' + str(total-balance) + ' more than your balance. Try again.')
    segidTotal = balance / 64
    sys.exit('Total avalible per segid is: ' + str(segidTotal))

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def sendmanyloop(rpc_connection, amount, utxos):
    txid_list = []
    for i in range(int(utxos)):
        sendmany64_txid = stakerlib.sendmany64(rpc_connection, amount)
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
stakerlib.unlockunspent(rpc_connection)
for i in sendmanyloop_result:
    print(i)
print('Success!')
