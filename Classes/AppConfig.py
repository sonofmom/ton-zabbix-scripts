import sys
import json
import Libraries.tools.general as gt
from Classes.Logger import Logger

class AppConfig:
    def __init__(self, args):
        self.args = args
        self.log = Logger(args.verbosity)

        self.log.log(self.__class__.__name__, 3, 'Config file ' + self.args.config_file)
        if not gt.check_file_exists(self.args.config_file):
            self.log.log(self.__class__.__name__, 1, "Configuration file does not exist!")
            sys.exit(1)
        try:
            fh = open(args.config_file, 'r')
            self.config = json.loads(fh.read())
            fh.close()
        except Exception as e:
            self.log.log(self.__class__.__name__, 1, "Configuration file read error: "+str(e))
            sys.exit(1)

# end class
