# pos64splitter

A coin splitter for PoS assetchains.

PoS or PoW/PoS assetchains require coins to be staked across 64 segids.

If there is not at least 1 UTXO in each segid, the chain is more viable to a 51% attack.

Simply run `./split`, choose your balance, and this will split your coins for you!


## Dependencies
python3 and requests installed 
```shell 
sudo apt-get install python3
sudo apt-get install python3-pip
pip3 install requests
```

[komodod](https://github.com/jl777/komodo) installed with your assetchain running.

Coins imported into your wallet.


## How to Use

Clone the repo:

`git clone https://github.com/komodoservices/pos64splitter`

Enter the repo:

`cd pos64splitter`

Modify the `config.py` file to match the RPC settings in your assetchain .conf file. 

`nano config.py`

Conf files are located at: $home/user/.komodo/ASSETCHAIN.

Run the `./split` command.

That will generate 64 addresses, and then ask how many coins you'd like to split.

Enter your balance or # you want split.  And then your coins will be sent proportionately to each address.



## This tool uses work from [alrighttt/dockersegid](https://github.com/alrighttt/dockersegid) and we thank Alright very much.
