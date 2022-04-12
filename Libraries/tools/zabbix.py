import requests
import os

def execute_api_query(cfg, payload, post=False):
    cfg.log.log(os.path.basename(__file__), 3, "Executing zabbix `{}` query.".format(payload["method"]))
    try:
        if post:
            rs = requests.post(cfg.config["zabbix"]["url"], json=payload).json()
        else:
            rs = requests.get(cfg.config["zabbix"]["url"], json=payload).json()
    except Exception as e:
        cfg.log.log(os.path.basename(__file__), 1, "Could not execute zabbix query: " + str(e))
        return None

    if "error" in rs:
        cfg.log.log(os.path.basename(__file__), 1, "Could not execute zabbix query: {}".format(rs["error"]["data"]))
        return None

    return rs

def fetch_hosts(cfg, groups, identifier):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": "extend",
            "groupids": groups,
            "selectGroups": "extend",
            "selectMacros": "extend",
            "selectTags": "extend",
            "selectInterfaces": "extend"
        },
        "auth": cfg.config["zabbix"]["api_token"],
        "id": 1
    }

    rs = execute_api_query(cfg, payload)
    if not rs:
        cfg.log.log(os.path.basename(__file__), 1, "Could not fetch host list")
        return None

    result = {}
    for host in rs["result"]:
        macro = next((chunk for chunk in host["macros"] if chunk["macro"] == identifier),
                         None)
        if macro:
            record = {
                "hostid": host["hostid"],
                "groups": [],
                "macros": host["macros"],
                "tags": host["tags"],
                "interfaces": host["interfaces"]
            }
            for group in host["groups"]:
                record["groups"].append(int(group["groupid"]))

            result[macro["value"]] = record

    return result


def set_tag(tags, tag, value):
    i = next((index for (index, chunk) in enumerate(tags) if chunk["tag"] == tag), None)
    if (i):
        tags[i]["value"] = value
    else:
        tags.append({"tag": tag, "value": value})

    return tags
