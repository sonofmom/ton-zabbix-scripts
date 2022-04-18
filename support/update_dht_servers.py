#!/usr/bin/env python3
#

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import argparse
import Libraries.arguments as ar
import Libraries.tools.general as gt
import Libraries.tools.zabbix as zt
import Classes.AppConfig as AppConfig
import requests
import copy

def run():
    description = 'Fetches list of dht servers from network config and performs sync with zabbix'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    ar.set_standard_args(parser, "other")
    cfg = AppConfig.AppConfig(parser.parse_args())

    stats = {
        "nodes": 0,
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

    if len(rs["dht"]["static_nodes"]["nodes"]) > 0:
        nodes = {}
        # We identify DHT nodes by ip:port combination
        #
        for element in rs["dht"]["static_nodes"]["nodes"]:
            nodes["{}.{}".format(gt.dec2ip(element["addr_list"]["addrs"][0]["ip"]),element["addr_list"]["addrs"][0]["port"])] = element
    else:
        cfg.log.log(os.path.basename(__file__), 1, "Network config contains no nodes")
        sys.exit(1)

    stats["nodes"] = len(nodes)

    cfg.log.log(os.path.basename(__file__), 3, "Retrieved {} DHT servers.".format(stats["nodes"]))

    cfg.log.log(os.path.basename(__file__), 3, "Fetching list of hosts in zabbix.")
    rs = zt.fetch_hosts(cfg, [cfg.config["mapping"]["groups"]["ton_public_dht_servers"]])
    if rs is None:
        cfg.log.log(os.path.basename(__file__), 1, "Could not fetch list of hosts.")
        sys.exit(1)

    # Again, we identify hosts by ip:port
    hdata = {}
    for element in rs:
        port = next((chunk for chunk in element["macros"] if chunk["macro"] == "{$DHT.PORT}"), None)
        if port:
            hdata["{}.{}".format(element["interfaces"][0]["ip"], port["value"])] = element

    stats["hosts_known"] = len(hdata)
    cfg.log.log(os.path.basename(__file__), 3, "Retrieved {} hosts.".format(stats["hosts_known"]))


    # Scan nodes from network config, add or update key as needed
    #
    for element in nodes:
        if element not in hdata:
            if nodes[element]["addr_list"]["addrs"][0]["ip"] != 2130706433:
                cfg.log.log(os.path.basename(__file__), 3, "Adding node {}.".format(element))
                rs = add_node(cfg,nodes[element])
                if not rs:
                    cfg.log.log(os.path.basename(__file__), 1, "Could not add host.")
                    sys.exit(1)

                stats["hosts_added"] += 1
        else:
            host = copy.deepcopy(hdata[element])
            key = next((chunk for chunk in host["macros"] if chunk["macro"] == "{$DHT.KEY}"), None)
            if not key or key["value"] != nodes[element]["id"]["key"]:
                zt.set_macro(host["macros"], "{$DHT.KEY}", str(nodes[element]["id"]["key"]))

            if host != hdata[element]:
                cfg.log.log(os.path.basename(__file__), 3, "Updating node {}.".format(element))
                zt.update_host(cfg, host, hdata[element])
                stats["hosts_updated"] += 1

    # Scan nodes from zabbix, remove if unknown
    #
    for host in hdata:
        if host not in nodes:
            zt.delete_host(cfg, hdata[host])

    sys.exit(0)

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
            "host": "TON DHT node {}.{}".format(gt.dec2ip(server_data["addr_list"]["addrs"][0]["ip"]),server_data["addr_list"]["addrs"][0]["port"]),
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
                    "value": cfg.config["net"]
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

if __name__ == '__main__':
    run()
