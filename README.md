# pos64splitter

An automated staker for PoS assetchains. Please see https://docs.komodoplatform.com/komodo/assetchain-params.html#ac-staked for details on pos64 POS implementation. 

This is a work in progress. We aim to make this easy to use and as "set and forget" as possible. Please feel free to contribute code and ideas. 

Currently, this will maintain a static number of UTXOs. This is important because a staking wallet can become very bloated over time. The block reward of any staked blocks will be combined with the UTXO used to stake the block.

## Dependencies
```shell
sudo apt-get install python3 libgnutls28-dev libssl-dev
sudo apt-get install python3-pip
pip3 install base58 slick-bitcoinrpc
```

[komodod](https://github.com/StakedChain/komodo) installed with your assetchain running.

## How to Use

The following examples will use CFEK. Replace CFEK with the chain you are using.

`git clone https://github.com/StakedChain/pos64staker`

`cd pos64staker`

`./genaddresses`
```shell
Please specify chain:CFEK
```

This will create a `list.json` file in the current directory. **THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.**
Copy this file to the directory `komodod` is located. 

`cp list.json ~/komodo/src/list.json`

`./sendmany64.py`
```shell
Please specify chain:CFEK
Balance: 1000000.77
Please specify the size of UTXOs:10
Please specify the amount of UTXOs to send to each segid:10
```
Please take note of what this is actually asking for. The above example will send 6400 coins total. It will send 100 coins in 10 UTXOs to each of the 64 segids. Will throw error if your entered amounts are more than your balance. Will tell you how much avalible you have for each segid.

You now need to start the daemon with -blocknotify and -pubkey set.

Fetch a pubkey from your `list.json` and place it in your start command. For example:

`./komodod -ac_name=CFEK -ac_supply=1000000 -ac_reward=10000000000 -ac_cc=2 -ac_staked=50 -addnode=195.201.20.230 -addnode=195.201.137.5  -pubkey=0367e6b61a60f9fe6748c27f40d0afe1681ec2cc125be51d47dad35955fab3ba3b '-blocknotify=/home/<USER>/pos64staker/staker.py %s CFEK'`

NOTE the CFEK in -blocknotify make sure you change this to the correct chain name you are using also note the single quotes.

After the daemon has started and is synced simply do `komodo-cli -ac_name=CFEK setgenerate true 0` to begin staking. 


### How the staker.py works

on block arrival:

getinfo for -pubkey 

setpubkey for R address 

check coinbase -> R address 

if yes check segid of block.

if -1 send PoW mined coinbase to :

        listunspent call ... 

        sort by amount -> smallest at top and then by confirms -> lowest to top. (we want large and old utxos to maximise staking rewards.)

        select the top txid/vout

        add this txid to txid_list

        get last segid stakes 1440 blocks (last24H)

        select all segids under 22 stakes (average stakes per segid in 24H)

        randomly choose one to get segid we will send to.        

if segid >= 0 :

    fetch last transaction in block

    check if this tx belongs to the node

    if yes, use alrights code to combine this coinbase utxo with the utxo that staked it.
    
    
### Withdraw 

Get chain name 

show balance 

ask how much needing to send 

Get address to send to

get listunspent call sort to least confirms at top. iterate down this list until have enough balance

--> Add segid to listunspent? (make sure we dont take too many from one segid?)

Second method:

put utxos into object sorted by segid .. like this:
    listunspent, sort by confirms.
    iterate down listunspent 
    put each utxo into list of segids utxos['segid'].append(utxo)
    should return object with each segid's utxos sorted by confirms.
    sort each segid by amount


get percentage of balance from user
