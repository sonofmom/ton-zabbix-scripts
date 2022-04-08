#!/usr/bin/env python3
#

import sys
import os
import argparse
import datetime

import requests

import Libraries.arguments as ar
import Classes.AppConfig as AppConfig
import Classes.LiteClient as LiteClient
import Classes.TonNetwork as TonNetwork
import json

def run():
    description = 'Fetches validators load statistics from blockchain, maps it to ADNL and returns JSON'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    ar.set_standard_args(parser)
    parser.add_argument('period', nargs=1, help='Period to fetch, in seconds - REQUIRED')

    cfg = AppConfig.AppConfig(parser.parse_args())
    lc = LiteClient.LiteClient(cfg.args, cfg.config["liteClient"], cfg.log)
    tn = TonNetwork.TonNetwork(lc, cfg.log)

    start_time = datetime.datetime.now()
    cfg.log.log(os.path.basename(__file__), 3, 'Fetching validation cycles list from elections server')
    try:
        rs = requests.get("https://elections.toncenter.com/getValidationCycles?return_participants=true&offset=0&limit=2").json()
    except Exception as e:
        cfg.log.log(os.path.basename(__file__), 1, "Could not elections request: " + str(e))
        sys.exit(1)

    cfg.log.log(os.path.basename(__file__), 3, "Looking for active cycle")
    dt = datetime.datetime.now(datetime.timezone.utc)
    now = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
    vdata = None
    for record in rs:
        if record["cycle_info"]["utime_since"] < now and record["cycle_info"]["utime_until"] >= now:
            vdata = record
            break

    if not vdata:
        cfg.log.log(os.path.basename(__file__), 1, "Could not find active validation cycle")
        sys.exit(1)

    cfg.log.log(os.path.basename(__file__), 3, 'Fetching validators load from blockchain')
    result = tn.get_validators_load(cfg.args.period[0])

    cfg.log.log(os.path.basename(__file__), 3, 'Mapping ADNLs to PUBKEYS for result')
    for i in range(len(result)):
        record = next((chunk for chunk in vdata["cycle_info"]["validators"] if chunk["pubkey"] == result[i]["pubkey"]),
                         None)
        if record:
            result[i]["adnl_addr"] = record["adnl_addr"]

    runtime = (datetime.datetime.now() - start_time)
    if not result:
        cfg.log.log(os.path.basename(__file__), 1, 'Could not retrieve information.')
        sys.exit(1)
    elif cfg.args.get_time:
        print(runtime.microseconds/1000)
    else:
        print(json.dumps(result))

if __name__ == '__main__':
    run()
