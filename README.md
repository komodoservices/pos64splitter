# pos64splitter

An automated staker for PoS assetchains. Please see https://docs.komodoplatform.com/komodo/assetchain-params.html#ac-staked for details on pos64 POS implementation. 

This is a work in progress. We aim to make this easy to use and as "set and forget" as possible. Please feel free to contribute code and ideas. 

Currently, this will maintain a static number of UTXOs. This is important because a staking wallet can become very bloated over time. The block reward of any staked blocks will be combined with the UTXO used to stake the block.

## Dependencies

### Linux

```shell
sudo apt-get install python3 libgnutls28-dev libssl-dev
sudo apt-get install python3-pip
pip3 install setuptools 
pip3 install wheel
pip3 install base58 slick-bitcoinrpc python-bitcoinlib
```

Please see the [Installing Smart Chain Software From Source Code](https://developers.komodoplatform.com/basic-docs/smart-chains/smart-chain-setup/installing-from-source.html#linux) document or download [pre-compiled binaries](https://github.com/KomodoPlatform/komodo/releases/).

The komodod binary must be copied to `~/pos64staker/komodod` for features such as `Start a new chain`, `restart daemon with -blocknotify` and `start a chain from assetchains.json`. 

### OSX

Install Command Line Tools and homebrew:

```shell
xcode-select --install
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

Install the dependencies:

```shell
brew install python
brew install openssl
pip3 install base58 slick-bitcoinrpc python-bitcoinlib
```

Please see the [Installing Smart Chain Software From Source Code](https://developers.komodoplatform.com/basic-docs/smart-chains/smart-chain-setup/installing-from-source.html#macos) document or download [pre-compiled binaries](https://github.com/KomodoPlatform/komodo/releases/).

The komodod binary must be copied to `~/pos64staker/komodod` for features such as `Start a new chain`, `restart daemon with -blocknotify` and `start a chain from assetchains.json`. 

## How to Use

```shell
git clone https://github.com/KMDLabs/pos64staker
cd pos64staker
./TUIstaker.py
```

You will be prompted with the initial menu:

```shell
pos64staker by KMDLabs
===============

0 | Start a chain from assetchains.json
1 | Bootstrap a chain from dexstats.info
2 | <Add/remove chain>
q | Exit TUI
===============
```

`0 | Start a chain from assetchains.json`
This can be used if the chain is not already running and it is included in jl777's [assetchains.json](https://github.com/jl777/komodo/blob/beta/src/assetchains.json`) file. 

`1 | Bootstrap a chain from dexstats.info`
This will attempt to bootstrap the chain from dexstats.info. Please note that not all Smart Chain bootstraps are available on dexstats.info. 

`2 | <Add/remove chain>`
If the chain is already running, this can be used to add it to `staker.conf` file. 

After selecting one of these options, the menu will be updated to include the chain you selected. 

```shell
pos64staker by KMDLabs
===============
0 | LABS

1 | Start a chain from assetchains.json
2 | Bootstrap a chain from dexstats.info
3 | <Add/remove chain>
q | Exit TUI
===============
```

Now select the chain by inputting `0`(or the associated value if you have added multiple chains) and hitting enter. This will bring you to the main menu of pos64staker:

```shell
LABS
===============
0 | <return to previous menu>

1 | sendmany64
2 | RNDsendmany
3 | genaddresses
4 | importlist
5 | withdraw
6 | Start a new chain
7 | Restart daemon with -blocknotify
8 | unlock all locked utxos
9 | stats
10 | Dilithium

q | Exit TUI
===============
```

If this is your first time setting this up, you will want to do `genaddresses`, `RNDsendmany64` then `Restart daemon with -blocknotify`.


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

        select all segids under average stakes per segid in 24H

        randomly choose one to get segid we will send to.        

if segid >= 0 :

    fetch last transaction in block

    check if this tx belongs to the node

    if yes, use alrights code to combine this coinbase utxo with the utxo that staked it.
    
    
### Withdraw 

Withdraw script is for withdrawing funds from a staking node, without messing up utxo distribution. Works like this:

    Asks for percentage you want locked (kept). 
    
    It then counts how many utxo per segid. 
    
    Locks the largest and oldest utxos in each segid up to the % you asked.
    
    Gives balance of utxos remaning that are not locked.  These should be the smallest and newest utxo's in each segid. The least likely to stake.
    
    Then lets you send some coins to an address. 
    
    Unlocks utxos again.

