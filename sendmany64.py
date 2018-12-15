#!/usr/bin/env python3
import json
import kmdrpc
import sys

CHAIN = input('Please specify chain:')
AMOUNT = input("Please specify the size of UTXOs:")
UTXOS = input("Please specify the amount of UTXOs to send to each segid:")

# iterate addresses list, construct dictionary,
# with amount as value for each address
def sendmany64(chain, amount):
    addresses_dict = {}
    with open('list.json') as key_list:
        json_data = json.load(key_list)
        for i in json_data:
            address = i[3]
            addresses_dict[address] = amount

    # make rpc call, issue transaction
    sendmany_result = kmdrpc.sendmany_rpc(chain, addresses_dict)
    return(sendmany_result)

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def sendmanyloop(chain, amount, utxos):
    txid_list = []
    for i in range(int(utxos)):
        sendmany64_txid = sendmany64(CHAIN, AMOUNT)
        txid_list.append(sendmany64_txid)
        getrawtx_result = kmdrpc.getrawtransaction_rpc(CHAIN, sendmany64_txid)
        lockunspent_list = []
        # find change output, lock all other outputs
        for vout in getrawtx_result['vout']:
            if vout['value'] != float(AMOUNT):
                change_output = vout['n']
            else:
                output_dict =	{
                    "txid": sendmany64_txid,
                    "vout": vout['n']
                    }
                lockunspent_list.append(output_dict)
        lockunspent_result = kmdrpc.lockunspent_rpc(CHAIN, False, lockunspent_list)
    
    return(txid_list)

sendmanyloop_result = sendmanyloop(CHAIN, AMOUNT, UTXOS)
#unlock all locked utxos
kmdrpc.unlockunspent(CHAIN)
for i in sendmanyloop_result:
   print(i)
print('Success!')
