#!/bin/sh
echo "nameserver 10.43.0.10" > /etc/resolv.conf
cd /opt
exec python3 net_routes.py
