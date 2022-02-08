#!/usr/bin/env python3
#

import sys
import os
import argparse
import Libraries.tools.general as gt
from Classes.Logger import Logger
import json

def run():
    description = 'Parses toncenter codes analytics JSON and returns result.'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    parser.add_argument('-f', '--file',
                        required=True,
                        dest='file',
                        action='store',
                        help='File containing analytics information - REQUIRED')

    parser.add_argument('-m', '--maxage',
                        required=False,
                        type=int,
                        default=300,
                        dest='maxage',
                        action='store',
                        help='Maximum age of analytics file in seconds - OPTIONAL')

    parser.add_argument('-v', '--verbosity',
                        required=False,
                        type=int,
                        default=0,
                        dest='verbosity',
                        action='store',
                        help='Verbosity 0 - 3')

    parser.add_argument('code_range', nargs=2, help='Code range <from> <to> - REQUIRED')
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
        analytics = json.loads(fh.read())
        fh.close()
    except Exception as e:
        log.log(os.path.basename(__file__), 1, "Configuration file read error: " + str(e))
        sys.exit(1)

    count = 0
    log.log(os.path.basename(__file__), 3, "Looking for codes in range {}-{}".format(args.code_range[0], args.code_range[1]))
    for element in analytics:
        if element["status_code"] >= int(args.code_range[0]) and element["status_code"] <= int(args.code_range[1]):
            count += int(element["count"])

    print(count)
    sys.exit(0)

def print_line(debug, line):
    if(debug):
        print(line)

if __name__ == '__main__':
    run()
