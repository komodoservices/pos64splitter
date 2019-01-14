#!/usr/bin/env python3
import random 
import sys
import json
import stakerlib 

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def RNDsendmanyloop(amounts):
    txid_list = []
    for amount in amounts:
        sendmany64_txid = stakerlib.sendmany64(amount)
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

CHAIN = input('Please specify chain: ')
try:
    rpc_connection = stakerlib.def_credentials(CHAIN)
except Exception as e:
    sys.exit(e)

try:
    balance = float(rpc_connection.getbalance())
except Exception as e:
    sys.exit(e)

print('Balance: ' + str(balance))

while True:
    UTXOS = int(input("Please specify the amount of UTXOs to send to each segid: "))
    if UTXOS < 3:
        print('Must have more than 3 utxos per segid, try again.')
        continue
    TUTXOS = UTXOS * 64
    print('Total number of UTXOs: ' + str(TUTXOS))
    average = float(balance) / int(TUTXOS)
    print('Average utxo size: ' + str(average))
    variance = float(input('Enter percentage of variance: '))
    minsize = round(float(average) * (1-(variance/100)),2)
    if minsize < 1:
        print('Cant stake coin amounts less than 1 coin, try again.')
        continue
    maxsize = round(average + float(average) * (variance/100),2)
    print('Min size: ' + str(minsize))
    print('Max size: ' + str(maxsize))
    ret = input('Are you happy with these? ').lower()
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

sendmanyloop_result = RNDsendmanyloop(AMOUNTS)
# unlock all locked utxos
stakerlib.unlockunspent(rpc_connection)
for i in sendmanyloop_result:
    print(i)
print('Success!')
