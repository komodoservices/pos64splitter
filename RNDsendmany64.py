#!/usr/bin/env python3
import random 
import sys
import json
from staker import def_credentials
from sendmany64 import sendmanyloop, sendmany64, unlockunspent


CHAIN = input('Please specify chain: ')
try:
    rpc_connection = def_credentials(CHAIN)
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

sendmanyloop_result = sendmanyloop(AMOUNTS)
# unlock all locked utxos
unlockunspent(rpc_connection)
for i in sendmanyloop_result:
    print(i)
print('Success!')
