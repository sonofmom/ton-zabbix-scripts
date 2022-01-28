#!/usr/bin/env python3
#

import json
import random
import string


def gen_uuid(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def gen_item(api, key, key_text, unit):
    return {
        "uuid": gen_uuid(32),
        "name": api + " " + key_text,
        "type": "EXTERNAL",
        "key": "parse_tc_analytics.py[\"--file\",\"{$ANALYTICS.FILE}\",\"--verbosity\",\"0\",\"--maxage\",{$ANALYTICS.MAXAGE}, \"" + api + "\",\"" + key + "\"]",
        "delay": "5m",
        "history": "180d",
        "trends": "1095d",
        "units": unit
    }

if __name__ == '__main__':
    apis = [
        "/api/v2/",
        "/api/v2/getAddressInformation",
        "/api/v2/getExtendedAddressInformation",
        "/api/v2/getWalletInformation",
        "/api/v2/getTransactions",
        "/api/v2/getAddressBalance",
        "/api/v2/getAddressState",
        "/api/v2/packAddress",
        "/api/v2/unpackAddress",
        "/api/v2/getMasterchainInfo",
        "/api/v2/lookupBlock",
        "/api/v2/shards",
        "/api/v2/getBlockTransactions",
        "/api/v2/getBlockHeader",
        "/api/v2/tryLocateTx",
        "/api/v2/tryLocateResultTx",
        "/api/v2/tryLocateSourceTx",
        "/api/v2/detectAddress",
        "/api/v2/sendBoc",
        "/api/v2/sendCellSimple",
        "/api/v2/sendQuery",
        "/api/v2/sendQuerySimple",
        "/api/v2/estimateFee",
        "/api/v2/estimateFeeSimple",
        "/api/v2/runGetMethod",
        "/api/v2/jsonRPC?method=getAddressInformation",
        "/api/v2/jsonRPC?method=getExtendedAddressInformation",
        "/api/v2/jsonRPC?method=getWalletInformation",
        "/api/v2/jsonRPC?method=getTransactions",
        "/api/v2/jsonRPC?method=getAddressBalance",
        "/api/v2/jsonRPC?method=getAddressState",
        "/api/v2/jsonRPC?method=packAddress",
        "/api/v2/jsonRPC?method=unpackAddress",
        "/api/v2/jsonRPC?method=getMasterchainInfo",
        "/api/v2/jsonRPC?method=lookupBlock",
        "/api/v2/jsonRPC?method=shards",
        "/api/v2/jsonRPC?method=getBlockTransactions",
        "/api/v2/jsonRPC?method=getBlockHeader",
        "/api/v2/jsonRPC?method=tryLocateTx",
        "/api/v2/jsonRPC?method=tryLocateResultTx",
        "/api/v2/jsonRPC?method=tryLocateSourceTx",
        "/api/v2/jsonRPC?method=detectAddress",
        "/api/v2/jsonRPC?method=sendBoc",
        "/api/v2/jsonRPC?method=sendCellSimple",
        "/api/v2/jsonRPC?method=sendQuery",
        "/api/v2/jsonRPC?method=sendQuerySimple",
        "/api/v2/jsonRPC?method=estimateFee",
        "/api/v2/jsonRPC?method=estimateFeeSimple",
        "/api/v2/jsonRPC?method=runGetMethod"
    ]

    items = []

    for api in apis:
        items.append(gen_item(api, "count", "count", "hits"))

    print(json.dumps(items, indent = 4))
