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
import json

def run():
    description = 'Fetches list of dht servers from network config and performs sync with zabbix'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    ar.set_standard_args(parser, "other")
    cfg = AppConfig.AppConfig(parser.parse_args())

    stats = {
        "servers": 0,
        "hosts_known": 0,
        "hosts_updated": 0,
        "hosts_added": 0,
        "hosts_disabled": 0
    }

    cfg.log.log(os.path.basename(__file__), 3, "Fetching network config.")
    try:
        rs = requests.get(cfg.config["configs"]["global_public"]).json()
    except Exception as e:
        cfg.log.log(os.path.basename(__file__), 1, "Could not retrieve network config: " + str(e))
        sys.exit(1)

    servers = {}
    for element in rs["dht"]["static_nodes"]["nodes"]:
        servers[element["id"]["key"]] = element

    stats["servers"] = len(servers)
    cfg.log.log(os.path.basename(__file__), 3, "Retrieved {} DHT servers.".format(stats["servers"]))

    cfg.log.log(os.path.basename(__file__), 3, "Fetching list of hosts in zabbix.")
    hdata = zt.fetch_hosts(cfg, [cfg.config["mapping"]["groups"]["ton_nodes"]], '{$NODE.ADNL}')
    if hdata is None:
        cfg.log.log(os.path.basename(__file__), 1, "Could not fetch list of hosts.")
        sys.exit(1)
    stats["hosts_known"] = len(hdata)
    cfg.log.log(os.path.basename(__file__), 3, "Retrieved {} hosts.".format(stats["hosts_known"]))

    for element in servers:
        if element not in hdata and servers[element]["addr_list"]["addrs"][0]["ip"] != 2130706433:
            cfg.log.log(os.path.basename(__file__), 3, "Adding node {}.".format(element))
            rs = add_node(cfg,servers[element])
            if not rs:
                cfg.log.log(os.path.basename(__file__), 1, "Could not add host.")
                sys.exit(1)

            stats["hosts_added"] += 1

    sys.exit(0)


    cfg.log.log(os.path.basename(__file__), 3, "Checking for nodes not known to zabbix")
    for element in validators:
        if element not in hdata:
            cfg.log.log(os.path.basename(__file__), 3, "Adding node {}.".format(element))
            rs = add_node(cfg,element,
                         [
                             cfg.config["mapping"]["groups"]["ton_validators"]
                         ], [
                             cfg.config["mapping"]["templates"]["ton_node_telemetry"],
                             cfg.config["mapping"]["templates"]["ton_node_validator"],
                         ])
            if not rs:
                cfg.log.log(os.path.basename(__file__), 1, "Could not add host.")
                sys.exit(1)

            stats["hosts_added"] += 1

    cfg.log.log(os.path.basename(__file__), 3, "Scanning existing nodes")
    for element in hdata:
        groups = hdata[element]["groups"].copy()
        if element in validators:
            if cfg.config["mapping"]["groups"]["ton_nodes"] in groups:
                groups.remove(cfg.config["mapping"]["groups"]["ton_nodes"])
            if cfg.config["mapping"]["groups"]["ton_validators"] not in groups:
                groups.append(cfg.config["mapping"]["groups"]["ton_validators"])
        else:
            if cfg.config["mapping"]["groups"]["ton_validators"] in groups:
                groups.remove(cfg.config["mapping"]["groups"]["ton_validators"])
            if cfg.config["mapping"]["groups"]["ton_nodes"] not in groups:
                groups.append(cfg.config["mapping"]["groups"]["ton_nodes"])

        if groups != hdata[element]["groups"]:
            cfg.log.log(os.path.basename(__file__), 3, "Updating node {}.".format(element))
            update_node(cfg, hdata[element], groups)
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


def add_node(cfg, server_data):
    cfg.log.log(os.path.basename(__file__), 3, "Adding host with KEY {}".format(server_data["id"]["key"]))

    groups = [
        cfg.config["mapping"]["groups"]["ton_public_dht_servers"]
    ]
    templates = [
        cfg.config["mapping"]["templates"]["ton_dht_server"]
    ]


    payload = {
        "jsonrpc": "2.0",
        "method": "host.create",
        "params": {
            "host": "TON DHT node {}".format(gt.dec2ip(server_data["addr_list"]["addrs"][0]["ip"])),
            "interfaces":
                [
                    {
                        "type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": gt.dec2ip(server_data["addr_list"]["addrs"][0]["ip"]),
                        "dns": "",
                        "port": "10050"
                    }
                ],
            "tags": [
                {
                    "tag": "c_network",
                    "value": "mainnet"
                },
                {
                    "tag": "c_stage",
                    "value": "prod"
                },
                {
                    "tag": "c_origin",
                    "value": "dht_sync"
                }
            ],
            "macros":
                [
                    {
                        "macro": "{$DHT.KEY}",
                        "value": server_data["id"]["key"]
                    },
                    {
                        "macro": "{$DHT.PORT}",
                        "value": str(server_data["addr_list"]["addrs"][0]["port"])
                    },
                    {
                        "macro": "{$UPDATED}",
                        "value": str(gt.get_timestamp())
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
        cfg.log.log(os.path.basename(__file__), 1, "Failed to add host with KEY {}".format(server_data["id"]["key"]))
        sys.exit(1)

    return rs["result"]["hostids"][0]

def update_node(cfg, host, groups):
    cfg.log.log(os.path.basename(__file__), 3, "Updating host with ID {}".format(host["hostid"]))

    payload = {
        "jsonrpc": "2.0",
        "method": "host.update",
        "params": {
            "hostid": str(host["hostid"]),
            "groups": []
        },
        "auth": cfg.config["zabbix"]["api_token"],
        "id": 1
    }
    for group in groups:
        payload["params"]["groups"].append({"groupid": group})

    rs = zt.execute_api_query(cfg, payload)
    if not rs:
        cfg.log.log(os.path.basename(__file__), 1, "Failed to update host with hostid {}".format(host["hostid"]))
        sys.exit(1)

    cfg.log.log(os.path.basename(__file__), 3, "Bumping updated macro")
    element = next((chunk for chunk in host["macros"] if chunk["macro"] == "{$UPDATED}"), None)

    if element:
        payload = {
            "jsonrpc": "2.0",
            "method": "usermacro.update",
            "params": {
                "hostmacroid": str(element["hostmacroid"]),
                "value": str(gt.get_timestamp())
            },
            "auth": cfg.config["zabbix"]["api_token"],
            "id": 1
        }
        rs = zt.execute_api_query(cfg, payload)
        if not rs:
            cfg.log.log(os.path.basename(__file__), 1, "Failed to update macro with hostmacroid {}".format(element["hostmacroid"]))

    else:
        cfg.log.log(os.path.basename(__file__), 3, "Updated macro not found")

    return True

if __name__ == '__main__':
    run()
