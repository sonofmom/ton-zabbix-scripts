#!/usr/bin/env python3
#

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import argparse
import datetime
import Libraries.arguments as ar
import Classes.AppConfig as AppConfig
import requests
import json

def run():
    description = 'Fetches and returns balance of the wallet in TON using toncenter.'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    ar.set_standard_args(parser, "tc")
    parser.add_argument('address', nargs=1, help='Wallet address - REQUIRED')
    cfg = AppConfig.AppConfig(parser.parse_args())

    cfg.log.log(os.path.basename(__file__), 3, "Executing getAddressBalance query for address '{}'.".format(cfg.args.address[0]))
    start_time = datetime.datetime.now()
    payload = {
        "method": "getAddressBalance",
        "params": {
            "address": cfg.args.address[0]
        },
        "jsonrpc": "2.0",
        "id": 1
    }

    runtime = (datetime.datetime.now() - start_time)

    try:
        result = requests.post(cfg.config["toncenter"]["url"], json=payload).json()
    except Exception as e:
        cfg.log.log(os.path.basename(__file__), 1, "Could not execute toncenter query: " + str(e))
        sys.exit(1)

    if result["ok"] != True:
        cfg.log.log(os.path.basename(__file__), 1, "Could not retrieve information: {}".format(result["error"]))
        sys.exit(1)

    if cfg.args.get_time:
        print(runtime.microseconds/1000)
    else:
        #print(json.dumps(result, indent=4, sort_keys=True))
        print(int(result["result"])/10**9)

if __name__ == '__main__':
    run()
