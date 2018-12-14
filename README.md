# pos64splitter

An automated staker for PoS assetchains. Please see https://docs.komodoplatform.com/komodo/assetchain-params.html#ac-staked for details on pos64 POS implementation. 

PoS or PoW/PoS assetchains require coins to be staked across 64 segids.

If there is not at least 1 UTXO in each segid, the chain is less secure.

## Dependencies
```shell
sudo apt-get install python3
sudo apt-get install python3-pip
pip3 install requests python-bitcoinlib hashlib base58
```

[komodod](https://github.com/StakedChain/komodo) installed with your assetchain running.

Coins imported into your wallet.


## How to Use

The following examples will use CFEK. Replace CFEK with the chain you are using.

`git clone https://github.com/StakedChain/pos64staker`

`cd pos64staker`

`./genaddresses`
```shell
Please specify chain:CFEK
```
This will create a `list.json` file in the current directory. [b]THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.[/b]
Move this file to the directory `komodod` is located. 
```shell
mv list.json ~/komodo/src`
```

`./sendmany64.py`
```shell
Please specify chain:CFEK
Please specify the size of UTXOs:10
Please specify the amount of UTXOs to send to each segid:10
```
Please take note of what this is actually asking for. The above example will send 6400 coins total. It will send 100 coins in 10 UTXOs to each of the 64 segids.



