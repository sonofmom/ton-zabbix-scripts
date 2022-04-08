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
