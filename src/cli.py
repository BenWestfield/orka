"""


Usage: 
    orka (--app) (--monkey)
    orka [-av]

Options:
    --app FILE          the apk file to run orka on
    --monkey SCRIPT     the defined test case to run orka on
    -h                  display the help 
    -v                  display the version number

Examples:
    orka --app foo.apk --monkey bar.py

Help:
    For more explaination, please check the readme file at
    https://github.com/BenWestfield/orka

""" 

from docopt import docopt

def main():
    "Main entry point for the tool"
    import commands
    options = docopt(__doc__, version=VERSION)
    print options
