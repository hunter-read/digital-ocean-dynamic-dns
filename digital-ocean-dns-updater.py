#!/usr/bin/env python3
'''
Digital Ocean API DNS updater in python3
'''

import os
import requests
import logging
import json
from requests.auth import AuthBase
from dotenv import load_dotenv

class ApiException(Exception):
    '''
    Api error handling
    '''
    def __init__(self, message):
        self.message = message
    pass

class BearerAuth(AuthBase):
    token=None
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["Authorization"] = f'Bearer {self.token}'
        return r


class DigitalOceanAPI(object):
    '''
    DigitalOcean object for making API requests
    '''
    api_key=None
    def __init__(self):
        '''
        Login to hover
        '''
        try:
            self.api_key = os.getenv('API_KEY')
        except NameError:
            raise ApiException("Name not found for API_KEY")
        if self.api_key is None or self.api_key=="":
            raise ApiException("API_KEY is not set")

    def call(self, method, resource, data=None):
        '''
        Make request to digital ocean api server
        '''
        url = f'https://api.digitalocean.com/v2/{resource}'
        json_data = json.dumps(data)
        try:
            r = requests.request(method, url, headers={'Content-Type': 'application/json'}, data=json_data, auth=BearerAuth(self.api_key))
            r.raise_for_status()
            if r.content:
                return r.json()
        except requests.exceptions.HTTPError as err:
            raise ApiException(err)


def update_record(client, domain_name, domain_record, current_ip):
    if domain_record.get("data") == current_ip:
        logging.debug(f'{domain_record.get("type")} record Ip is same for {domain_record.get("name")}.{domain_name}')
        return
    if domain_record.get("id") is None:
        logging.error(f'Id is null for domain {domain_name} and domain record {domain_record}')
        return

    logging.info(f'Updating {domain_record.get("type")} record IP for {domain_record.get("name")}.{domain_name} from {domain_record.get("data")} to {current_ip}')
    client.call("put", f'domains/{domain_name}/records/{domain_record.get("id")}', data={"data": current_ip})

def main():
    '''
    Main function for updating dns with digital API
    '''
    load_dotenv()
    #set log level from .env or to info
    log_level=logging.INFO
    level = os.getenv('LOG_LEVEL')
    if level is not None:
        log_level = getattr(logging, level, logging.INFO)

    ipv6_enabled=False
    if os.getenv('IPV6') is not None:
        ipv6_enabled=bool(os.getenv('IPV6'))

    logging.basicConfig(
        filename="/var/log/digital-ocean/digital-ocean-dns-updater.log",
        level=log_level,
        format="%(asctime)s:%(levelname)s:%(message)s"
        )

    #get current ip address
    try:
        ipv4_request = requests.post("https://ipv4.icanhazip.com")
        if not ipv4_request.ok:
            logging.error("Unable to retrieve IPv4 address")
            exit(1)
        current_ipv4 = ipv4_request.content.decode("utf-8").strip()
        logging.debug(f'Current IPv4 address is {current_ipv4}')
    except ConnectionError:
        logging.error("Unable to retrieve IPv4 address")
        exit(1)

    if ipv6_enabled:
        logging.debug("IPv6 is enabled")
        try:
            ipv6_request = requests.post("https://ipv6.icanhazip.com")
            if not ipv6_request.ok:
                logging.error("Unable to retrieve IPv6 address")
                exit(1)
            current_ipv6 = ipv6_request.content.decode("utf-8").strip()
            logging.debug(f'IPv6 is enabled: Current IPv6 address is {current_ipv6}')
        except ConnectionError:
            logging.error("Unable to retrieve IPv6 address")
            ipv6_enabled=False



    #update dns record if necessary
    try:
        client = DigitalOceanAPI()
        domains = client.call("get", "domains")
        for domain in domains.get("domains"):
            domain_name = domain.get("name")
            domain_records = client.call("get", f'domains/{domain_name}/records')
            for domain_record in domain_records.get("domain_records"):
                if domain_record.get("type") == 'A':
                    update_record(client, domain_name, domain_record, current_ipv4)
                elif domain_record.get("type") == 'AAAA' and ipv6_enabled:
                    update_record(client, domain_name, domain_record, current_ipv6)
    except ApiException as err:
        logging.error(err.message)
        exit(1)

if __name__ == '__main__':
    main()
