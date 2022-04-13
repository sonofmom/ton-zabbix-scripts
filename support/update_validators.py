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
    description = 'Fetches actual list of validators and performs sync with zabbix'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    ar.set_standard_args(parser, "other")
    cfg = AppConfig.AppConfig(parser.parse_args())

    stats = {
        "validators": 0,
        "hosts_known": 0,
        "hosts_updated": 0,
        "hosts_added": 0
    }

    cfg.log.log(os.path.basename(__file__), 3, "Fetching current validation cycle.")
    cycle = fetch_validation_cycle(cfg)
    if not cycle:
        cfg.log.log(os.path.basename(__file__), 1, "Could not find active validation cycle.")
        sys.exit(1)

    validators = {}
    for element in cycle["cycle_info"]["validators"]:
        validators[element["adnl_addr"]] = element["wallet_address"]

    stats["validators"] = len(validators)
    cfg.log.log(os.path.basename(__file__), 3, "Retrieved {} validators.".format(stats["validators"]))

    cfg.log.log(os.path.basename(__file__), 3, "Fetching list of hosts in zabbix.")
    hdata = fetch_hosts(cfg, [
                        cfg.config["mapping"]["groups"]["ton_nodes"],
                        cfg.config["mapping"]["groups"]["ton_validators"]
        ])
    if hdata is None:
        cfg.log.log(os.path.basename(__file__), 1, "Could not fetch list of hosts.")
        sys.exit(1)
    stats["hosts_known"] = len(hdata)
    cfg.log.log(os.path.basename(__file__), 3, "Retrieved {} hosts.".format(stats["hosts_known"]))

    cfg.log.log(os.path.basename(__file__), 3, "Checking for nodes not known to zabbix")
    for adnl in validators:
        if adnl not in hdata:
            cfg.log.log(os.path.basename(__file__), 3, "Adding node {}.".format(adnl))
            rs = add_node(cfg, adnl, validators[adnl],
                         [
                             cfg.config["mapping"]["groups"]["ton_validators"]
                         ], [
                             cfg.config["mapping"]["templates"]["ton_node_telemetry"],
                             cfg.config["mapping"]["templates"]["ton_node_validator"],
                         ],
                          cycle["cycle_id"])
            if not rs:
                cfg.log.log(os.path.basename(__file__), 1, "Could not add host.")
                sys.exit(1)

            stats["hosts_added"] += 1

    cfg.log.log(os.path.basename(__file__), 3, "Scanning existing nodes")
    for adnl in hdata:
        host = copy.deepcopy(hdata[adnl])
        if adnl in validators:
            if cfg.config["mapping"]["groups"]["ton_nodes"] in host["groups"]:
                host["groups"].remove(cfg.config["mapping"]["groups"]["ton_nodes"])
            if cfg.config["mapping"]["groups"]["ton_validators"] not in host["groups"]:
                host["groups"].append(cfg.config["mapping"]["groups"]["ton_validators"])
            zt.set_tag(host["tags"], "c_wallet", validators[adnl])
            zt.set_macro(host["macros"], "{$LAST.CYCLE.ID}", str(cycle["cycle_id"]))
            host["status"] = '0'
        else:
            if cfg.config["mapping"]["groups"]["ton_validators"] in host["groups"]:
                host["groups"].remove(cfg.config["mapping"]["groups"]["ton_validators"])
            if cfg.config["mapping"]["groups"]["ton_nodes"] not in host["groups"]:
                host["groups"].append(cfg.config["mapping"]["groups"]["ton_nodes"])

        if host != hdata[adnl]:
            cfg.log.log(os.path.basename(__file__), 3, "Updating node {}.".format(adnl))
            zt.update_host(cfg, host, hdata[adnl])
            stats["hosts_updated"] += 1

    cfg.log.log(os.path.basename(__file__), 2, "Run completed, added: {}, updated: {}".format(stats["hosts_added"],stats["hosts_updated"]))
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

def fetch_hosts(cfg, groups):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": "extend",
            "groupids": groups,
            "tags": [{"tag": "c_origin", "value": "validator_sync"}],
            "selectGroups": "extend",
            "selectMacros": "extend",
            "selectTags": "extend"
        },
        "auth": cfg.config["zabbix"]["api_token"],
        "id": 1
    }

    rs = zt.execute_api_query(cfg, payload)
    if not rs:
        cfg.log.log(os.path.basename(__file__), 1, "Could not fetch host list")
        return None

    result = {}
    for host in rs["result"]:
        adnl = next((chunk for chunk in host["macros"] if chunk["macro"] == "{$NODE.ADNL}"), None)
        if adnl:
            record = {
                "hostid": host["hostid"],
                "status": host["status"],
                "groups": [],
                "macros": host["macros"],
                "tags": host["tags"],
                "wallet": None
            }
            for group in host["groups"]:
                record["groups"].append(int(group["groupid"]))

            wallet = next((chunk for chunk in host["tags"] if chunk["tag"] == "c_wallet"), None)
            if wallet:
                record["wallet"] = wallet["value"]

            result[adnl["value"]] = record

    return result

def add_node(cfg, adnl, wallet, groups, templates, cycle_id):
    cfg.log.log(os.path.basename(__file__), 3, "Adding host with ADNL {}".format(adnl))

    payload = {
        "jsonrpc": "2.0",
        "method": "host.create",
        "params": {
            "host": "TON node {}...{}".format(adnl[:6],adnl[58:]),
            "interfaces":
                [
                    {
                        "type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": "127.0.0.1",
                        "dns": "",
                        "port": "10050"
                    }
                ],
            "tags": [
                {
                    "tag": "c_network",
                    "value": cfg.config["net"]
                },
                {
                    "tag": "c_stage",
                    "value": "prod"
                },
                {
                    "tag": "c_origin",
                    "value": "validator_sync"
                },
                {
                    "tag": "c_wallet",
                    "value": wallet
                }
            ],
            "macros":
                [
                    {
                        "macro": "{$NODE.ADNL}",
                        "value": adnl
                    },
                    {
                        "macro": "{$UPDATED}",
                        "value": str(gt.get_timestamp())
                    },
                    {
                        "macro": "{$LAST.CYCLE.ID}",
                        "value": str(cycle_id)
                    }
                ],
            "groups": [],
            "templates": []
        },
        "auth": cfg.config["zabbix"]["api_token"],
        "id": 1
    }
    for element in groups:
        payload["params"]["groups"].append({"groupid": element})
    for element in templates:
        payload["params"]["templates"].append({"templateid": element})

    rs = zt.execute_api_query(cfg, payload)
    if not rs:
        cfg.log.log(os.path.basename(__file__), 1, "Failed to add host with ADNL {}".format(adnl))
        sys.exit(1)

    return rs["result"]["hostids"][0]

if __name__ == '__main__':
    run()
