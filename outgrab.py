#!/usr/bin/python3
"""outgrab: Programatically turn giant output files into useful, readable files."""
 
#-------------------------------------------------------------------------------
# outgrab: "output grabber"
# The motivating case is to parse the output files of simulation programs
# and create reports for human readability,
# for use as input to other programs (spreadsheets, other simulations, ...),
# or for plotting or any other use. The basic scheme is to find combinations
# of input lines and then print information from those lines.
# Can be invoked as a python library or as a program interpreter.
#-------------------------------------------------------------------------------
# Why would you use this program instead of grep, sed, awk, cut, paste, etc.?
# 1. Because you forget how to use all of the options of those programs.
# 2. Because outgrab maintains its state (the current line) between commands:
#    this can make a sequence of commands more simple and more efficient.
# 3. Because the commands included are very close to what you would do by hand
#    when searching through an output file and selecting the bits of interest.
#-------------------------------------------------------------------------------

import sys
import os
import re
import logging
from outgrab_startup import getparser, setlogging, setverbositylevels

# Set up command line parsing; get verbosity level from command line
parserargs = getparser()
verbosity = parserargs.verbosity

# Set up logging levels from most verbose to least.
myloglevel = setverbositylevels(verbosity,verbosity_default=2)
myloglevelnames = ("ogdebug","ogverbose","oginfo","ogmain")
(msg, maxlevel, (   ogdebug,  ogverbose,  oginfo,  ogmain)) = setlogging(myloglevel,myloglevelnames)

#Demonstration/Test of logging.
#Only those with log(verbosity) level >=(<=) loglevel(verbosity) should be printed.
msg(ogmain,   "printing status messages at verbosity level {} (ogmain)".format(maxlevel-ogmain+1))
msg(oginfo,   "printing status messages at verbosity level {} (oginfo)".format(maxlevel-oginfo+1))
msg(ogverbose,"printing status messages at verbosity level {} (ogverbose)".format(maxlevel-ogverbose+1))
msg(ogdebug,  "printing  debug messages at verbosity level {} (ogdebug)".format(maxlevel-ogdebug+1))

#
# module level functions
#

def createInputFiles():
#   Create input files from the command line: from stdin, from --inputfiles,
#   and also create an empty scratch file
#   Return them in a dictionary with standard names as keys ("$file1", "$file2", etc. and "scratch")
    ifilesd = {}

#   Create InputFile from stdin
    filenum = 1
    name1, x = createInputFile(sys.stdin,InputFile,filenum)
    ifilesd[name1] = x
    x.name1 = name1

#   Create any files from input argument "-i" or "--inputfiles"
    if parserargs.inputfiles:
        for myfile in parserargs.inputfiles:
            filenum += 1
            name1, x = createInputFile(myfile,InputFile,filenum)
            ifilesd[name1] = x
            x.name1 = name1

#   get rid of any empty files
    emptyfilelist = []
    for thisfile in ifilesd.keys():
        if ifilesd[thisfile].length <= 0:
            emptyfilelist.append(thisfile)
    for thisfile in emptyfilelist:
            msg(ogmain,"deleting empty {} = {}".format(ifilesd[thisfile].name, ifilesd[thisfile].name1))
            del ifilesd[thisfile]

#   but now create one empty file named "scratch" for a scratch space
#   ignore the original name created
    junk, x = createInputFile(0,ScratchFile,0)
    msg(ogdebug,"new file name: \"{}\"".format("scratch"))
    msg(ogdebug,"new file object: {}".format(x))
    x.name = "scratch"
    ifilesd[x.name] = x
    x.name1 = x.name

    return ifilesd

def createInputFile(fh,Inp,filenum):
#   create Inp=InputFile (or ScratchFile) object from filehandler (fh)
#   with suggested name "$file(filenum). e.g. createInputFile(fh,InputFile,3)
    filebase = "$file"
    newfilename = filebase + str(filenum)
    if fh: msg(ogmain,"reading {}".format(fh.name))
    newfile = Inp(fh)
    msg(ogmain,"new file suggested name: \"{}\"".format(newfilename))
    msg(ogdebug,"new file object: {}".format(newfile))
    return newfilename, newfile

def composestring(stringlist,delim=" "):
#  Concatenate each string in stringlist togther with delimiter between them.
    result = ""
    for mystring in stringlist:
        result += (mystring + delim)
    result.rstrip()
    msg(ogdebug,"--in composestring, result= \"{}\"".format(result))
    return result   

def getfieldlist(mystring,delim="whitespace"):
#   split current line into fields based on a regular expression delimiter
#   returns dictionary with keys = $field1, $field2, etc.
#   if fieldnameslist is defined correctly.
    msg(ogverbose,"getting fields from string")
    if delim == "whitespace":
        delim = "[\s]+"
    if delim == "comma":
        delim = "[,]"   # no + so that empty fields are maintained
    fieldlist = re.split(delim,mystring) 
    msg(ogdebug,"--list of fields:")
    msg(ogdebug,fieldlist)
    return fieldlist

def getslicelist(mystring,startend):
#    get sections of mystring beginning at character (or column) start
#    and ending with character (or column) end; return as new string.
#    startend is list of tuples, each with a start and end
#    [(start1,end1),(start2,end2),...]
#    Returns a list of the resulting string slices
    myslices = []
    count = 0
    for (start,end) in startend:
        count += 1
        if end > len(mystring):     #short circuit if section too long
            msg(ogverbose,"section {} too long in getslicelist".format(count))
            end = len(mystring)
            myslices.append(mystring[start:end+1])
            break
        myslices.append(mystring[start:end+1])
    msg(ogdebug,"--in getslicelist, captured slices = {}".format(myslices))
    return myslices

def getfielddic(mystring,fieldnameslist,delim="whitespace"):
#   split current line into fields based on a regular expression delimiter
#   returns dictionary with keys = $field1, $field2, etc.
#   if fieldnameslist is defined correctly.

    fieldlist = getfieldlist(mystring)
    fieldnames = fieldnameslist[:len(fieldlist)]
    msg(ogdebug,"--list of field names:")
    msg(ogdebug,fieldnames)
    fields = dict(zip(fieldnames,fieldlist))
    msg(ogdebug,"--fields dictionary:")
    msg(ogdebug,fields)
    return fields

def getslicedic(mystring,slicenameslist,startend):
#   split current line into slices based on startend (see getsliceslist)
#   returns dictionary with keys = $slice1, $slice2, etc.
#   if slicenameslist is defined correctly.

    slicelist = getslicelist(mystring,startend)
    slicenames = slicenameslist[:len(slicelist)]
    msg(ogdebug,"--list of slice names:")
    msg(ogdebug,slicenames)
    slices = dict(zip(slicenames,slicelist))
    msg(ogdebug,"--slices dictionary:")
    msg(ogdebug,slices)
    return slices

def translatefields(stringlist,fields=None,slices=None):
#    given a mixed list of strings, some normal strings,
#    and some designating fields ($field1 etc.), or slices ($slice1 etc.),
#    substitute the contents of the fields for the field designators
#    and return a list of simple strings
#    stringlist = list, fields = dictionary
    for i,mystring in enumerate(stringlist):
        if "$field" in mystring and mystring in fields:
            stringlist[i] = fields[mystring]
        if "$slice" in mystring and mystring in slices:
            stringlist[i] = slices[mystring]
    msg(ogdebug,"--in translatefields, final list of strings = {}".format(stringlist))
    return stringlist

def substitute(pattern,repl,instring,count=1):
#   substitute repl for pattern in instring count times (if there are that many)
#   return resulting string or None if no substitution occurred
    outstring=re.sub(pattern,repl,instring,count)
    if instring == outstring:
        outstring = None
        msg(oginfo,"no substitute performed in substitute.")
    else:
        msg(ogverbose,"in substitute, replaced line")
        msg(ogdebug,"--old: \"{}\"".format(instring))
        msg(ogdebug,"--new: \"{}\"".format(outstring))
        
    return outstring

def matchnextcopy(infile,outfile,mystring,nfind=1,nnext=0,ncopy=1):
#   for nfind instances: find line in infile object with match string, go forward or backward nnext lines,
#   (determined by postive or negative nnext) and write ncopy lines to outfile object.
#   works just like matchnextreturn, but actually writes to outfile
    mylines = infile.matchnextreturn(mystring,nfind,nnext,ncopy)
    if mylines:
        msg(oginfo,"found match in matchnextcopy")
        msg(ogdebug,mylines)
        outfile.addlines(mylines)

def copyline(infile,outfile):
    msg(oginfo,"copying line from input to output")
    myline = infile.getline()
    outfile.addline(myline)

def copylines(infile,outfile,nlines=1):
#   copy nlines lines, starting from current line in infile, to outfile
    msg(oginfo,"copying {} lines from input to output".format(nlines))
    mylines = infile.getlines(nlines)
    outfile.addlines(mylines)

def initializenameslist(namebase,maxnum):
#   produce list of names (for fields or slices etc.) to potentially be used later
#   e.g. if namebase = "$field", produce: ["$field1", "$field2",..]
#   maxnum should be larger than expected number of names required
    names = [namebase]*maxnum
    for i in range(maxnum):
        names[i] += str(i+1)
    return names


class InternalFile:
#   Base class for internal representation of files

    def __init__(self):
        self.lines = []
        self.length = 0
        self.name = "empty"
        self.name1 = "empty"
        self.type = "Initialized"
        msg(ogverbose,"initializing file with name {}".format(self.name1))

    def interpretposition(self,myposition):
#   convert named positions to line numbers etc.
        if isinstance(myposition,str):
           myposition = self.positions[myposition]
        elif isinstance(myposition,int):
           pass 
        else:
           msg(ogmain,"stopping: position must be string (label) or integer (line no.)")
           sys.exit("stopping: position must be string (label) or integer (line no.)")
        return myposition
    
    def interpretpositionpair(self,start,end):
#   set defaults for starting and ending lines if start and/or end missing
        if start is None:     start = 0
        if end   is None:     end = self.length - 1
        start = self.interpretposition(start)
        if start < 0:
            start = 0
            msg(ogverbose,"position past beginning of file, reset to first line")
        end   = self.interpretposition(end)
        if end >= self.length:
            end = self.length - 1
            msg(ogverbose,"position past end of file, reset to end")
        return start,end
    
    def goto(self,myposition):
#   set current line to myposition; this is now just a synonym for update current
        return self.updatecurrent(myposition)

    def addline(self,mystring):
#   add mystring as new line at end of file
        msg(ogdebug,"--adding line \"{}\" to {} file {}".format(mystring,self.type,self.name1))
        self.lines.append(mystring)
        self.length += 1

    def addlines(self,mylines):
#   add mylines as new lines at end of output file
        msg(ogdebug,"--adding lines \"{}\" to {} file {}".format(mylines,self.type,self.name1))
        for line in mylines:
            self.lines.append(line)
        self.length += len(mylines)

    def insertexternalfile(self,filename):
#   insert named file (not a file object currently in memory) at end of file
#   useful for standard headers or similar
        linenum = self.length 
        msg(ogmain,"inserting file {} at end (line {}) in {} file {}".format(filename,linenum,self.type,self.name1))
        with open(filename,"r") as f:
            for line in f:
                self.lines.append(line.rstrip())
        self.length = len(self.lines)

    def writefile(self):
#   write the in-memory file object to stdout
        msg(oginfo,"writing {} file {}".format(self.type,self.name1))
        for line in self.lines:
            print(line)
        msg(ogmain,"finished writing")

class OutputFile(InternalFile):
#   Output file is list of lines eventually to be sent to stdout

    def __init__(self):
        InternalFile.__init__(self)
        self.type = "OutputFile"
        self.name1 = "output"


class InputFile(InternalFile):
# InputFile is object holding an input file

    def __init__(self,fh,start=None,end=None):    # fh is a filehandler object
        InternalFile.__init__(self)
        self.type = "InputFile"
        self.getinputfile(fh,start,end)
        self.initializepositions()
        self.fieldnameslist = initializenameslist("$field",100)
        self.slicenameslist = initializenameslist("$slice",100)

    def initializepositions(self):
#   define standard locations within the file
#   define a dictionary to hold them and any remembered positions
#   initialize current to first line of file
        self.current=0
        self.positions = {}
        self.positions["current"] = self.current
        self.positions["top"] =     0
        self.positions["bottom"] =  self.length - 1
        self.positions["begin"] =   0
        self.positions["end"] =     self.length - 1
        self.positions["first"] =   0
        self.positions["last"] =    self.length - 1
        self.positions["start"] =   0
            
        self.reserved_positions = ["top","bottom"]

    def getinputfile(self,fh,start=None,end=None):
#   fh is a filehandler object. If fh == 0, create an empty list
#   read in the file (or part of it) and load into "lines" list
        if not fh or fh == 0:
            return
        if end is None:
            if start is None:  # no start and no end specified: read entire file
                with fh as f:
                    self.lines=[x.rstrip() for x in f]
            else:              # start given: read from "start" to EOF
                with fh as f:
                    self.lines=[x.rstrip() for i,x in enumerate(f) if i>=start]
        else:                  # end is given: read up to "end"
            if start is None:  # read from start to "end"
                with fh as f:
                    self.lines=[x.rstrip() for i,x in enumerate(f) if i<=end]
            else:              # both given: read from "start" to "end"
                with fh as f:
                    self.lines=[x.rstrip() for i,x in enumerate(f) if i>= start and i<=end]

        self.name = f.name
        self.name1 = ""
        self.length = len(self.lines)

    def updatecurrent(self,newline):
#   set the current line to newlineno
#   or to begin or end of file if newlineno is past one of those
        self.current = self.interpretposition(newline)
        self.positions["current"] = self.current
        return self.current

    def next(self,increment=1):
#   go forward increment number of lines (increment-1 => goto next line)
#   if increment < 0, go backwards
        self.current += increment
        result = self.updatecurrent(self.current)
        return result

    def back(self,increment=1):
#   go back increment number of lines
        if increment < 0:
            increment = -increment # only allow positive increment in back
            msg(oginfo,"Only positive increments allowed in back: set to positive")
        self.current -= increment
        result = self.updatecurrent(self.current)
        return result

    def remember(self,myposition):
#   label current line for later use
        msg(ogdebug,"--remembering current line as {}".format(myposition))
        if myposition in self.reserved_positions:
            msg(ogmain,"Unable to overwrite reserved position {}.".format(myposition)) 
            return
        else:
            self.positions[myposition] = self.current 

    def forget(self,myposition):
#   remove reference to myposition
        msg(ogdebug,"--forgetting line position {}".format(myposition))
        if myposition in self.reserved_positions:
            msg(ogmain,"Unable to forget reserved position {}.".format(myposition)) 
            return
        else:
            del self.positions[myposition]

    def printcurrent(self):
        msg(ogverbose,"printing current line to stout")
        print(self.lines[self.current])

    def getline(self):
#   return the current line
        return self.lines[self.current]

    def getlines(self,nlines):
#   return nlines lines including current line
        return self.lines[self.current:self.current+nlines]

    def getfields(self,delim="whitespace"):
#   split (on delimiter) the current line into fields and return them as a dictionary
#   with keys $field1, $field2, etc. defined in fieldnameslist
        return getfielddic(self.lines[self.current],self.fieldnameslist,delim)

    def getslices(self,startend):
#   return slices from current line based on startend (see getsliceslist)
#   e.g.:to get columns 2-5 as $slice1 and 8-13 as $slice2, startend = [(2,5),(8,13)]
        return getslicedic(self.lines[self.current],self.slicenameslist,startend)

    def match(self,mystring,nfind=1,dir=1):
#   starting with current line, search, in dir direction (dir>=0:up, dir<0:down)
#   for nfind lines containing mystring and set current line at the last one

        mystart = self.current
        if dir >= 0:
            dir = 1
            myend = self.length
        else:
            dir = -1
            myend = -1
        msg(ogdebug,"--in match, searching for \"{}\" from line {} to {}".format(mystring,mystart,myend-1)) 
        nfound = 0
        for lineno in range(mystart,myend,dir):
            searchObj = re.search(mystring,self.lines[lineno])
            if searchObj:
                nfound += 1
                self.goto(lineno) 
                msg(ogverbose,"found {} match of \"{}\" out of {} on line {}:".format(nfound,mystring,nfind,lineno))
                msg(ogverbose,self.lines[lineno])
                msg(oginfo,"found returned search object \"{}\"".format(searchObj))
                if nfind == nfound: return nfind

        self.goto(self.length - 1)
        msg(oginfo,"found only {} out of {} matches of \"{}\"".format(nfound,nfind,mystring)) 
        msg(oginfo,"reached end or beginning of file during match.") 
        return 0

    def matchnextreturn(self,mystring,nfind=1,nnext=0,nreturn=1):
#   for nfind instances: find match string, go forward or backward nnext lines,
#   (determined by dir) and return nreturn lines.
#   The next operates forward or backward,
#   but searches and captures only in positive direction.
#   Default is search for mystring once, and return the line containing the match.

        for i in range(nfind):
            result = self.match(mystring,1,1)
            if result == 0: 
                msg(oginfo,"match {} of \"{}\" not found in matchnextreturn.".format(i+1,mystring))
                return
            result = self.next(nnext) 
            if result <= 0 : 
                msg(oginfo,"next reached end or begin of file in matchnextreturn") 
                return
            if self.current + nreturn <= self.length: 
                mylines = self.getlines(nreturn)
            else:
                msg(oginfo,"Not enough lines in file for return section in matchnextreturn".format(i+1))
                return

        return mylines

    def empty(self):
#   empty the file in memory
        self.deleteinputsection("top","bottom")


    def deleteinputsection(self,position1,position2):
#   delete lines from an input file in memory
#   probably doing this for memory or efficiency for future searches
        msg(ogdebug,"--deleteinputsection positions 1 & 2: {} {} ".format(position1,position2))
        start = self.interpretposition(position1)
        end = self.interpretposition(position2)
        msg(ogverbose,"deleting input from line {} to line {} in {} = {}.".format(start,end,self.name,self.name1))
        del self.lines[start:end+1]
        self.updatelabels(start,end)
        return

    def updatelabels(self,start,end):
#   update the remembered labels after deleting section of input file in memory
        keylist =  list(self.positions.keys())
        for mykey in keylist:
            z = self.positions[mykey]
            if z >= start and z <= end:  
                msg(oginfo,"deleting remembered position {} with value {}".format(mykey,z))
#                del self.positions[mykey]
                self.forget(mykey)
            if z > end:
                z = z - (end - start) 
                msg(oginfo,"resetting remembered position {} to {}".format(mykey,z))
                self.positions[mykey]=z
        msg(ogverbose,"resetting current position to top of file")
        self.updatecurrent(0)
        msg(ogverbose,"resetting \"top\" and \"bottom\" remembered labels")
        self.length = len(self.lines)
        self.positions["top"] =     0
        self.positions["bottom"] =  self.length - 1
        return

    def writefile(self):
#   use logging to write input file to stderr
        msg(ogmain,"entire input file:")
        for line in self.lines:
            msg(ogmain,line)

class ScratchFile(InputFile):
#   A ScratchFile is an Inputfile with extra methods for modifying its lines
#   in place. Intended to be used as "scratch" space before copying to output.
#   Always initialized as empty.

    def __init__(self,fh,start=None,end=None):
        InputFile.__init__(self,0,start=None,end=None)
        self.type = "ScratchFile"
        self.name = "scratch"
        self.name1 = "scratch"

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def main():

#   Get all InputFiles specified on commandline (--> $file1, $file2, etc.)
#   and create a ScratchFile "scratch"
    ifilesd = createInputFiles()

#   Set up the output file
    y = OutputFile()
            
    mykeys = list(ifilesd.keys())
    mykeys.remove("scratch")
    for thisfile in mykeys:
        x = ifilesd[thisfile]
        msg(oginfo,"searching in file: {} = {}".format(x.name,x.name1))

        if x.name == "b.txt":
            x.goto("top")
            x.next()
            x.remember("mystart")
            x.next()
            x.remember("myend")
            x.deleteinputsection("mystart","myend") 
            msg(ogverbose,"file {} = {} after deleting section:".format(x.name,x.name1))
            x.writefile() 

        x.goto("top")
        nfound = x.match("cc",2,1)
        msg(ogverbose,"after match, current line is: {}".format(x.current))

        mystring = x.getline()
        mystring = substitute("cc","This was cc",mystring)
        y.addline(mystring)
        
        mystring = x.getline()
        fields = x.getfields(delim="whitespace")
#       a list of strings to print separated by a delimiter
#       fields from getfieldlist are identifed by $field1, $field2, etc.
        mybits = ["Here are some fields I found:","$field1","other text","$field4"]
        mybits = translatefields(mybits,fields)
        mybits = composestring(mybits," ")
        y.addline(mybits)

        mystring = x.getline()
        if len(mystring) > 0:
            slices = x.getslices([(2,5),(8,13)])
            mybits = ["Slices of the line:", "$field1", "$slice1", "$field2", "$slice2"]
#            fields = {}
            mybits = translatefields(mybits,fields,slices)
            newstring = composestring(mybits," ")
            y.addline(newstring)

        x.goto("top")
        matchnextcopy(x,y,"cc",1,0,2)

#
#
#   When running og script, won't have "newstring" var to hold result... write directly to output or scratch??
#   need(?) loops
#   modify copyline, copylines to also write to scratch with checking... don't allow copying input file to input file other then scratch?
#
#


    print("----------------------------------------------") 
    y.writefile()

    return


if __name__ == "__main__":
    main()
