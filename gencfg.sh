#!/bin/bash
if [ -z $1 ]; then
  echo ""
  echo "Please set the name of the chain."
  echo "eg. ./gencfg STAKED4"
  echo ""
  exit
fi

ac=$1
conf="~/.komodo/$ac/$ac.conf"
if [ ! -f "$conf" ]; then
  echo ""
  echo "Please sync the chain first before running this script!"
  echo ""
  exit
fi

thisconf=$(<~/.komodo/$ac/$ac.conf)
user=$(echo $thisconf | grep -Po "rpcuser=(\S*)" | sed 's/rpcuser=//')
pass=$(echo $thisconf | grep -Po "rpcpassword=(\S*)" | sed 's/rpcpassword=//')
port=$(echo $thisconf | grep -Po "rpcport=(\S*)" | sed 's/rpcport=//')

cfgfile="config.py"
echo "rpcuser = '"$user"'"
echo "rpcpassword = '"$pass"'"
echo "rpcport = '"$port"'"
echo "rpcip = '127.0.0.1'"

