# pos64splitter

An automated staker for PoS assetchains. Please see https://docs.komodoplatform.com/komodo/assetchain-params.html#ac-staked for details on pos64 POS implementation. 

This is a work in progress. We aim to make this easy to use and as "set and forget" as possible. Please feel free to contribute code and ideas. 

Currently, this will maintain a static number of UTXOs. This is important because a staking wallet can become very bloated over time. The block reward of any staked blocks will be combined with the UTXO used to stake the block.

## Dependencies
```shell
sudo apt-get install python3
sudo apt-get install python3-pip
pip3 install requests python-bitcoinlib hashlib base58
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
Please specify the size of UTXOs:10
Please specify the amount of UTXOs to send to each segid:10
```
Please take note of what this is actually asking for. The above example will send 6400 coins total. It will send 100 coins in 10 UTXOs to each of the 64 segids.

You now need to start the daemon with -blocknotify and -pubkey set. For example:

`./komodod -ac_name=CFEK -ac_supply=1000000 -ac_reward=10000000000 -ac_cc=2 -ac_staked=50 -addnode=195.201.20.230 -addnode=195.201.137.5 -blocknotify=/home/<USER>/pos64staker/staker.py -pubkey=0367e6b61a60f9fe6748c27f40d0afe1681ec2cc125be51d47dad35955fab3ba3b`

You can use the `validateaddress` command in komodo-cli to get the pubkey of an address you own. Be sure that this address is imported to the daemon before you begin using the staker. 

After the daemon has started and is synced simply do `komodo-cli -ac_name=CFEK setgenerate true 0` to begin staking. 
