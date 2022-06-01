#!/usr/bin/env python3
#
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import argparse
import datetime
import Libraries.arguments as ar
import Libraries.tools.general as gt
import Libraries.tools.zabbix as zt
import Classes.AppConfig as AppConfig
import requests
import copy

def run():
    description = 'Fetches validators and outputs csv list'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    ar.set_standard_args(parser, "other")
    cfg = AppConfig.AppConfig(parser.parse_args())

    cfg.log.log(os.path.basename(__file__), 3, "Fetching current validation cycle.")
    cycle = fetch_validation_cycle(cfg)
    if not cycle:
        cfg.log.log(os.path.basename(__file__), 1, "Could not find active validation cycle.")
        sys.exit(1)

    validators = {}
    for element in cycle["cycle_info"]["validators"]:
        validators[element["adnl_addr"]] = element["wallet_address"]

    cfg.log.log(os.path.basename(__file__), 3, "Retrieved {} validators.".format(len(validators)))

    cfg.log.log(os.path.basename(__file__), 3, "Fetching telemetry data.")
    rs = fetch_telemetry(cfg)
    if not rs:
        cfg.log.log(os.path.basename(__file__), 1, "Could not fetch telemetry.")
        sys.exit(1)


    telemetry = {}
    for element in rs:
        telemetry[element["adnl_address"]] = element

    cfg.log.log(os.path.basename(__file__), 3, "Retrieved {} telemetry records.".format(len(telemetry)))

    cfg.log.log(os.path.basename(__file__), 3, "Extracting telemetry for active validators.")
    v_t = {}
    for element in validators.keys():
        if element in telemetry:
            v_t[element] = {"t": telemetry[element], "w": validators[element]}

    cfg.log.log(os.path.basename(__file__), 3, "Got telemetry for {} validators.".format(len(v_t)))

    cfg.log.log(os.path.basename(__file__), 3, "Performing Output below")
    print("active validators:,{},,,,,".format(len(validators)))
    print("wallet,adnl,country,isp,cpus,mytonctrl version,validator version")
    for element in v_t:
        line = []
        line.append(v_t[element]["w"])
        line.append(v_t[element]["t"]["adnl_address"])
        line.append(v_t[element]["t"]["remote_country"])
        line.append(v_t[element]["t"]["remote_isp"])
        line.append(str(v_t[element]["t"]["data"]["cpuNumber"]))
        line.append(str(v_t[element]["t"]["data"]["gitHashes"]["mytonctrl"]))
        line.append(str(v_t[element]["t"]["data"]["gitHashes"]["validator"]))

        print (",". join(line))

    sys.exit(0)

def fetch_validation_cycle(cfg):
    cfg.log.log(os.path.basename(__file__), 3, 'Fetching validation cycles list from elections server')
    try:
        rs = requests.get("{}/getValidationCycles?return_participants=true&offset=0&limit=2".format(cfg.config["elections"]["url"])).json()
    except Exception as e:
        cfg.log.log(os.path.basename(__file__), 1, "Could not perform elections request: " + str(e))
        sys.exit(1)

    cfg.log.log(os.path.basename(__file__), 3, "Looking for active cycle")
    dt = datetime.datetime.now(datetime.timezone.utc)
    now = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
    for record in rs:
        if record["cycle_info"]["utime_since"] < now and record["cycle_info"]["utime_until"] >= now:
            return record

def fetch_telemetry(cfg):
    cfg.log.log(os.path.basename(__file__), 3, 'Fetching telemetry for last {} seconds from server'.format(cfg.config["telemetry"]["offset"]))
    dt = datetime.datetime.now(datetime.timezone.utc)
    now = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
    try:
        rs = requests.get("{}/getTelemetryData?timestamp_from={}&api_key={}".format(cfg.config["telemetry"]["url"],now-cfg.config["telemetry"]["offset"],cfg.config["telemetry"]["api_key"],)).json()
    except Exception as e:
        cfg.log.log(os.path.basename(__file__), 1, "Could not perform elections request: " + str(e))
        sys.exit(1)

    return rs

if __name__ == '__main__':
    run()
