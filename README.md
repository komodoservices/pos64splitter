# pos64splitter
A coin splitter for PoS assetchains.


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

That will generate 64 addresses, then send your coins proportionately to each address.



## This tool uses work from [alrighttt/dockersegid](https://github.com/alrighttt/dockersegid) and we thank Alright very much.