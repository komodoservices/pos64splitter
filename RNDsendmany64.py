#!/usr/bin/env python3
import json
import kmdrpc
import sys
import random 

CHAIN = input('Please specify chain: ')
balance = float(kmdrpc.getbalance_rpc(CHAIN))
print('Balance: ' + str(balance))

while True:
    UTXOS = int(input("Please specify the amount of UTXOs to send to each segid: "))
    TUTXOS = UTXOS * 64
    print('Total number of UTXOs: ' + str(TUTXOS))
    average = float(balance) / int(TUTXOS)
    print('Average utxo size: ' + str(average))
    variance = float(input('Enter percentage of variance: '))
    minsize = round(float(average) * (1-(variance/100)),2)
    if minsize < 1:
        print('Cant stake coin amounts less than 1 coin, try again.')
        break
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
        if totalamnt > balance:
            totalamnt = 0
            AMOUNTS.clear()
            break
    if totalamnt > balance*0.9999:
        finished = True

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
def sendmanyloop(chain, amounts, utxos):
    txid_list = []
    for amount in amounts:
        sendmany64_txid = sendmany64(CHAIN, amount)
        txid_list.append(sendmany64_txid)
        getrawtx_result = kmdrpc.getrawtransaction_rpc(CHAIN, sendmany64_txid)
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
        lockunspent_result = kmdrpc.lockunspent_rpc(CHAIN, False, lockunspent_list)
    return(txid_list)

sendmanyloop_result = sendmanyloop(CHAIN, AMOUNTS, UTXOS)
# unlock all locked utxos
kmdrpc.unlockunspent(CHAIN)
for i in sendmanyloop_result:
    print(i)
print('Success!')
