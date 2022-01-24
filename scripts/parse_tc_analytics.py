#!/usr/bin/env python3
#

import sys
import os
import argparse
import Libraries.tools.general as gt
from Classes.Logger import Logger
import json

def run():
    description = 'Parses toncenter analytics JSON and returns result.'
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

    parser.add_argument('url', nargs=1, help='URL to retrieve - REQUIRED')
    parser.add_argument('key', nargs=1, help='Statistics / Key to retrieve - REQUIRED')
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

    log.log(os.path.basename(__file__), 3, "Looking for URL '{}'".format(args.url[0]))
    url_data = next((chunk for chunk in analytics if chunk["url"] == args.url[0]), None)
    if not url_data:
        log.log(os.path.basename(__file__), 2, "Data for URL '{}' not found".format(args.url[0]))
        print(0)
        sys.exit(0)

    log.log(os.path.basename(__file__), 3, "Looking for key '{}'".format(args.key[0]))
    if not args.key[0] in url_data:
        log.log(os.path.basename(__file__), 1, "Key '{}' was not found in data".format(args.key[0]))
        sys.exit(1)

    print(url_data[args.key[0]])
    sys.exit(0)

    #start_time = datetime.datetime.now()
    #result  = tn.get_last()
    #runtime = (datetime.datetime.now() - start_time)
    #if not result:
    #    cfg.log.log(os.path.basename(__file__), 1, 'Could not retrieve information.')
    #    sys.exit(1)
    #elif cfg.args.get_time:
    #    print(runtime.microseconds/1000)
    #else:
    #    print(result["ago"])

def print_line(debug, line):
    if(debug):
        print(line)


if __name__ == '__main__':
    run()
