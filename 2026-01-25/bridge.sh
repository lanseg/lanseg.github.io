#!/bin/bash
set -euo pipefail

IFNAME="enp1s0f0"
BRNAME="firebridge"
BRADDR="10.10.20.2"

if [[ "$1" == "up" ]]; then
    brctl addbr $BRNAME
    ip addr add 10.10.20.1/24 dev $BRNAME
    ip link set $BRNAME up
    iptables -t nat -A POSTROUTING -o $IFNAME -s 10.10.20.0/24 -j MASQUERADE
    iptables -t nat -A OUTPUT -m addrtype --src-type LOCAL --dst-type LOCAL -p tcp --dport 11434 -j DNAT --to-destination $BRADDR:11434
    iptables -t nat -A POSTROUTING -m addrtype --src-type LOCAL --dst-type UNICAST -p tcp -d $BRADDR --dport 11434 -j MASQUERADE
    sysctl -w net.ipv4.conf.all.route_localnet=1
elif [[ "$1" == "down" ]]; then
    iptables -t nat -D POSTROUTING -o $IFNAME -s 10.10.20.0/24 -j MASQUERADE
    iptables -t nat -D OUTPUT -m addrtype --src-type LOCAL --dst-type LOCAL -p tcp --dport 11434 -j DNAT --to-destination $BRADDR:11434 2>/dev/null
    iptables -t nat -D POSTROUTING -m addrtype --src-type LOCAL --dst-type UNICAST -p tcp -d $BRADDR --dport 11434 -j MASQUERADE 2>/dev/null
    sysctl -w net.ipv4.conf.all.route_localnet=0
    ip link set $BRNAME down
    brctl delbr $BRNAME
else
    echo "Usage: $0 {up|down}"
    exit 1
fi