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

def main():
    '''
    Main function for updating dns with digital API
    '''
    load_dotenv()
    #set log level from .env or to info
    log_level=logging.INFO
    try:
        level = os.getenv('LOG_LEVEL')
        if level is not None:
            log_level = getattr(logging, level, logging.INFO)
    except NameError:
        pass
    logging.basicConfig(
        filename="/usr/local/var/log/digital-ocean-dns-updater.log",
        level=log_level,
        format="%(asctime)s:%(levelname)s:%(message)s"
        )

    #get current ip address
    ip_request = requests.post("https://bot.whatismyipaddress.com")
    if not ip_request.ok:
        logging.error("Unable to retrieve IP address")
        sys.exit(1)
    current_ip = ip_request.content.decode("utf-8")
    current_ip='67.161.80.5'

    #update dns record if necessary
    try:
        client = DigitalOceanAPI()
        domains = client.call("get", "domains")
        for domain in domains.get("domains"):
            domain_name = domain.get("name")
            domain_records = client.call("get", f'domains/{domain_name}/records')
            for domain_record in domain_records.get("domain_records"):
                if domain_record.get("type") == 'A' and domain_record.get("data") != current_ip:
                    if domain_record.get("id") is not None:
                        logging.info(f'Updating DNS Ip for {domain_record.get("name")}.{domain_name}')
                        client.call("put", f'domains/{domain_name}/records/{domain_record.get("id")}', data={"data": current_ip})
                    else:
                        logging.error(f'Id is null for domain {domain_name} and domain record {domain_record}')

                elif domain_record.get("type") == 'A':
                    logging.debug(f'Ip is same for {domain_record.get("name")}.{domain_name}')
    except ApiException as err:
        logging.error(err.message)
        exit(1)

if __name__ == '__main__':
    main()
