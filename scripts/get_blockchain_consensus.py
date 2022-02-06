#!/usr/bin/env python3
#

import sys
import os
import argparse
import datetime
import time
import Libraries.arguments as ar
import Libraries.tools.general as gt
import Classes.AppConfig as AppConfig
import requests
import json

def run():
    description = 'Fetches and returns latest consensus block using toncenter.'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    ar.set_standard_args(parser, "tc")
    parser.add_argument('-m', '--metric',
                        required=False,
                        type=str,
                        default='block',
                        dest='metric',
                        action='store',
                        help='Metric type, one of block|time|age|rate. Default value: block')
    parser.add_argument('-r', '--ratefile',
                        required=False,
                        type=str,
                        default='/tmp/ton_cbr.json',
                        dest='ratefile',
                        action='store',
                        help='Rate file, to store last rate query. Default value: /tmp/ton_cbr.json')
    cfg = AppConfig.AppConfig(parser.parse_args())

    cfg.log.log(os.path.basename(__file__), 3, "Executing getConsensusBlock.")
    start_time = datetime.datetime.now()
    payload = {
        "method": "getConsensusBlock",
        "params": {},
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
        if cfg.args.metric == 'time':
            print(int(result["result"]["timestamp"]))
        elif cfg.args.metric == 'age':
            result = time.mktime(datetime.datetime.now().timetuple()) - result["result"]["timestamp"]
            if result < 0:
                result = 0
            print(result)
        elif cfg.args.metric == 'rate':
            rate = 0
            cfg.log.log(os.path.basename(__file__), 3, "Checking for presence of rate file '{}'.".format(cfg.args.ratefile))
            if gt.check_file_exists(cfg.args.ratefile):
                cfg.log.log(os.path.basename(__file__), 3, "Loading and parsing file '{}'.".format(cfg.args.ratefile))
                try:
                    fh = open(cfg.args.ratefile, 'r')
                    prev_result = json.loads(fh.read())
                    fh.close()

                    seconds = time.mktime(datetime.datetime.now().timetuple()) - prev_result["result"]["timestamp"]
                    blocks = result["result"]["consensus_block"] - prev_result["result"]["consensus_block"]
                    if blocks and seconds:
                        rate = blocks / seconds
                except Exception as e:
                    cfg.log.log(os.path.basename(__file__), 1, "Could not load and parse rate file: " + str(e))
            else:
                cfg.log.log(os.path.basename(__file__), 3, "File not found.")

            try:
                fh = open(cfg.args.ratefile, 'w')
                fh.write(json.dumps(result, indent=4, sort_keys=True))
                fh.close()
            except Exception as e:
                cfg.log.log(os.path.basename(__file__), 1, "Could not write rate file: " + str(e))

            print(rate)

        else:
            print(int(result["result"]["consensus_block"]))

if __name__ == '__main__':
    run()
