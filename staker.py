#!/usr/bin/env python3
import kmdrpc
import os.path
import sys
from conf import CoinParams
import bitcoin
from bitcoin.wallet import P2PKHBitcoinAddress
from bitcoin.core import x


CHAIN = 'MGNX'
#BESTBLOCKHASH =  sys.argv[1]
TXFEE = 0.00005
bitcoin.params = CoinParams
BESTBLOCKHASH =  kmdrpc.getbestblockhash_rpc(CHAIN)

# function to get addresses:txs for outputs from latest block
def latest_block_txs(chain, blockhash):
    # get txs in latest block
    getblock_result = kmdrpc.getblock_rpc(chain, blockhash, 2)
    getblock_txs = getblock_result['tx']
    output_addresses = {}

    # get outputs of latest block
    for tx in getblock_txs:
        output_addresses[tx['vout'][0]['scriptPubKey']['addresses'][0]] = tx['txid']
    return(output_addresses)

# function to find address that staked
def staked_from_address(chain, blockhash):
   # get txs in latest block
    getblock_result = kmdrpc.getblock_rpc(chain, blockhash, 2)
    return(getblock_result['tx'][-1]['vout'][0]['scriptPubKey']['addresses'][0])

# function to determine if we mined latest block
def didwemine(chain, blockhash):
    getblock_result = kmdrpc.getblock_rpc(chain, blockhash, 2)
    for i in getblock_result['tx']:
       if 'coinbase' in i['vin'][0]:
           coinbase_address = i['vout'][0]['scriptPubKey']['addresses'][0]
    ismine = kmdrpc.validateaddress_rpc(chain, coinbase_address)
    return(ismine['ismine'])

txid_list = []

# function to combine coinbase and UTXO used to stake it
if didwemine(CHAIN, BESTBLOCKHASH):
    tx_value = 0
    block_txs = latest_block_txs(CHAIN, BESTBLOCKHASH)
    for address in block_txs:
        validateaddress_result = kmdrpc.validateaddress_rpc(CHAIN, address)
        if validateaddress_result['ismine']:
             getrawtx_result = kmdrpc.getrawtransaction_rpc(CHAIN, block_txs[address])
             txid_list.append(block_txs[address])
             tx_value += getrawtx_result['vout'][0]['value']
    #print(block_txs)
else:
    #logger.info('did not mine latest block, exiting')
    #logging.info('did not mine latest block, exiting')
    print('did not mine latest block, exiting')
    sys.exit(0)

#print(tx_value)
#print(txid_list)

# take list of txids and format them for createrawtransaction
createraw_list = []

staked_from = staked_from_address(CHAIN, BESTBLOCKHASH)

for txid in txid_list:
    input_dict =	{
        "txid": txid,
        "vout": 0
    }
    createraw_list.append(input_dict)

output_dict = {
        staked_from: (tx_value - TXFEE)
    }

unsigned_hex = kmdrpc.createrawtransaction_rpc(CHAIN, createraw_list, output_dict)
signrawtx_result = kmdrpc.signrawtransaction_rpc(CHAIN, unsigned_hex)
signed_hex = signrawtx_result['hex']
sendrawtx_result = kmdrpc.sendrawtx_rpc(CHAIN, signed_hex)
sendrawtxid = sendrawtx_result
validateaddress_result = kmdrpc.validateaddress_rpc(CHAIN, staked_from)
print('Staked from segid' + str(validateaddress_result['segid']) + ' ' + sendrawtxid)

