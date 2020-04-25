#!/usr/bin/python3
"""outgrab: Programatically select important information from large
   files and send it to other files for human or program consumption.
   outgrab.py Can be invoked as a program interpreter or 
   outgrab_tools.py and outgrab_startup can be imported as a library of python
   classes and methods.
"""

#-------------------------------------------------------------------------------
# Why would you use this program instead of grep, sed, awk, cut, paste, etc.?
# 1. Because you forget how to use all of the options of those programs.
# 2. Because outgrab maintains its state (the current line) between commands:
#    this can make a sequence of commands more simple and more efficient.
# 3. Because the commands included are very close to what you would do by hand
#    when searching through an output file and selecting the bits of interest.
#-------------------------------------------------------------------------------
# Usage: 
#
# See near the end of this file for a summary of the outgrab command language.
#
# Input text files can either come from stdin and optionally from the -i flag.
# These will be treated separately and are named $file1, $file2, etc. 
# Output goes to stdout or may be redirected into an output file
# If mytest.grab contains outgrab commands, use the outgrab interpreter:
# python outgrab.py -p mytest.grab < a.txt
# python outgrab.py -p mytest.grab < a.txt > output.ext
# cat *.txt | python -p mytest.grab > output.txt
# where mytest.grab contains outgrab commands, a.txt is an input text file,
# and output.txt is an output file. The first version sends output to the screen
# and the last version concatenates all .txt files in the current directory and uses them as input.
# e.g.
# Use as a python class/method library is less well tested. See outgrab.py as a starter.
# If mytest.py contains python statements using the classes and functions within this file:
# e.g. python mytest.py < a.txt
#      python mytest.py < a.txt > output.txt
#      python mytest.py -i b.txt < a.txt > output.txt
#      cat *.txt | python mytest.py > output.txt (files concatenated and together named $file1)
#
#-------------------------------------------------------------------------------

import sys
import os
import re
import logging
from outgrab_startup import getparser, setlogging, setverbositylevels


# global variables related to messaging
verbosity = 0
maxlevel = 4
ogdebug = 0
ogverbose = 0
oginfo = 0
ogmain = 0
parserargs = ""
msg = ""
# and a global dictionary to hold the internal files by their names
ifilesd = {}
#standard filename prefix; use with a postfix number in addfilename
filebase = "$file"

#
# module level functions
#

def startup():
# Set up command line parsing; get verbosity level from command line
    global parserargs
    global verbosity, maxlevel
    parserargs = getparser()

    verbosity = parserargs.verbosity
    setuplogging()
    return

def setuplogging():
    global msg
    global ogdebug, ogverbose, oginfo, ogmain
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

def runoutgrab(programfile,verboseness,outputfile,*inputfiles):
   """ function to set up files and launch outgrab from your program
       needs explicit file paths or local names for programfile, outputfile, and 
       an arbitrary number of inputfiles
   """
   global verbosity

   verbosity = verboseness
   setuplogging()

#  create program file
   filenum = 0
   pgmfh = open(programfile, "r")
   x = createInputFile(pgmfh,ProgramFile)
   pgmfh.close()
   addfilename(x,filebase,filenum)
   addfilename(x,"program")
   msg(oginfo,"Creating program file with names = {}".format(x.names))

#  create output file
   y = OutputFile()
   addfilename(x,outputfile)
   y.filename = outputfile
   msg(oginfo,"Creating output file with names: {}".format(y.names))

#   create scratch file
   x = createScratchFile("ScratchFile")
   addfilename(x,"scratch")
   msg(oginfo,"Creating scratch file with names: {}".format(x.names))

#  create input files
   for myfile in inputfiles:
       filenum += 1
       readinputfile(myfile,filenum)

#  Assign input and output files for the outgrab program so it processes the former and writes to the latter
#  Initial focus is on the input file coming from stdin
   x = getfilefromname("$file1")
   z = getfilefromname("program")
   z.setinputfile(x)
   z.setoutputfile(y)

#  Process the outgrab program file
   z.processcommands()

#  Write the output file
   outf = open(y.filename,"w") 
   y.writefile(outf)
   outf.close()

def readinputfile(myfile,filenum):
    """ given the path/name of a file, read it in to an internal input file
        give it a name filebase ($file) + str(filenum)
    """
    fh = open(myfile, "r")
    x = createInputFile(fh,InputFile)
    fh.close()
    addfilename(x,filebase,filenum)    # create the standard filename ($fileN)
    msg(ogdebug,"Creating input file with names = {}".format(x.names))

def createInputFiles():
    """Create input files from the command line: from stdin, from --inputfiles,
    and also create an empty scratch file
    Return them in a dictionary with standard names as keys: names = ("$file1", "$file2", etc. )
    Also give them names name = <stdin>, filename from the command line, or "scratch"
    """
    global ifilesd 

#   Create InputFile from stdin
    msg(oginfo,"Creating input files from stdin")
    x = createInputFile(sys.stdin,InputFile)
    filenum = 1
    addfilename(x,filebase,filenum)
    msg(oginfo,"Names = {}".format(x.names))

#   Create any files from input argument "-i" or "--inputfiles"
    if parserargs.inputfiles:
        msg(oginfo,"Creating input files from -i or --inputfiles")
        for myfile in parserargs.inputfiles:
            msg(ogdebug,"file = {}".format(myfile))
            filenum += 1
            x = createInputFile(myfile,InputFile)
            addfilename(x,filebase,filenum)
            msg(oginfo,"Names = {}".format(x.names))

#   Create outgrab program files from input argument "-p" or "--program"
    if parserargs.program:
        msg(oginfo,"Creating program files from -p or --program")
        filenum = 0
        x = createInputFile(parserargs.program,ProgramFile)
        addfilename(x,filebase,filenum)
        addfilename(x,"program")
        msg(oginfo,"Names = {}".format(x.names))

#   now create one empty file named "scratch" for a scratch space
#   ignore the original name created
    x = createScratchFile("Scratch")
    addfilename(x,"scratch")
    msg(oginfo,"Creating scratch file with names: \"{}\"".format(x.names))

    msg(ogdebug,"The ifilesd dictionary at end of createInputFiles:")
    for key,value in ifilesd.items():
        msg(ogdebug,"name= {}  :  object = {}".format(key,value))
     
def createScratchFile(content):
#   create ScratchFile object
    newfile = ScratchFile(content)
    msg(ogdebug,"new file object: {}".format(newfile))
    try:
        addfilename(newfile,content.name)
    except:
        pass
    return newfile

def createInputFile(content,Inp):
#   create Inp=InputFile or ProgramFile object from filehandler,string, or list of strings
    newfile = Inp(content)
    msg(ogdebug,"new file object: {}".format(newfile))
#   add a blank line at the end of the new file (to prevent matches on last line repeating...)
    newfile.addblankline()    # note "bottom" set to line before this blank line
    try:
        addfilename(newfile,content.name)
    except:
        pass
    return newfile

def getnextfilenum():
    """ look through ifilesd for all files named $filexyz (actually filebasexyz)
        and return the highest int(xyz) + 1: to be used as the next filenum
    """
    largest = -1
    start = len(filebase)
    for key in ifilesd.keys():
        if key.startswith(filebase):
            oldfilenum = int(key[start:])
            if oldfilenum > largest: largest = oldfilenum
    return largest+1
        
def getfilefromname(name):
#   returns the internal file object corresponding to myname
    return ifilesd[name]   

def samevaluekeys(mykey,mydict):
    sameas = [k for k,v in mydict.items() if v == mydict[mykey]]
    return sameas

def listofsamevaluekeys(mydict):
    usedkeys = []
    dumplist = []
    for key in mydict.keys():
        if key not in usedkeys:
            samekeys = samevaluekeys(key,mydict)
            dumplist.append(samekeys)
        for item in samekeys:
            usedkeys.append(item)
    return dumplist

def addfilename(fileobj,name,postfix=""):
#   add a name for fileobj to the ifilesd dictionary
#   and to the attribute list of names for the object
#   if postfix is present, it is added to the end of name
#   (to create standard names like $file1) 
    global ifilesd
    if isinstance(postfix,int):
        postfix = str(postfix)
    name = name + postfix
    ifilesd[name] = fileobj
    fileobj.names.append(name)
    msg(oginfo,"Adding name {} for file object {}".format(name,fileobj))

def setfilename(*names):
#   give an internal file a new name (old one remains unless you overwrite it)
#   first names should be old one, 2nd is new one.
    x = getfilefromname(names[0])
    addfilename(x,names[1])

def stringlisttostring(stringlist,delim=" "):
#  Concatenate each string in stringlist togther with delimiter between them.
    result = ""
    for mystring in stringlist:     #does this ignore empty strings ("") ?
        result += (mystring + delim)
    result.rstrip()
    msg(ogdebug,"--in stringlisttostring, result= \"{}\"".format(result))
    return result   

def stringtostringlist(mystring,delim="whitespace"):
#   split mystring into fields based on a regular expression delimiter
#   returns list of strings
    msg(ogdebug,"getting fields from string based on delimiter = {}".format(delim))
    if delim == "whitespace":
        delim = "[\s]+"                   # regular expression version
    if delim == "comma":
        delim = "[,]"   # regular expression version. no + so that empty fields are maintained
    stringlist = re.split(delim,mystring) # regular expression version
    msg(ogdebug,"stringtostringlist found {} fields".format(len(stringlist)))
    msg(ogdebug,"--list of fields:")
    msg(ogdebug,stringlist)
    return stringlist

def getslicelist(mystring,startend):
#    get sections of mystring beginning at character (or column) start
#    and ending with character (or column) end; return as new string.
#    startend is list of tuples, each with a start and end
#    [(start1,end1),(start2,end2),...]
#    Returns a list of the resulting string slices
    mylength = len(mystring)
    msg(ogdebug,"string has {} characters in getslicelist".format(mylength))
    myslices = []
    if mylength == 0: return myslices
    count = 0
    for (start,end) in startend:
        count += 1
        if end > len(mystring):     #short circuit if section too long
            msg(oginfo,"section {} too long in getslicelist".format(count))
            end = len(mystring)
            myslices.append(mystring[start:end+1])
            break
        myslices.append(mystring[start:end+1])
    msg(ogdebug,"--in getslicelist, captured slices = {}".format(myslices))
    return myslices

def getfielddic(mystring,fieldnameslist,delim="whitespace"):
#   split string into fields based on a regular expression delimiter
#   returns dictionary with keys = $field1, $field2, etc.
#   if fieldnameslist is defined correctly.

    fieldlist = stringtostringlist(mystring.strip())
    fieldnames = fieldnameslist[:len(fieldlist)]
#    msg(ogdebug,"--list of field names:")
#    msg(ogdebug,fieldnames)
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
#    msg(ogdebug,"--list of slice names:")
#    msg(ogdebug,slicenames)
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
    fieldnamebase = "$field"
    slicenamebase = "$slice"
    for i, mystring in enumerate(stringlist):
        if fieldnamebase in mystring:
            if mystring in fields:
                stringlist[i] = fields[mystring]
            else:
                 stringlist[i] = ""
        if slicenamebase in mystring:
            if mystring in slices:
                stringlist[i] = slices[mystring]
            else:
                 stringlist[i] = ""
    msg(ogdebug,"--in translatefields, final list of strings = {}".format(stringlist))
    return stringlist

def stringlistfromfields(fieldtypes,texts,slicetexts,fieldtexts,holdtexts=[]):
#   build a string from lists of fields of different types
#   separate the fields by delimiter to produce the string
#   fieldtypes list should contain the types corresponding to the different lists
#   The kinds of fields supported are: "text", "slice", "field", "hold"
#   The fields are held in lists texts, slicetexts, fieldtexts, holdtexts

    fieldcount = 0
    slicecount = 0
    textcount  = 0
    holdcount  = 0
    nfield = len(fieldtexts)
    nslice = len(slicetexts)
    ntext  = len(texts)
    nhold  = len(holdtexts)
    outstringlist = [] 
    for fieldtype in fieldtypes:
        if fieldtype == "text" and ntext > 0:
            if textcount <= ntext - 1:
                outstringlist.append(texts[textcount])
                textcount += 1
            else:
                msg(ogmain,"Ignoring text: only {} available.".format(ntext)) 
        if fieldtype == "slice" and nslice > 0:
            if slicecount <= nslice - 1:
                outstringlist.append(slicetexts[slicecount])
                slicecount += 1
            else:
                msg(ogmain,"Ignoring slice: only {} available.".format(nslice)) 
        if fieldtype == "field" and nfield > 0:
            if fieldcount <= nfield - 1:
                outstringlist.append(fieldtexts[fieldcount])
                fieldcount += 1
            else:
                msg(ogmain,"Ignoring field: only {} available.".format(nfield)) 
        if fieldtype == "hold" and nhold > 0:
            if holdcount <= nhold - 1:
                outstringlist.append(holdtexts[holdcount])
                holdcount += 1
            else:
                msg(ogmain,"Ignoring hold: only {} available.".format(nhold)) 

    
    return outstringlist


def combinequoted(inlist):
    """if a sequence of items in a list is preceded and followed by a double quote,
       combine the separate words between them into one. Looks for a double quotes
       by themselves (separated by space) or one at the beginning of one
       word and one (later) at the end of a word.
       e.g. "one two three" becomes one element as does " one two three ".
       The quotes are removed.
    """

    msg(ogdebug,"In combinequoted, initial tokens = {} ".format(inlist))

    mybegin = False
    myend   = False
    ibegin = -1
    iend   = -1
    quotechar = '"'
    msg(ogdebug,"In combinequoted, quotechar = {} ".format(quotechar))

#       find first double quote at beginning of list item
    for i,item in enumerate(inlist):
        if item.startswith(quotechar):
            mybegin = True
            ibegin = i
            break
#       find last double quote at end of list item
    for i,item in enumerate(inlist):
        if item.endswith(quotechar):
            myend = True
            iend  =  i 

    
    if mybegin: 
        msg(ogdebug,"In combinequoted, found token with beginning quote: {} ".format(inlist[ibegin]))
    if myend: 
        msg(ogdebug,"In combinequoted, found token with ending quote: {} ".format(inlist[iend]))

#       concatenate all items between quotes
    outlist = []
    newitem = ""
    if mybegin and myend and (iend > ibegin):
        inlist[ibegin] = inlist[ibegin][1:]
        inlist[iend] = inlist[iend][0:-1]
        for i in range(ibegin):
            outlist.append(inlist[i])
        for item in inlist[ibegin:iend]:
            newitem+= item + " "
        newitem+= inlist[iend]
        outlist.append(newitem)
        if len(inlist) > iend:
            for i in range(iend+1,len(inlist)):
                outlist.append(inlist[i])

        msg(ogdebug,"In combinequoted, final tokens = {} ".format(outlist))
        return outlist

    else:
        msg(ogdebug,"In combinequoted, no change to tokens because no pair of suitable quote characters")
        return inlist

def substitute(pattern,repl,instring,count=1):
#   substitute repl for pattern in instring count times (if there are that many)
#   return resulting string or None if no substitution occurred
    outstring=re.sub(pattern,repl,instring,count)
    if instring == outstring:
        outstring = None
        msg(oginfo,"no substitute performed in substitute.")
    else:
        msg(oginfo,"in substitute, replaced line")
        msg(ogdebug,"--old: \"{}\"".format(instring))
        msg(ogdebug,"--new: \"{}\"".format(outstring))
        
    return outstring

def matchnextcopy(infile,outfile,mystring,*,nfind=1,increment=0,nlines=1):
#   for nfind instances: find line in infile object with match string, go forward or backward increment lines,
#   (determined by sign of increment) and write nlines lines to outfile object.
#   uses matchnextreturn, but actually writes to outfile
    mylines = infile.matchnextreturn(mystring,nfind,increment,nlines)
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
    msg(ogverbose,"copying {} lines from input to output".format(nlines))
    mylines = infile.getlines(nlines)
    outfile.addlines(mylines)

def copyuntilmatch(infile,outfile,mystring,*,start=False,end=False):
#   copy all lines (exclusive of start and end by default) from current to line matching mystring
    msg(oginfo,"copying all lines until {} matched from input to output".format(mystring))
    mylines,endpos = infile.getuntilmatch(mystring,start=start,end=end)
    outfile.addlines(mylines)
    return endpos

def copysection(infile,outfile,start,end):
#   copy a section of input lines from line start to line end, inclusive
    msg(oginfo,"copying section ( {} to {} ) from input to output".format(start,end))
    mylines,endposition = infile.getsection(start,end)
    outfile.addlines(mylines)
    return endposition

def initializenameslist(namebase,maxnum):
#   produce list of names (for fields or slices etc.) to potentially be used later
#   e.g. if namebase = "$field", produce: ["$field1", "$field2",..]
#   maxnum should be larger than expected number of names required
    names = [namebase]*maxnum
    for i in range(maxnum):
        names[i] += str(i+1)
    return names

def parameterstartswithkey(param,default,mydict):
    """ Determine if any of the keys in a dictionary are a shortened form of 
        an input string. (e.g. key ~ "dir" and string = "direction")
        If they are, return value corresponding to key, otherwise, return default
    """ 

    returnvalue = default
    for key,value in mydict.items():
        if param.startswith(key):
            returnvalue = value
            break
    return returnvalue

def removesubstring(mystring,substring,occurrence=1):
    """ find the nth occurrence of substring in string and remove it
    """
    nfound = 0
    position = 0
    while True:
        idx = mystring.find(substring,position)
        if idx >= 0:
            nfound += 1
            position = idx + len(substring)
            if nfound == occurrence:
                newstring = mystring[:idx] + mystring[position:] 
                return newstring
        else:
            msg(ogmain,"In removesubstring, {} occurrences of {} not found".format(occurrence,substring))
            return mystring
    
def replacesubstring(mystring,substring,replacement,occurrence=1):
    """ find the nth occurrence of substring in string and remove it
    """
    nfound = 0
    position = 0
    while True:
        idx = mystring.find(substring,position)
        if idx >= 0:
            nfound += 1
            position = idx + len(substring)
            if nfound == occurrence:
                newstring = mystring[:idx] + replacement + mystring[position:] 
                return newstring
        else:
            msg(ogmain,"In replacesubstring, {} occurrences of {} not found".format(occurrence,substring))
            return mystring
        

class InternalFile:
#   Base class for internal representation of files

    def __init__(self):
        self.lines = []
        self.length = 0
        self.names = []
        self.type = "InternalFile"
        msg(ogdebug,"initializing empty InternalFile")

    def checkstartposition(self,start):
#       if position is before begin of file, set to to begin of file and report
        if start < 0:
            start = 0
            msg(ogdebug,"position past beginning of file, reset to first line")
        return start

    def checkendposition(self,end):
#       if position is past end of file, set to end of file and report
        if end >= self.length:
            end = self.length - 1
            msg(ogdebug,"position past end of file, reset to end")
        return end
    
    def addblankline(self):
        self.lines.append("")
        self.length += 1

    def writefile(self,fileh=sys.stdout):
#   write the in-memory file object to file (default stdout)
        msg(oginfo,"writing {} file {}".format(self.type,self.names))
        msg(oginfo,"-----------------------------------------------")
        for line in self.lines:
            print(line,file=fileh)
        msg(ogmain,"finished writing")

class OutputFile(InternalFile):
#   Output file is list of lines (usually) eventually to be sent to stdout

    def __init__(self):
        InternalFile.__init__(self)
        self.type = "OutputFile"
        addfilename(self,"output")
        msg(ogdebug,"Initializing output file.")
        msg(ogdebug,"Names = {}".format(self.names))

    def addline(self,mystring,printblank=False):
#   add mystring as new line at end of file
        if mystring == "" or mystring == None:
            if not printblank:
                msg(ogdebug,"-- not adding blank line in addline")
                return
        else:
            msg(ogdebug,"--adding line \"{}\" to {} file {}".format(mystring,self.type,self.names))
            self.lines.append(mystring)
            self.length += 1

    def addlines(self,mylines,printblank=False):
#   add mylines as new lines at end of output file
        if mylines == [] and not printblank:
            msg(ogdebug,"-- not adding empty lines in addlines")
            return
        else:
            msg(ogdebug,"--adding lines \"{}\" to {} file {}".format(mylines,self.type,self.names))
            self.lines.extend(mylines)
            self.length += len(mylines)

    def joinlastlines(self,joiner=""):
#       join last two lines of output file,
#       assign the result to the next-to-last line and
#       delete the last line.

        msg(ogdebug,"In joinlastlines, file length = {}:".format(self.length))
        msg(ogdebug,"Last two lines are:")
        msg(ogdebug,"{}".format(self.lines[-2]))
        msg(ogdebug,"{}".format(self.lines[-1]))
        self.lines[-2] = self.lines[-2] + joiner + self.lines[-1]
        msg(ogdebug,"New line is: {}".format(self.lines[-2]))
        del self.lines[-1]
        self.length = len(self.lines)
        msg(ogdebug,"In joinlastlines, file length = {}:".format(self.length))
        self.current = self.length - 1

    def switchlastlines(self):
#       switch last two lines of output file,
        msg(ogdebug,"In switchlastlines, file length = {}:".format(self.length))
        msg(ogdebug,"Last two lines are:")
        msg(ogdebug,"{}".format(self.lines[-2]))
        msg(ogdebug,"{}".format(self.lines[-1]))
        self.lines[-2],self.lines[-1] = self.lines[-1],self.lines[-2]
        msg(ogdebug,"Last two lines are:")
        msg(ogdebug,"{}".format(self.lines[-2]))
        msg(ogdebug,"{}".format(self.lines[-1]))
        msg(ogdebug,"In switchlastlines, file length = {}:".format(self.length))

    def replacelastline(self,newtext):
#       replace the last line with some new text
        msg(ogdebug,"In replacelastline before replacement, last line is:")
        msg(ogdebug,"{}".format(self.lines[-1]))
        self.lines[-1] = newtext
        msg(ogdebug,"In replacelastline after replacement, last line is:")
        msg(ogdebug,"{}".format(self.lines[-1]))


class InputFile(InternalFile):
# InputFile is object holding an input file

    def __init__(self,content,start=None,end=None):    # fh is a filehandler object or a list of strings
        InternalFile.__init__(self)
        self.type = "InputFile"
        if isinstance(content,list):
            self.loadinputfilefromstringlist(content,start,end)
        elif isinstance(content,str):
            contentlist = []
            contentlist.append(content)
            self.loadinputfilefromstringlist(contentlist,start,end)
        else:
            self.getinputfile(content,start,end)
            msg(ogmain,"reading {}".format(content.name))
        self.initializepositions()
        self.fieldnameslist = initializenameslist("$field",100)
        self.slicenameslist = initializenameslist("$slice",100)
        self.holdnameslist  = initializenameslist("$hold",100)
 
    def loadinputfilefromstringlist(self,mystringlist,start=None,end=None):
#       Alternative to getinputfile: assign all or part of mystringlist as the content
#       of an InputFile object
        if end is None:
            if start is None:  # no start and no end specified: read entire file
                self.lines=[x.rstrip() for x in mystringlist]
            else:              # start given: read from "start" to EOF
                self.lines=[x.rstrip() for i,x in enumerate(mystringlist) if i>=start]
        else:                  # end is given: read up to "end"
            if start is None:  # read from start to "end"
                self.lines=[x.rstrip() for i,x in enumerate(mystringlist) if i<=end]
            else:              # both given: read from "start" to "end"
                self.lines=[x.rstrip() for i,x in enumerate(mystringlist) if i>= start and i<=end]

        self.length = len(self.lines)

    def getinputfile(self,fh,start=None,end=None):
#   fh is a filehandler object. If fh == 0 or None, do nothing
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

        self.length = len(self.lines)

    def initializepositions(self):
#   define standard locations within the file
#   define a dictionary to hold them and any remembered positions
#   initialize current to first line of file
        self.current=0
        self.positions = {}
        self.positions["current"] = self.current
        self.positions["top"] =     0
        self.positions["bottom"] =  self.length - 1
            
        self.reserved_positions = ["top","bottom"]

    def updatecurrent(self,newline):
#   set the current line to newlineno
#   or to begin or end of file if newlineno is past one of those
        self.current = self.interpretposition(newline)
        self.positions["current"] = self.current
        return self.current

    def goto(self,myposition):
#   set current line to myposition; this is now just a synonym for update current
        return self.updatecurrent(myposition)

    def interpretposition(self,myposition):
#       convert named positions to line numbers etc.
        if isinstance(myposition,str):
           try:             # case where myposition is a string version of a number
               myposition = int(myposition)
           except:
               myposition = self.positions[myposition]
        elif isinstance(myposition,int):
           pass 
        else:
           msg(ogmain,"stopping: position must be string (label) or integer (line no.)")
           sys.exit("stopping: position must be string (label) or integer (line no.)")

        myposition = self.checkstartposition(myposition)
        myposition = self.checkendposition(myposition)

        return myposition

    def interpretpositionpair(self,start,end):
#   set defaults for starting and ending lines if start and/or end missing
        if start is None:     start = 0
        if end   is None:     end = self.length - 1
        start = self.interpretposition(start)
        end   = self.interpretposition(end)
        return start,end

    def step(self,increment=1):
#   go forward increment number of lines (increment=1 => goto next line)
#   if increment < 0, go backwards
        newlineno = self.current + increment
        result = self.updatecurrent(newlineno)
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
        msg(oginfo,"--remembering current line as {}".format(myposition))
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
        msg(oginfo,"printing current line to stout (not to OutputFile)")
        print(self.lines[self.current])

    def getline(self):
#   return the current line
        return self.lines[self.current]

    def getlines(self,nlines):
#   return nlines lines including current line
        myend = self.interpretposition(self.current+nlines)
        return self.lines[self.current:myend]

    def getsection(self,start,end):
#   return lines from start to end, inclusive
        mystart = self.interpretposition(start)
        myend = self.interpretposition(end)
        return self.lines[mystart:myend+1],myend

    def getuntilmatch(self,mystring,*,start=False,end=False):
#   starting from the current line, return all lines up to
#   first line that matches mystring. Exclusive of start and end,
#   unless start = True and/or end = True
        
        if start:
            startpos = self.current
        else:
            startpos = self.current + 1
        self.match(mystring,nfind=1,dir=1)
        if end:
            endpos = self.current
        else:
            endpos = self.current - 1
        return self.getsection(startpos,endpos)   #returns the lines and the ending position?

    def getfields(self,delim="whitespace"):
#   split (on delimiter) the current line into fields and return them as a dictionary
#   with keys $field1, $field2, etc. defined in fieldnameslist
        return getfielddic(self.lines[self.current],self.fieldnameslist,delim)

    def getslices(self,startend):
#   return slices from current line based on startend (see getsliceslist)
#   e.g.:to get columns 2-5 as $slice1 and 8-13 as $slice2, startend = [(2,5),(8,13)]
        return getslicedic(self.lines[self.current],self.slicenameslist,startend)

    def match(self,mystring,*,nfind=1,dir=1):
#   starting with current line, search, in dir direction (dir<=0:up, dir>0:down)
#   for nfind lines containing mystring and set current line at the last one

        dir = int(dir)
        mystart = self.current
        if dir >= 0:
            dir = 1
            myend = self.length
        else:
            dir = -1
            myend = -1
        msg(ogdebug,"--in match, dir= {}".format(dir)) 
        msg(ogdebug,"--in match, searching for \"{}\" from line {} to {}".format(mystring,mystart,myend-1)) 
        nfound = 0
        self.matchflag = False
        msg(ogdebug,"--in match, setting matchflag to {}".format(self.matchflag)) 
        for lineno in range(mystart,myend,dir):
            searchObj = re.search(mystring,self.lines[lineno])
            if searchObj:
                nfound += 1
                self.goto(lineno) 
                msg(oginfo,"found {} match of \"{}\" out of {} on line {}:".format(nfound,mystring,nfind,lineno))
                msg(oginfo,self.lines[lineno])
                msg(ogverbose,"found returned search object \"{}\"".format(searchObj))
                if nfind == nfound:
                    self.matchflag = True
                    msg(ogdebug,"--in match, setting matchflag to {}".format(self.matchflag)) 
                    return nfind
            elif mystart != self.length - 1 and lineno == self.length -1:
                self.matchflag = False
                msg(ogdebug,"--in match, setting matchflag to {}".format(self.matchflag)) 
                msg(oginfo,"reached end of file during match.")
                msg(oginfo,"found only {} out of {} matches of \"{}\"".format(nfound,nfind,mystring)) 
                self.goto(self.length - 1)
                return -1
            elif mystart != 0 and lineno == 0:
                self.matchflag = False
                msg(ogdebug,"--in match, setting matchflag to {}".format(self.matchflag)) 
                msg(oginfo,"reached beginning of file during match.")
                msg(oginfo,"found only {} out of {} matches of \"{}\"".format(nfound,nfind,mystring)) 
                self.goto(0)
                return -1

        return 0

    def matchnextreturn(self,mystring,nfind=1,increment=0,nlines=1):
#   for nfind instances: find match string, go forward or backward increment lines,
#   (determined by sign) and return nlines lines.
#   The next operates forward or backward,
#   but searches and captures only in positive direction.
#   Default is search for mystring once, and return the line containing the match.
#   Note the special value for nfind: "all": searches the entire file

        if nfind == "all":
            nfind = self.length

        mylines = []
        for i in range(nfind):
            result = self.match(mystring,nfind=1,dir=1)
            if result == 0: 
                msg(oginfo,"match {} of \"{}\" not found in matchnextreturn.".format(i+1,mystring))
                break
            elif result == -1: 
                msg(oginfo,"reached end or begin of file in matchnextreturn") 
                break
            elif result < -1:
                msg(oginfo,"something weird in match called from matchnextreturn") 
                break                
            if self.current + nlines <= self.length: 
                if increment == 0 and nlines == 1:
                    mylines.append(self.getline())
                    self.step(nlines)
                else:
                    self.step(increment)
                    mylines.extend(self.getlines(nlines))
                    self.step(nlines)
            else:
                msg(oginfo,"Not enough lines in file for return section in matchnextreturn".format(i+1))
                mylines.append(self.getlines(nlines))
                result = self.step(nlines)
                break 

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
        msg(oginfo,"deleting input from line {} to line {} in {} ".format(start,end,self.names))
        del self.lines[start:end+1]
        if len(self.lines) == 0:
            self.lines.append("")
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
        msg(oginfo,"resetting current position to top of file")
        self.updatecurrent(0)
        msg(oginfo,"resetting \"top\" and \"bottom\" remembered labels")
        self.length = len(self.lines)
        self.positions["top"] =     0
        finalline = self.lines[self.length - 1]
        if finalline == "":
            self.positions["bottom"] =  self.length - 2  # assume xtra blank line is there
        else:
            self.positions["bottom"] =  self.length - 1  # assume xtra blank line is not there
        return

class ScratchFile(InputFile,OutputFile):
#   A Scratchfile has the methods and attributes of both InputFile and OutputFile
#   It can be added to, removed from, and has named line labels
#   Initialize lt as an InputFile. Just use a blank string if nothing else.

    def __init__(self,content,start=None,end=None):
        InputFile.__init__(self,content,start,end)
        self.type = "ScratchFile"
        addfilename(self,"scratch")
        msg(ogdebug,"Initializing scratch file.")
        msg(ogdebug,"Names = {}".format(self.names))

    def addline(self,mystring,printblank=False):
#   add mystring as new line at end of file
#   ScratchFile version: update positions
        if mystring == "" or mystring == None:
            if not printblank:
                msg(ogdebug,"-- not adding blank line in addline")
                return
        else:
            msg(ogdebug,"--adding line \"{}\" to {} file {}".format(mystring,self.type,self.names))
            self.lines.append(mystring)
            self.length += 1
            self.current += 1
            self.positions["bottom"] = self.current

    def addlines(self,mylines,printblank=False):
#   add mylines as new lines at end of output file
#   ScratchFile version: update positions
        if mylines == [] and not printblank:
            msg(ogdebug,"-- not adding empty lines in addlines")
            return
        else:
            msg(ogdebug,"--adding lines \"{}\" to {} file {}".format(mylines,self.type,self.names))
            self.lines.extend(mylines)
            self.length += len(mylines)
            self.current += len(mylines)
            self.positions["bottom"] = self.current


class ProgramFile(InputFile):
#   A ProgramFile is an Inputfile with added methods so that it can be interpreted
#   as an outgrab program file
#   self.infile is the internal file that the outgrab program operates on
#   and self.outfile is the file to be written.
#   They must be set by an outside program

    def __init__(self,fh,start=None,end=None):
        InputFile.__init__(self,fh,start=None,end=None)
        self.type = "ProgramFile"
        self.infile = ""
        self.nestlevel = -1
        self.loopmaxiter = []
        self.loopiter = []
        self.looplabel = []
        self.matchflag = False
        self.execute  = True
        self.ifmatchlevel = -1
        self.holddic = {}

    def setinputfile(self,infile):
        self.infile = infile

    def setoutputfile(self,outfile):
        self.outfile = outfile

    def insertfile(self,filename,overwrite=True):
        """Open an outgrab program file and insert it
           into the currently processing outgrab program 
           either in place of the current line
           (overwrite = True, the default) or
           after the current line (overwrite = False).
        """

        msg(ogverbose,"inserting program file: {} ".format(filename))
        with open(filename, "r") as f:
            mylines = [x.rstrip().lstrip() for x in f]

            for thing in mylines:
                msg(ogdebug," line = {} ".format(thing))

            if overwrite:
                lineadjust = 0
            else:
                lineadjust = 1
            self.lines = ( self.lines[:self.current+lineadjust]
                         + [" "]   # insert blank line to ensure first line of new program lines executed
                         + mylines[:]
                         + self.lines[self.current+1:] )
            
        self.length = len(self.lines) 
        self.positions["bottom"] =  self.length - 1
        self.current = self.current + lineadjust
        self.positions["current"] = self.current

    def processcommands(self,comments=["#","!"]):
        """process commands in this file; translate them to the outgrab methods
           ignore comment lines beginning with any character in comments
           and strip off any whitespace from beginning or end of line
        """

        msg(ogmain,"The files known at the start of processing commands:")
        samevalueslist = listofsamevaluekeys(ifilesd)
        for item in samevalueslist:
            printline = "    "
            for key in item[:-1]:
                printline += key + " = " 
            printline += item[-1]
            msg(ogmain,printline)

        maxlastlinecount = 10
        lastlinecount = 0

        countline = 0
        while True:
            line = self.getline()
            line = line.rstrip().lstrip()
            countline +=1
            msg(ogdebug,"In processcommands at start, matchflag, execute: {}, {}".format(self.matchflag,self.execute))

            if self.interpretposition(self.current) >= self.interpretposition("bottom"):
                lastlinecount +=1
                msg(ogdebug,"Processing command at bottom of program file")

            if lastlinecount >= maxlastlinecount:
                msg(ogmain,"At end of program file for {} steps. Finishing processing outgrab commands."
                .format(lastlinecount))
                msg(ogmain,"-------------------------------------------------")
                break
             
            if line:
                msg(ogdebug,"*******processing outgrab file line {}*********************************".format(countline))
                iscomment = False 
                for comment in comments:
                    if line.startswith(comment):
                        msg(ogdebug,"Found a comment: {} ".format(line))
                        self.step()
                        iscomment = True
                        break
                if not iscomment:
                    if line.startswith("exit"):
                        msg(ogmain,"Exit found: finished processing outgrab commands.")
                        msg(ogmain,"-------------------------------------------------")
                        break
                    else:
                        msg(ogdebug,"Processing command:")
                        msg(ogdebug," ")
                        msg(ogdebug,"{} ".format(line))
                        msg(ogdebug," ")
                        self.processcommand(line) 
                        msg(ogdebug,"In processcommands, after processcommand: matchflag, execute: {}, {}".format(self.matchflag,self.execute))
                        self.step()
            else:
                # blank line
                self.step()
             
    def processcommand(self,myline):
        """split the command up into the command itself and its keyword arguments
        """

#       split outgrab command into tokens/parts; first is command
#       e.g.  match thistext direction -1
        msg(ogdebug,"In processcommand at start, matchflag, execute: {}, {}".format(self.matchflag,self.execute))

        tokens = stringtostringlist(myline,delim="whitespace")
        msg(ogdebug,"In processcommand, tokens: {} ".format(tokens))

#       capture the command
        command = tokens[0]

        self.interpretcommand(command,tokens)

    def getargs(self,tokens,style):
#        convert tokens into arguments based on style of command
#       style = comargdict: line is the command, then a first argument, then some name, parameter pairs
#       style = comargs:    line is the command followed by a list of parameters


#       manage double qouted strings: combine if preceded and followed by double quotes
        tokens = combinequoted(tokens)
        
        ntokens = len(tokens)
        if style == "comargdict":
            arg1 = ""
            if ntokens >= 2:
                arg1 = tokens[1]

#           capture the others in name, arg pairs
            kwargs = {}
            if ntokens >= 3:
                lname = True
                for thing in tokens[2:]:
                    if lname:
                        myname = thing
                        lname = False
                    else:
                        myarg = thing
                        lname = True
                        kwargs[myname] = myarg

            msg(ogdebug,"In getargs , kwargs =: {} ".format(kwargs))
            return arg1,kwargs

        elif style == "comargs":
            args = tokens[1:]
            return args

    def processfields(self,args,mytext,holddic=[]):
#       for use by dumpfields and related commands
#       args are the arguments to that command
#       mytext is the inputfile line the commands operate on
#       command line as a string.
#       produce lists of different kinds of fields from a command line
#       texts: simple text strings
#       fields: words delimited by the delimiter
#       slices: e.g. 4:21 for characters 4 - 21 from the input line
#       holds: fields of all types stored previously: passed in thru holddic

        msg(ogdebug,"In process fields, the original line:\n {}".format(mytext))
        fieldtypes = []
        slicesplitter = ":"
        fieldbase = "$field"
        holdbase  = "$hold"
        slicedef = []
        fielddef = []
        holddef  = []
        fieldtexts = []
        holdtexts  = []
        texts = []
        for arg in args:
            msg(ogdebug,"looking at argument: {} ".format(arg))
            if slicesplitter in arg:
                start,end = arg.split(slicesplitter)
                try:
                    start = int(start) - 1
                    end   = int(end) - 1
                    fieldtypes.append("slice")
                    slicedef.append((start,end))
                    msg(ogdebug,"assigning argument {} to slice ".format(arg))
                except:            # take care of the case where ":" in a text field
                    texts.append(arg)
                    fieldtypes.append("text")
                    msg(ogdebug,"assigning argument {} to text".format(arg))
            elif fieldbase in arg:
                fielddef.append(arg)
                fieldtypes.append("field")
                msg(ogdebug,"assigning argument {} to field".format(arg))
            elif holdbase in arg:
                holddef.append(arg)
                fieldtypes.append("hold")
                msg(ogdebug,"assigning argument {} to hold".format(arg))
            else:
                texts.append(arg)
                fieldtypes.append("text")
                msg(ogdebug,"assigning argument {} to text".format(arg))
    #           create lists of the slices and fields
        slicetexts = getslicelist(mytext,slicedef)
        fielddic   = getfielddic(mytext,self.fieldnameslist)
        for field in fielddef:
            try:
                fieldtexts.append(fielddic[field]) 
            except:
                msg(ogmain,"problem with field {} ".format(field))
        for hold in holddef:
            try:
                holdtexts.append(holddic[hold]) 
            except:
                msg(ogmain,"problem with hold {} ".format(field))
     
        msg(ogdebug,"texts found: {} ".format(texts))
        msg(ogdebug,"fielddef: {} ".format(fielddef))
        msg(ogdebug,"fieldtypes: {} ".format(fieldtypes))
        msg(ogdebug,"fieldtexts found: {} ".format(fieldtexts))
        msg(ogdebug,"slicedef: {} ".format(slicedef))
        msg(ogdebug,"slicetexts found: {} ".format(slicetexts))
        msg(ogdebug,"holddef: {} ".format(holddef))
        msg(ogdebug,"holdtexts found: {} ".format(holdtexts))

        return fieldtypes,texts,slicetexts,fieldtexts,holdtexts

    def updatemsg(self,command):
            msg(ogverbose,"____________________________________________")
            msg(ogverbose,"After command: {}, line # = {}, line =  ".format(command,self.infile.current))
            msg(ogverbose,"{}".format(self.infile.lines[self.infile.current]))
            msg(ogverbose,"____________________________________________")

    def interpretcommand(self,command,tokens):
        """ Translate an outgrab command into calls to outgrab_tools methods
        """
        msg(ogdebug,"In interpretcommand, matchflag, execute: {}, {}".format(self.matchflag,self.execute))


        if command == "include":
            args = self.getargs(tokens,"comargs")
            self.insertfile(args[0],overwrite=True)
            self.updatemsg(command)
            return

        if command == "match" and self.execute:        
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            nfind    = int(kwargdict.get("nfind",1))
            dir = parameterstartswithkey("direction",1,kwargdict)
            dir = int(dir) 
            self.infile.match(arg1,nfind=int(nfind),dir=dir)
            self.matchflag = self.infile.matchflag
            self.updatemsg(command)

        elif command == "ifmatch":
            kwargdict = {}
            self.ifmatchlevel += 1
            msg(ogdebug,"In interpretcommand (ifmatch), matchlevel: {}".format(self.ifmatchlevel))
            if self.ifmatchlevel > 1:
                sys.exit("stopping: no nested ifmatch/ifnomatch allowed")
            self.execute = self.matchflag
            msg(ogdebug,"In interpretcommand (ifmatch), matchflag, execute: {}, {}".format(self.matchflag,self.execute))
            self.updatemsg(command)

        elif command == "ifnomatch":
            kwargdict = {}
            self.ifmatchlevel += 1
            msg(ogdebug,"In interpretcommand (ifnomatch), matchlevel: {}".format(self.ifmatchlevel))
            if self.ifmatchlevel > 1:
                sys.exit("stopping: no nested ifmatch/ifnomatch allowed")
            self.execute = not self.matchflag
            msg(ogdebug,"In interpretcommand (ifnomatch), matchflag, execute: {}, {}".format(self.matchflag,self.execute))
            self.updatemsg(command)

        elif command == "endifmatch" or command == "endif":
            kwargdict = {}
            self.ifmatchlevel -= 1
            msg(ogdebug,"In interpretcommand (endifmatch), matchlevel: {}".format(self.ifmatchlevel))
            self.execute = True
            msg(ogdebug,"In interpretcommand (endifmatch), matchflag, execute: {}, {}".format(self.matchflag,self.execute))
            self.updatemsg(command)

        elif (command == "next" or command == "step") and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            if arg1:
                self.infile.step(increment=int(arg1))
            else:
                self.infile.step(increment=1)
            self.updatemsg(command)

        elif command == "back" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            if arg1:
                self.infile.back(int(arg1))
            else:
                self.infile.back(increment=1)
            self.updatemsg(command)

        elif command == "remember" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            self.infile.remember(arg1)
            self.updatemsg(command)

        elif command == "forget" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            self.infile.forget(arg1)
            self.updatemsg(command)

        elif command == "setverbosity" and self.execute:
            args = self.getargs(tokens,"comargs")
            verbosity = int(args[0])
            myloglevel = setverbositylevels(verbosity,verbosity_default=2)
#           Note that running logging.basicConfig a 2nd time does nothing
#           must run setLevel instead to reset verbosity/loglevel
            logging.getLogger().setLevel(myloglevel)
            msg(ogmain,"Resetting verbosity to {} ".format(verbosity))
            self.updatemsg(command)

        elif command == "dumpline" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            copyline(self.infile,self.outfile)
            self.infile.step(increment=1)
            self.updatemsg(command)

        elif command == "dumplines" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            if not arg1: arg1 = 1
            copylines(self.infile,self.outfile,int(arg1))
            self.infile.step(increment=int(arg1))
            self.updatemsg(command)

        elif command == "dumpsection" and self.execute:
            args = self.getargs(tokens,"comargs")
            endpos = copysection(self.infile,self.outfile,args[0],args[1])
            self.infile.goto(endpos)
            self.infile.step(increment=1)
            self.updatemsg(command)

        elif command == "dumpuntilmatch" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            start = kwargdict.get("start",False)
            end   = kwargdict.get("end",False)
            if start in ["True","true","T","t","yes","Yes"]: start = True
            if end   in ["True","true","T","t","yes","Yes"]: end   = True
            endpos = copyuntilmatch(self.infile,self.outfile,arg1,start=start,end=end)
            self.infile.goto(endpos)
            self.infile.step(increment=1)
            if not end: self.infile.step(increment=1)
            self.updatemsg(command)

        elif command == "switchinputto" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            x = getfilefromname(arg1)
            self.setinputfile(x)
            self.updatemsg(command)

        elif command == "switchoutputto" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            x = getfilefromname(arg1)
            self.setoutputfile(x)
            self.updatemsg(command)

        elif command == "setoutputfilename" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            self.setfilename(self.output,arg1)
            self.updatemsg(command)

        elif command == "setinputfilename" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            self.setfilename(self.input,arg1)
            self.updatemsg(command)

        elif command == "empty" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            if arg1:
                x = getfilefromname(arg1)
                x.empty()
                msg(ogmain,"Emptying file {} ".format(arg1))
            else:
                msg(ogmain,"Ignoring 'empty' command: must specify file to empty.")
            self.updatemsg(command)

        elif command == "goto" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            self.infile.goto(arg1)
            self.updatemsg(command)

        elif command == "writefile" and self.execute:
            arg1,arg2 = self.getargs(tokens,"comargs")
            if arg1:
                x = getfilefromname(arg1)
            else:
                x = getfilefromname("output")
            fh = open(arg2,"w")
            x.writefile(fh)
            self.updatemsg(command)

        elif command == "readinput" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            filenum = getnextfilenum()
            readinputfile(arg1,filenum)
            self.updatemsg(command)

        elif command == "print" and self.execute:
            args = self.getargs(tokens,"comargs")
            self.outfile.addline(" ".join(args))
            self.updatemsg(command)
            
        elif command == "joinlast" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            if not arg1: arg1 = ""
            self.outfile.joinlastlines(arg1)
            self.updatemsg(command)

        elif command == "switchlast" and self.execute:
            self.outfile.switchlastlines()
            self.updatemsg(command)

        elif command == "remove":
            args = self.getargs(tokens,"comargs")
            substring = args[0]
            if len(args) > 1:
                occurrence = int(args[1])
            else:
                occurrence = 1
            mytext = self.outfile.lines[-1]
            mytext = removesubstring(mytext,substring,occurrence)
            self.outfile.replacelastline(mytext)
            self.updatemsg(command)
            
        elif command == "replace":
            args = self.getargs(tokens,"comargs")
            substring = args[0]
            replacement = args[1]
            if len(args) > 2:
                occurrence = int(args[2])
            else:
                occurrence = 1
            mytext = self.outfile.lines[-1]
            mytext = replacesubstring(mytext,substring,replacement,occurrence)
            self.outfile.replacelastline(mytext)
            self.updatemsg(command)

        elif command == "matchnextdump" and self.execute:
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            nfind = parameterstartswithkey("nfind",1,kwargdict)
            if nfind == "all":
                pass
            else:
                nfind = int(nfind)
            increment = int(parameterstartswithkey("increment",0,kwargdict))
            nlines =    int(parameterstartswithkey("nlines",1,kwargdict))
            matchnextcopy(self.infile,self.outfile,arg1,nfind=nfind,increment=increment,nlines=nlines)
            self.updatemsg(command)

        elif command == "dumpfields" and self.execute:
            args = self.getargs(tokens,"comargs")
            mytext = self.infile.getline()
            fieldtypes,texts,slicetexts,fieldtexts,holdtexts = self.processfields(args,mytext,self.holddic)
            outputstringlist = stringlistfromfields(fieldtypes,texts,slicetexts,fieldtexts,holdtexts)
            outputstring = stringlisttostring(outputstringlist,delim=" ")
            if outputstring:
                msg(ogdebug,"The line to be added: {} ".format(outputstring))
                self.outfile.addline(outputstring) 
            self.infile.step(increment=1)
            self.updatemsg(command)

        elif command == "holdfields" and self.execute:
            args = self.getargs(tokens,"comargs")
            mytext = self.infile.getline()
            fieldtypes,texts,slicetexts,fieldtexts,holdtexts = self.processfields(args,mytext,self.holddic)
            holdtexts = stringlistfromfields(fieldtypes,texts,slicetexts,fieldtexts)
            self.holddic = dict(zip(self.holdnameslist,holdtexts))
            msg(ogdebug,"Texts to be held from this line: {} ".format(holdtexts))
            msg(ogdebug,"holddic: {} ".format(self.holddic))
            self.updatemsg(command)

        elif command == "break" and self.execute:
            if self.ifmatchlevel >= 0:
                if self.nestlevel >= 0:
                    self.match("endrepeat")
                    self.ifmatchlevel -= 1
                    self.execute = True
                    self.match = False
                else:
                    sys.exit("break command must be executed inside repeat loop")
            else:
                sys.exit("break command must be executed inside ifmatch or ifnomatch")

        elif  command == "repeat" and self.execute:
#           loop: repeat sequence of commands from this line to "endrepeat" arg1 times
            arg1,kwargdict = self.getargs(tokens,"comargdict")
            arg1 = int(arg1)
            self.nestlevel += 1
            self.loopmaxiter.append(arg1)
            msg(ogdebug,"Found repeat. nestlevel = {}, maxiter = {} ".format(self.nestlevel,arg1))
            self.loopiter.append(1)
            mylooplabel = "loop_" + str(self.nestlevel)
            self.looplabel.append(mylooplabel)
            self.remember(mylooplabel) # label the line after the repeat

        elif (command == "endrepeat"):
            if self.execute:
                if self.loopiter[self.nestlevel] >= self.loopmaxiter[self.nestlevel]:
                    msg(ogdebug,"Reached endrepeat. nestlevel = {}, iter = {}, maxiter = {} "
                                .format(self.nestlevel,self.loopiter[self.nestlevel],self.loopmaxiter[self.nestlevel]))
#                   finished with this loop
                    self.loopmaxiter.pop() 
                    self.loopiter.pop() 
#                   forget looplabel....
                    self.forget(self.looplabel[self.nestlevel])
                    self.looplabel.pop()
                    self.nestlevel -= 1
                else:
                    msg(ogdebug,"Reached endrepeat. nestlevel = {}, iter = {}, maxiter = {} "
                                 .format(self.nestlevel,self.loopiter[self.nestlevel],self.loopmaxiter[self.nestlevel]))
                    self.loopiter[self.nestlevel] +=1 
                    self.goto(self.looplabel[self.nestlevel])
                
        elif not self.execute:
            msg(ogmain,"Not executing command {} near line {} in Program {}: within ifmatch "
                       .format(command,self.current,self.names))

        elif command != "include":
            msg(ogmain,"Command {} near line {} in Program {} is not a valid outgrab command"
                       .format(command,self.current,self.names))
            ifkwargdict: msg(ogmain,"Arguments found: {} ".format(kwargdict))
            sys.exit("Command {} near line {} in Program {} is not a valid outgrab command"
                       .format(command,self.current,self.names))

"""
=======================================================
Outgrab command language
=======================================================

Each command statement is a command name followed by zero or more arguments or parameters.
The argument syntax is one of two types:
1. a list of position-specific parameters (usually just one)
2. a first position-specific parameter, followed by a list of name, value pairs
e.g., "match energy nfind 3" is the command "match" followed by the a first
argument "energy" (which is the word to match), followed by a parameter pair with
name "nfind" and value "3"; the number of matches to find.
All named parameters have a default value and are optional.
Two more more words can be combined into one argument or parameter
by surrounding with double quotes, for simple text to be printed,
this is not usually necessary. Don't put double quotes around a single word.

Almost no punctuation is needed or allowed; each statement is a sequence of words or numbers
All leading or trailing whitespace is ignored
Anywhere a position is required, you can use an absolute line number,
but this is not usually necessary or recommended. Instead use
a label.  At initialization, labels are created for the beginning of the file
(top) and the end of the file (bottom)
top and bottom are reserved and should always be valid.
# or ! at the beginning of a line lead to it being ignored as a comment

A simple outgrab program is:

    match energy    (search through the input lines until finding one containing "energy")
    next 2          (step to the next line and then to the next)
    dumplines 4     (send that line and the next 3 to the output, then set focus to the next line)

What if you wanted to do this three times?

    repeat 3
        match energy
        next 2
        dumplines 4
    endrepeat
 
That loop can be replaced with the single line program:
    matchnextdump "energy" nfind 3 increment 2 nlines 4

matchnextdump has one advantage: if you specify nfind to be greater than
the number of possible matches in the input file, matchnextdump will only
print out those that exist, while the repeat loop will fall to the bottom
of the input file and then print out the last line of the file
for each repeat iteration above the number of matches that actually exist.
You can avoid this behavior using ifmatch, ifnomatch, and break:
    repeat 3
        match energy
        ifmatch
          next 2
          dumplines 4
        endifmatch
        ifnomatch
           break
        endifmatch
    endrepeat

Regular expressions can be very useful.
For example, to print out 3 lines containing "Energy" or "energy",
you can do:
matchnextdump [E|e]nergy nfind 3
The regular expressions syntax is that used by Python.

=======================================================
Common Arguments or Parameters:
=======================================================
increment     = (integer); number of lines to move forward or back (<0 => back)
find          = (string or regular expression); The string or re to match or find 
nfind         = (integer); number of matches to find 
label         = (string); A label to assign to a position in a file (using remember/forget)
nlines        = (integer); number of lines to return
position      = (integer or string) either a line number (0:) or a label
direction     = (integer) -1 or 1 for searching or moving back or forward

=======================================================
Commands:
=======================================================

=======================================================
Commands for moving around the input file
=======================================================
match         (find)          (find next line that matches find and set focus there)
next or step  (increment)     (go forward increment lines; default 1; can be negative)
back          (increment)     (go backward increment lines; default 1; back n = next -n)
remember      (label)         (assign label to current line)	
forget        (label)         (erase label; not usually necessary)
goto          (position)      (set current line to position (line number or a previously defined label)
Note that: next, back, goto  update the "state" or the current line number to the one indicated
match                        updates the "state" or the current line number to the first one containing the match
commands with "dump" in them update the current line number to that just after the last line dumped 
other commands do not normally change the current line of the input file

=======================================================
Commands for dumping (copying) information from the input file to the output file
         or sending new text to the output file
=======================================================
dumpline                      (send current line to output and set input focus to next line)
dumplines     (nlines)        (send nlines to output, starting with current and set input focus to next line)
dumpuntilmatch (find)         (send lines from current line until matching line to output and set input focus to next line)
                              (exclusive of current/matching line unless start/end =True)
dumpsection   (position1,position2)
                              (send lines from position1 to position2 to output and set focus to line after section) 
dumpfields    ("text" "$fieldn" "m:p" "$holdn" any number of them in any order)
              ("fieldn" e.g. $field1 or $field5 designate the nth whitespace-delimited field from the current line)
              ("m:p" desinates columns or characters m to p of the current line)
              ($holdn designates the nth item stored by a previous holdfields command)
              (e.g. "dumpfields $field3 1:10 feet" should print the 3rd field, then columns 1-10, then "feet")
              ("dumpfields text" is, in effect, a synonym for "print text")
matchnextdump (find)          (increment () nfind () nlines () )
                              (match find, next increment, dump nlines lines, repeat nfind times, set focus to next line)
                              (if nfind = "all", search entire file)
holdfields    ("text")        (processes an input line like dumpfields,)
                              (but instead of dumping to output, holds the fields, slices, or text)
                              (for output in a subsequent dumpfields command)
                              (used to combine parts of two input lines)
print         ("text")        (write arbitrary text string to output)
                              (print Here is some text... or print "Here is some text" both work)

=======================================================
Commands related to different input/output files
=======================================================
switchinputto (name)          (start processing input file name at its current line)
switchoutputto(name)          (start writing to the named output file (usually "output") )
setinputfilename              (give an existing input file a new name)
                              (e.g. setinputfilename $file2 auxilliary_file
setoutputfilename             (give existing output file a new name)
writefile     (name filename) (write to filename the internal file corresponding to name) 
                              (you usually don't need to do this; maybe helpful when debugging)
readinput     (name)          (read another input file; give it the name $filen where n is)
                              (1 more than the previous highest-numbered input file)
                              (mostly useful when running outgrab using runoutgrab function
                              (from within another program)
empty         (name)          (delete all the lines in the input file "name".)
                              (affects only internal representation of file in memory; no changes on disk)
                              (probably most useful for emptying the scratch file)

There are three ways to get input files into the program.
1. From standard in (stdin) on the command line running the outgrab.py interpreter
e.g. python outgrab.py < maininputfile.txt 
2. From the -i flag on the command line running the outgrab.py interpreter
e.g. python outgrab.py -i a.txt b.txt < maininputfile.txt
3. Using the readinput command
e.g. (within an outgrab program file) readinput c.txt
The file read in on standard input, is called $file1 or <stdin>
Other input files are called $file2, $file3, etc. as well as by their actual filenames.
There is also, automatically created, a file called "scratch" which can be written to or read from
The outgrab program file is called $file0 or "program" or by its actual file name
The initially created output file is just called "output"

=======================================================
Commands for modifying the last line of the output file
=======================================================
joinlast                      (join together last two lines of *output* file)
                              (so that " line (n-1) = line(n-1) + line(n) and line(n) is deleted)
switchlast                    (switch last two lines of *output* file)
remove        (text, occurrence)
                              (remove nth occurrence of "text" from last line of output file)
replace       (text, newtext, occurrence)
                              (replace nth occurrence of "text" from last line of output file with newtext)

=======================================================
Commands for loops and simple if/endif
=======================================================
ifmatch   / endifmatch        (surround set of commands to be executed only if previous match was successful)
ifnomatch / endifmatch        (surround set of commands to be executed only if previous match was not successful)
repeat        (ntimes)        (beginning of a loop: repeat (ntimes times) all lines from here...)
                              (to endrepeat)
endrepeat/end                 (end of loop)
break                         (stop execution of loop and execute statement after endrepeat)
                              (must be executed inside both if(no)match/endifmatch and repeat/endpreat)

"""

if __name__ == "__main__":
    pass
