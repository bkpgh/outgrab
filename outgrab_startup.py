#!/usr/bin/python3
#   functions to set up command line parsing, verbosity, and logging

import argparse
import logging

def getparser():
    """Get parser object. """
#   Set up command line options and parser
#   from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i","--inputfiles",
                        type=argparse.FileType('r'),
                        nargs='+',
                        help='input file(s) to be processed as individuals')
    parser.add_argument("-p","--program",
                        type=argparse.FileType('r'),
                        nargs='?',
                        default="default.grab",
                        help='outgrab program file to be run on the input file(s)')
    parser.add_argument("-v","--verbosity",
                        type=int,
                        nargs='?',
                        default=0,
                        help='silent=0, main=1, info=2, verbose=3, debug=4')

    parserargs = parser.parse_args()
    return parserargs

def setlogging(myloglevel,names):
# Set up logging levels and configure logging messages
# arguments are logging level to use, and a list or tuple of names of logging levels
# the first one is assigned level 1 (most verbose), the second 2, and so on
# returns logging object, maximum logging level, tuple of levels
# use like: (msg,maxlevel,(verbose,notverbose,)) = setlogging(myloglevel,("verbose","notverbose"))
    levels = ()
    for i,name in enumerate(names):
        level = i + 1
        logging.addLevelName(level,name)
        levels += (level,)
    logging.basicConfig(level=myloglevel,format='%(message)s')
    return (logging.log,level,levels)

def setverbositylevels(verbosity,verbosity_default=2):
# set log levels from command-line verbosity
    if verbosity is None:
        verbosity=verbosity_default
# logging level runs opposite direction to verbosity
    level = (4 - verbosity) + 1
    return level
