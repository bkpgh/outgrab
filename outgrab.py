#!/usr/bin/python3
""" This is the outgrab processor/interpreter
    usage:
    python outgrab.py -v (verbosity)  -i (input.txt...) -p program.grab 
    -v (optional) 0 = silent, 4 = debug, 1,2(default),3 = intermediate levels of output
    -p the outgrab program to read in
    -i (optional) additional input files to read in; named $file2, $file3, etc.
    reads from stdin and internally calls that file $file1
    writes to stdout
    python outgrab.py -p program.grab < a.txt > myoutput.txt
    applies outgrab program program.grab to file a.txt, producing myoutput.txt
"""

from outgrab_tools import *

# Perform startup stuff: parse command line and set logging levels
startup()

# Create internal input files from the command line:
#      one from stdin and optionally others from -i or --inputfiles
#      Also create the outgrab program file from -p or --program on the command line
createInputFiles()

# Create a file for output
y = OutputFile()

# Assign input and output files to the outgrab program so it processes the former and writes to the latter
# Initial focus is on the input file coming from stdin
x = getfilefromname("$file1")
z = getfilefromname("program")
z.setinputfile(x)
z.setoutputfile(y)

# Process the outgrab program file
z.processcommands()

# Write the results to stdout
y.writefile()


