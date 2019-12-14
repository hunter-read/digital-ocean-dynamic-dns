# Digital Ocean Dynamic DNS updater

This repository provides a hassel free way to set up a dynamic dns service to update all 'A' records for domains handled by digital ocean.
This python program will update all domains associated to the given account to the current external ip address of the device running the service every 15 minutes, but will not create any new ones. This enables a set and forget setup for those who want an easy way to have dynamic dns on their domain

Requirements:
* Python 3.6
* requests Library for python3
* python-dotenv Library for python3

Python3 requirements can be install with `pip3 install -r requirements.txt`

Python script and systemd services can be installed with `sudo ./install`, all you need is your api key (which is store locally on your device only)

Python logs can be found in /var/log/digital-ocean/digital-ocean-dns-updater.log
