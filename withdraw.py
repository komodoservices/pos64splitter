#!/usr/bin/env python3
import sys
import stakerlib 
   
# function to unlock ALL lockunspent UTXOs
def unlockunspent():
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
    
def extract_segid(_segid,unspents):
    ret = []
    for unspent in unspents:
        if unspent['segid'] == _segid:
            unspent['amount'] = float(unspent['amount'])
            ret.append(unspent)
    return(ret)

CHAIN = input('Please specify chain: ')
try:
    rpc_connection = stakerlib.def_credentials(CHAIN)
except Exception as e:
    sys.exit(e)
balance = float(rpc_connection.getbalance())
print('Balance: ' + str(balance))

PERC = int(input("Please specify the percentage of balance to lock: "))
if PERC < 1:
    sys.exit('Cant lock 0%. Exiting.')

# get listunspent
try:        
    listunspent_result = rpc_connection.listunspent()
except Exception as e:
    sys.exit(e)

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
    sys.exit(e)
totalbalance = 0
for unspent in listunspent_result:
    totalbalance = float(totalbalance) + float(unspent['amount'])
    
print('Balance avalibe to send: ' + str(totalbalance))
address = input('Address? ')
if len(address) != 34:
    # can be improved, use validate address?
    unlockunspent()
    sys.exit('invalid address')
    
amount = float(input('Amount? '))
if amount < 0 or amount > totalbalance:
    unlockunspent()
    sys.exit('Too poor!')
    
print('Sending ' + str(amount) + ' to ' + address)
ret = input('Are you happy with these? ').lower()
if ret.startswith('n'):
    unlockunspent()
    sys.exit('You are not happy?')

# send coins.
txid_result = rpc_connection.sendtoaddress(address, amount)

# unlock all locked utxos
unlockunspent()
print('Success: ' + txid_result)
