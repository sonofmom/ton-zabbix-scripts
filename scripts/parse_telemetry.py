#!/usr/bin/env python3
#

import sys
import os
import argparse
import Libraries.tools.general as gt
from Classes.Logger import Logger
import json

def run():
    description = 'Parses TON telemetry JSON and returns result.'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    parser.add_argument('-f', '--file',
                        required=True,
                        dest='file',
                        action='store',
                        help='File containing telemetry information - REQUIRED')

    parser.add_argument('-m', '--maxage',
                        required=False,
                        type=int,
                        default=300,
                        dest='maxage',
                        action='store',
                        help='Maximum age of telemetry file in seconds - OPTIONAL')

    parser.add_argument('-v', '--verbosity',
                        required=False,
                        type=int,
                        default=0,
                        dest='verbosity',
                        action='store',
                        help='Verbosity 0 - 3')

    parser.add_argument('-c', '--check',
                        required=False,
                        type=int,
                        default=0,
                        dest='check',
                        action='store',
                        help='Check existence of requested path, return 1 if exists, 0 if not')

    parser.add_argument('-k', '--keys',
                        required=False,
                        type=int,
                        default=0,
                        dest='keys',
                        action='store',
                        help='Return list of keys in requested path')

    parser.add_argument('adnl', nargs=1, help='ADNL to retrieve - REQUIRED')
    parser.add_argument('path', nargs=1, help='Telemetry path to retrieve - REQUIRED')
    args = parser.parse_args()

    log = Logger(args.verbosity)

    log.log(os.path.basename(__file__), 3, "Checking data file '{}'".format(args.file))
    if not gt.check_file_exists(args.file):
        log.log(os.path.basename(__file__), 1, "Data file '{}' does not exist!".format(args.file))
        sys.exit(1)

    log.log(os.path.basename(__file__), 3, "Checking file is not older then {} seconds.".format(args.maxage))
    if ((gt.get_timestamp() - os.path.getctime(args.file)) > args.maxage):
        log.log(os.path.basename(__file__), 1, "Data file is older then {} seconds!".format(args.maxage))
        sys.exit(1)

    log.log(os.path.basename(__file__), 3, "Parsing data file")
    try:
        fh = open(args.file, 'r')
        telemetry = json.loads(fh.read())
        fh.close()
    except Exception as e:
        log.log(os.path.basename(__file__), 1, "Configuration file read error: " + str(e))
        sys.exit(1)

    log.log(os.path.basename(__file__), 3, "Looking for ADNL '{}'".format(args.adnl[0]))
    adnl_data = next((chunk for chunk in telemetry if chunk["adnl_address"] == args.adnl[0]), None)
    if not adnl_data:
        log.log(os.path.basename(__file__), 2, "Data for ADNL '{}' not found".format(args.adnl[0]))
        sys.exit(1)

    log.log(os.path.basename(__file__), 3, "Looking for path '{}'".format(args.path[0]))
    result = gt.get_leaf(adnl_data, args.path[0].split('.'))

    if result is None:
        log.log(os.path.basename(__file__), 1, "Path '{}' was not found in data".format(args.path[0]))
        if (args.check):
            print(0)
            sys.exit(0)
        else:
            sys.exit(1)

    if args.check == 1:
        print(1)
    elif args.keys == 1:
        keys = []
        if isinstance(result, dict):
            keys = list(result.keys())
        elif isinstance(result, list):
            for x in range(len(result)):
                keys.append(x)
        else:
            log.log(os.path.basename(__file__), 3, "Keys return requested but result data is neither list or dictionary")
            sys.exit(1)

        result = []
        for key in keys:
            result.append({"{#DISKNAME}": key})

        print(json.dumps(result))

    elif isinstance(result, bool):
        print(int(result))
    else:
        print(result)

    sys.exit(0)

def print_line(debug, line):
    if(debug):
        print(line)


if __name__ == '__main__':
    run()
