#!/usr/bin/env bash

if [ "$EUID" -ne 0 ]
  then echo "Please run with sudo"
  exit 1
fi

#application files
mkdir -p /usr/local/etc/digital-ocean
touch /usr/local/etc/digital-ocean/.env
cp digital-ocean-dns-updater.py /usr/local/etc/digital-ocean/
chown -R $SUDO_USER:$SUDO_USER /usr/local/etc/digital-ocean

#log files
mkdir /var/log/digital-ocean
chown -R $SUDO_USER:$SUDO_USER /var/log/digital-ocean

echo "API_KEY=$DIGITAL_OCEAN_API_KEY" > /usr/local/etc/digital-ocean/.env

has_ipv6=$(curl -sL -w "%{http_code}" "https://ipv6.icanhazip.com" -o /dev/null --connect-timeout 3 --max-time 5)
if [ -f /proc/net/if_inet6 ] && [ "$has_ipv6" == "200" ]; then
    echo "IPV6=true" >> /usr/local/etc/digital-ocean/.env
else 
    echo "IPV6=false" >> /usr/local/etc/digital-ocean/.env
fi

sed "s/USER/$SUDO_USER/g" digital-ocean-dns-updater.service > /etc/systemd/system/digital-ocean-dns-updater.service
cp digital-ocean-dns-updater.timer /etc/systemd/system/
systemctl daemon-reload
systemctl start digital-ocean-dns-updater.timer
systemctl enable digital-ocean-dns-updater.timer
