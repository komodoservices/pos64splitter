#!/usr/bin/env python3
import sys
import random
import json
from stakerlib import def_credentials, genvaldump

BESTBLOCKHASH =  sys.argv[1]
CHAIN = sys.argv[2]
TXFEE = 5000
#bitcoin.params = CoinParams
#BESTBLOCKHASH = kmdrpc.getbestblockhash_rpc(CHAIN)

    
# function to get first and last outputs from latest block
def latest_block_txs(chain, getblock_ret):
    # get txs in latest block
    getblock_txs = getblock_ret['tx']
    output_addresses = {}
    first_address = getblock_txs[0]['vout'][0]['scriptPubKey']['addresses'][0]
    last_address = getblock_txs[-1]['vout'][0]['scriptPubKey']['addresses'][0]
    output_addresses[first_address] = getblock_txs[0]['txid']
    output_addresses[last_address] = getblock_txs[-1]['txid']
    return(output_addresses)


# function to find address that staked
def staked_from_address(chain, getblock_ret):
    # get txs in latest block
    pep8fu = getblock_ret['tx'][-1]
    return(pep8fu['vout'][0]['scriptPubKey']['addresses'][0])


try:    
    rpc_connection = def_credentials(CHAIN)
except:
    sys.exit('Could not get connection to daemon. Exiting')

try:
    with open('list.json') as list:
        segid_addresses = json.load(list)
except:
    sys.exit('Could not load list.json please make sure it is in the directory where komodod is located. Exiting')

# Get pubkey being mined to.
try:
    pubkey = rpc_connection.getinfo()['pubkey']
except:
    sys.exit('PubKey not set. Exiting')

# Get the address of this pubkey.
try:
    setpubkey_result = rpc_connection.setpubkey(pubkey)
    address = setpubkey_result['address']
except:
    sys.exit('Could not get address. Exiting')
    
# Get the block and all transactions in it and save for later use.
try:
    getblock_result = rpc_connection.getblock(BESTBLOCKHASH, 2)
    coinbase_address = getblock_result['tx'][0]['vout'][0]['scriptPubKey']['addresses'][0]
except:
    sys.exit('Could not get block. Exiting')

# If the address of our pubkey matches the coinbase address we mined this block.
if coinbase_address == address:
    segid = getblock_result['segid']
    if segid == -2:
        sys.exit('SegId not set in block, this should not happen. Exiting.')
else:
    sys.exit('Not our block, exit.')
    
txid_list = []
tx_value = 0
createraw_list = []

if segid == -1:
    # This means we PoW mined the block
    tx_value = getblock_result['tx'][0]['vout'][0]['valueZat']
    input_dict = {
        "txid": getblock_result['tx'][0]['txid'],
        "vout": 0
    }
    createraw_list.append(input_dict)
    try:
        listunspent_result = rpc_connection.listunspent()
    except Exception as e:
        sys.exit(e)
    listunspent_result = sorted(listunspent_result,key=lambda x : (x['amount'], x['confirmations']))
    for unspent in listunspent_result:
        # Check the utxo is spendable and has been notarised at least once, to prevent problems with reorgs.
        if unspent['spendable'] and unspent['confirmations'] > 2:
            input_dict = {
                "txid": unspent['txid'],
                "vout": unspent['vout']
            }
            tx_value += unspent['amount'] * 100000000
            break
    createraw_list.append(input_dict)
    # check height so we dont count early chain or throw an error.
    if getblock_result['height'] > 1800:
        # find out what segids have staked the least in the last day and randomly choose one to send our funds too.
        try:
            getlastsegidstakes_result = rpc_connection.getlastsegidstakes(1440)['SegIds']
        except Exception as e:
            sys.exit(e)
        usable_segids = []
        for _segid, stakes in getlastsegidstakes_result.items():
            if stakes < 22:
                usable_segids.append(_segid)
        segid_to_use = int(usable_segids[random.randint(0,len(usable_segids))])
    else:
        segid_to_use = random.randint(0,63)
    staked_from = segid_addresses[segid_to_use][3]
else:
    # This means it was staked.
    block_txs = latest_block_txs(CHAIN, getblock_result)
    for address in block_txs:
        try:
            validateaddress_result = rpc_connection.validateaddress(address)
        except Exception as e:
            sys.exit(e)
        if validateaddress_result['ismine']:
            try:
                getrawtx_result = rpc_connection.getrawtransaction(block_txs[address],1)
            except Exception as e:
                sys.exit(e)
            txid_list.append(block_txs[address])
            tx_value += getrawtx_result['vout'][0]['valueSat']
            staked_from = staked_from_address(CHAIN, getblock_result)
        else:
            sys.exit('The address is not imported. Please check you imported list.json. Exiting.')
    for txid in txid_list:
        input_dict = {
            "txid": txid,
            "vout": 0
        }
        createraw_list.append(input_dict)

output_dict = {
        staked_from: ((tx_value - TXFEE) / 100000000)
    }

try:
    unsigned_hex = rpc_connection.createrawtransaction(createraw_list, output_dict)
except Exception as e:
    sys.exit(e)

try:
    signrawtx_result = rpc_connection.signrawtransaction(unsigned_hex)
except Exception as e:
    sys.exit(e)

signed_hex = signrawtx_result['hex']

try:
    sendrawtx_result = rpc_connection.sendrawtransaction(signed_hex)
except Exception as e:
    sys.exit(e)

sendrawtxid = sendrawtx_result

if segid != -1:
    print('Staked from segid ' + str(segid) + ' ' + sendrawtxid)
else:
    print('Mined block combined to ' + str(segid_to_use) + ' ' + sendrawtxid)
