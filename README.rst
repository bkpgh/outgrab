======================
**OUTGRAB**
======================

.. contents::

Introduction
-------------

Outgrab programatically selects important information from,
usually large, text files and sends that information to other files
for later consumption by humans or other programs.
It provides a relatively simple domain-specific
language for file summarization, report writing, or input file
creation. The canonical examples and motivating
cases for the creation of outgrab are the large output files
produced by programs for molecular simulations or quantum chemistry
calculations. Those output files can be many thousands of lines long
and while all of those lines may be important for some purposes,
most often you just want to look at a few of the important ones
or send a small subset of them to another program for, e.g.,
plotting. Outgrab intends to make this process simple, maintainable,
and reproducible. 

Why would you use this program instead of grep, sed, awk, cut, paste, etc.?

1. Because you forget how to use all of the options of those programs.
2. Because it makes some of the relevant operations easy to do.
3. Because the commands included are very close to what you would do by hand
   when searching through an output file and selecting the bits of interest.

If outgrab doesn't do something you would like, but one of the
unix command-line tools mentioned above does, the best approach 
may be to post-process the result of outgrab with, e.g., sed.


License
-------
Outgrab is released under the MIT License. We hope you find it useful.

Brief Installation and Usage 
------------------------------------

As of this initial v0.1 release, there is no installation package for
outgrab; it simply consists of three python files (which have been
tested only under linux and python 3). There are two modules which
should probably be placed on your PYTHONPATH so they can be imported:

  | outgrab_tools.py
  | outgrab_simulation.py

The outgrab interpreter is outgrab.py. It might be useful to add it
to the system PATH variable. For a minimum installation
to just get started, you can place the three .py files in the directory
in which you want to work.

See later for a summary of the outgrab command language, but for now
you can picture it containing commmands like::

   match energy
   dumpline

which find the first line in an input file that contains the word
"energy" and prints/copies/sends it to an output file.

If these commands are placed in a file energy.grab, you want to run
this program on a file simulation.output, and produce a file called
simulation.summary, the full command might be::

  python outgrab.py -p energy.grab < simulation.output > simulation.summary

where "-p" stands for "program" and can be replaced with "--program".

Depending on your system, you may be able to eliminate the explicit use
of "python" since outgrab.py starts with a "shebang":
#!/usr/bin/python3. It might also be useful to create an alias,
e.g. in your .bashrc file, like this::

  alias og="python3 ~/bin/python/outgrab.py"

so that you can just do::

  og -p energy.grab < simulation.output > simulation.summary

Input text files can come from several places, but at least one always
comes from stdin. You can use redirection as above (<) or can send
one or more files to outgrab via a pipe::

  cat *.txt | python outgrab.py -p mytest.grab > myoutput.txt

in which case the the .txt files will be concatenated together and
outgrab will see them as one file. The file coming in on stdin
is referenced by $file1 in the command language.

You can also input files via the -i or --inputfiles flags like this::

  python outgrab.py -i a.txt b.txt < simulation.output > simulation.summary

These will be treated separately and can be referred to within the og
command language as $file2, $file3, etc. or by their filenames, e.g.
"a.txt".  Output goes to stdout: it by default goes to the screen
or it may be redirected into an output file as in the initial example
where it is redirected to simulation.summary.

There is one more flag to outgrab, "-v" or --verbosity, which
recognizes values from 0 to 4 which direct the program
to produce increasing levels of informational or diagnostic output
which goes to stderr (by default the screen). Verbosity = 0,
the default, means silent; the program produces no output other
than the result of the outgrab commands. Verbosity = 4 produces
huge amounts of output and is mostly useful for debugging
outgrab itself. Verbosity levels 1,2,3 may be useful for debugging
outgrab program files or individual outgrab
command lines.

=======================================================
Outgrab Command Language
=======================================================

Syntax
------

Each outgrab statement is a command name followed by zero or more
arguments or parameters. The argument syntax is one of two types:

    | 1. a list of position-specific parameters (usually just one):

        command arg1 arg2 ...

    | 2. a first position-specific parameter, followed by a list of
      name, value pairs:

        command arg1 paramname1 param1 paramname2 param2 ...

For example, "match energy nfind 3" is the command
"match" followed by a first argument "energy"
(which is the word to match), followed by a parameter pair with
name "nfind" and value "3"; the number of matches to find.
All named parameters have a default value and are optional.
Two more more words can be combined into one argument or
parameter by surrounding with double quotes, for simple text
to be printed, this is not usually necessary.
Don't put double quotes around a single word.

Almost no punctuation is needed or allowed; each statement is a
sequence of words or numbers. All leading or trailing whitespace
is ignored. Anywhere a position is required, you can use an
absolute line number, but this is not usually necessary
or recommended. Instead use a label. At initialization,
labels are created for the beginning of the file (top)
and the end of the file (bottom). Top and bottom are reserved
words and should always be valid. One usually finds things with
*match* or a similar command rather than using an explicit line number.

# or ! at the beginning of a line lead to it being ignored
as a comment. Blank lines or lines containing only whitespace
are also ignored.

Preliminary Examples
-----------------------

A simple outgrab program is::

    print "Here are some lines after the energy."
    match energy    (search through the input lines until finding one containing "energy")
    next 2          (step to the next line and then to the next (skip a line))
    dumplines 4     (send that line and the next 3 to the output, then set focus to the next line)

In that example, we searched for the word "energy". Instead of
matching simple words or phrases, one can use python-style
regular expressions. For example, to match lines containing
either "Energy" or "energy" (upper or lower case "E"), you can::

    match [E|e]nergy

The above commands demonstrate the most common uses of outgrab:
move around an input file, match certain text strings, print out
the lines containing them, and/or print out other lines near those lines.

Common Arguments or Parameters
--------------------------------

========= ==================== ======================================================
Argument   argument type        definition
========= ==================== ======================================================
increment     integer           number of lines to move forward or back (<0 => back)
find          string/re         string or regular expression (re) to match or find 
nfind         integer           number of matches to find 
label         string            label to assign to a position(using remember/forget)
nlines        integer           number of lines to return
position      integer/string    line number (0:) or a label
direction     integer           -1 or 1 for searching or moving back or forward
========= ==================== ======================================================

Commands
--------

Commands for moving around the input file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

============= ==================== =======================================================
command         argument             effect
============= ==================== =======================================================
match          | find              | go to next line that matches "find"; set focus there
               | nfind             | the number of matches to find before stopping 
               | direction         | -1 or 1 to indicate searching backwards or forwards
next or step    increment          go forward increment lines; default 1; can be negative
back            increment          go backward increment lines; default 1; back n = next-n
remember        label              assign label to current line
forget          label              erase label; not usually necessary
goto            position           set current line to line number label
============= ==================== =======================================================

Note that: next, back, goto  update the "state" or the current
line number to the one indicated, while match updates the "state"
or the current line number to the first one containing the match
Commands with "dump" in them update the current line number to
that just after the last line dumped. Other commands do not normally
change the current line of the input file

Commands for sending text to the output file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

=============== ==================== ======================================================
command           arguments            effect
=============== ==================== ======================================================
dumpline                               | send current line to output and
                                       | set input focus to next line
dumplines        nlines                | send nlines to output, starting with current
                                       | and set input focus to next line
dumpuntilmatch  | find                 | send lines from current line until matching line
                | start                | to output and set input focus to next line
                | end                  | exclusive of current/matching line
                                       | unless start/end =True
dumpsection     | position1            | send lines from position1 to position2
                | position2            | to output and set focus to line after section
dumpfields      | text                 | print text to output
                | $fieldn              | designate nth whitespace-delimited field
                | m:p                  | a "slice" designates columns or characters m to p
                | $holdn               | designates nth item stored by previous holdfields
                                       | e.g. "dumpfields $field3 1:10 feet"
                                       | prints the 3rd field, the columns 1-10, then "feet"
                                       | "dumpfields text" is a synonym for "print text"
holdfields      | text                 | processes an input line like dumpfields,
                | $fieldn              | but instead of dumping to output,
                | m:p                  | holds the fields, slices, or text
                                       | for output in a subsequent dumpfields command
                                       | used to combine parts of two input lines
matchnextdump   | find                 | match find, next increment, dump nlines lines,
                | increment            | repeat nfind times, set focus to next line
                | nfind                | if nfind = "all", search entire file
                | nline
print           text                   | write arbitrary text string to output
                                       | print Here is some text...
                                       | or print "Here is some text" both work
=============== ==================== ======================================================

Commands related to different input/output files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

=================  ==================== =======================================================
command             arguments            effect
=================  ==================== =======================================================
switchinputto      name                 start processing input file name at its current line
switchoutputto     name                 start writing to the named output file;
                                        usually "output"
setinputname       name                 give an existing input file a new name,
                                        e.g. setinputname $file2 auxilliary_file
setoutputname      name                 give existing output file a new name
writefile          | name               write to filename the internal file corresponding
                   | filename           to name. Not often used. 
readinput          name                 read another input file and
                                        give it the name $filen where n is
                                        1 more than the previous highest-numbered input file
empty              name                 | delete all the lines in the input file "name"
                                        | affects only internal representation of file in
                                        | memory; no changes on disk
                                        | probably most useful for emptying the scratch file
include            filename             insert lines of "filename" into the current *program*
=================  ==================== =======================================================

Commands for modifying the last line of the output file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

=============== ==================== ======================================================
command           arguments            effect
=============== ==================== ======================================================
joinlast                               | join together last two lines of *output* file
                                       | so that " line (n-1) = line(n-1) + line(n)
                                       | and line(n) is deleted)
switchlast                             switch last two lines of *output* file)
remove           | text                | remove nth occurrence of "text"
                 | occurrence          | from last line of output file)
replace          | text                | replace nth occurrence of "text" from final line
                 | newtext             | of output file with newtext
                 | occurrence
=============== ==================== ======================================================

Commands for loops and rudimentary if/endif
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===================== ==================== ======================================================
command                 arguments            effect
===================== ==================== ======================================================
ifmatch/endifmatch                          | surround set of commands to be executed only
                                            | if previous match was successful
ifnomatch/endifmatch                        | surround set of commands to be executed only if
                                            | if previous match was NOT successful
repeat/endrepeat      ntimes                | beginning of a loop: repeat (ntimes times)
                                            | all lines from repeat to endrepeat
break                                       | stop execution of loop and execute statement
                                            | after endrepeat. Must be executed inside both
                                            | if(no)match/endifmatch and repeat/endpreat
===================== ==================== ======================================================

Other commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===================== ==================== ======================================================
command                 arguments            effect
===================== ==================== ======================================================
exit                                         stop execution at this point
setverbosity            verbosity level      | overrides the initial verbosity level
                                             | 0 --> silent; 4 --> very verbose / debug
===================== ==================== ======================================================

======================
Tutorial
======================

Included with the release is a file containing the
King James Version of the book of Genesis:
kjv_genesis.txt. Running the outgrab
program test.grab with kjv_genesis.txt as an input file
is done like this::

    python outgrab.py -p test.grab < kjv_genesis.txt

Or, you can set up the outgrab files, alises, etc.
to make a shorter command as described above.

print, exit, setverbosity
---------------------------

Most of the following code snippets (perhaps in
extended/annotated form) are included in the test.grab
file in the tutorial directory. 

The print command is useful for adding your own
information, not coming from an input file, to
the output. Therefore, the canonical first program
(run as described above) is::

    print Hello World!

If you look in the supplied test.grab, you will see
that following
the print command is an "exit" command. This just
stops execution of an outgrab program at that point.
As you progress in the tutorial, just
move the exit command to a point after the code that
you want to run and all of the commands up to that
point, and none of those after, will run.

If, at any point, you want to see more of what is
going on under the hood, add a "setverbosity N"
command, where 0 <= N <= 4 (0 means silent,
4 means very verbose). This overrides any verbosity
set on the command line with the -v or --verbosity
flags. This can be very useful for debugging an outgrab
program (or outgrab.py itself) without seeing all
of the information/warning/debug information for
code sections that are working. Start with verbosity
1 or 2 for finding bugs in outgrab programs.

comment, dumpline, goto, match, back
--------------------------------------------------------------

If you want to print the first line of the inputfile,
an appropriate outgrab file would be simply::

    dumpline

Pasting that line in a file "test.grab",
and running "python outgrab.py -p test.grab < kjv_genesis.txt"
should yield on the screen::

    1:1: In the beginning God created the heaven and the earth.

With the supplied test.grab, just move the exit command to below
the dumpline command and the "Hello World!" and "dumpline" programs
will both run. If you no longer want the "Hello World!" program to run,
you can comment it out by placing "#" or "!" at the beginning of
each line that you do not want to run.

If instead you wanted to see the last line of the input file::

    # My second outgrab program
    goto bottom
    dumpline

which should print::

    50:26: So Joseph died, being an hundred and ten years old:
    and they embalmed him, and he was put in a coffin in Egypt. 

You could have used::

    goto 1532

instead of "goto bottom" to achieve the same result,
but then you would have to know
that there are 1533 lines in kjv_genesis.txt and that outgrab
numbers the first line "0" as in the python or "C" programming
languages. Lesson: labels are easier to use than line numbers
(except incremental line numbers sometimes). The labels "top"
and "bottom" are predefined to point to the first and last
lines of any input file, but other labels can be defined.
You will see "goto top" many times in the test.grab file.
This just resets the input file so each code snippet acts
like it is a new program running on a fresh input file
except that the output file is not reset.

There is another case where "goto" a line number might be useful.
Outgrab currently reads all of the lines of all of input files
entirely into memory and any match commands look through
every line of the current input file until a match is found.
Therefore, sometimes the program will run quicker if you
"goto" a line that you know or guess precedes any matches::

    goto 100000
    match "thing that exists after line 100000"
    dumpline

You might want to try that program on the kjv_genesis file
to see what happens when you try to "goto" beyond the end of the file.

The commands seen so far implicitly search and move in
the "forward" or "down" direction, from the first line
of the file toward the last. This is reasonable, but sometimes
you want the opposite behavior. Suppose you want to find the
word "Isaac" that occurs just previous to the first occurrence
of "Jacob". This program does that::

    match Jacob
    back
    match Isaac direction -1
    dumpline

This prints:: 

    25:21: And Isaac intreated the LORD for his wife,
    because she was barren: and the LORD was intreated of him,
    and Rebekah his wife conceived.

It so happens that the line containing first occurrence of
"Jacob" also contains "Isaac". Since "match" finds a line
and then sits there, if the "back" was left out of the
above program, the 2nd "match" would have found "Isaac"
on the same line as the first match of "Jacob" and *that*
line would have been printed. That behavior might be
useful; it depends on what you want. 

Note that the "dump" commands, except for matchnextdump,
only operate forwards, and that after printing a line,
they advance to the next line of the input. This is so
you don't have to put a "next" after every "dump". 

If you want to print out the 5th line containing "Jacob",
the program could be::

    match Jacob nfind 5
    dumpline


repeat, endrepeat, matchnextdump, dumplines
--------------------------------------------------------------

"match" with nfind > 1 (the default) is like::

    repeat 5
        match Jacob
        next
    endrepeat
    back

The "match" command with nfind > 1 automatically steps
forward one line after each successful match
but the last one, so that subsequent
matches don't occur on the same line. Therefore::

    repeat 5
        match Jacob
    endrepeat

and::

    match Jacob nfind 5

produce different results. The former will just match
the same line 5 times while the latter does not; it
matches the first 5 lines containing "Jacob" and afterwards
the focus of the program is on that 5th "hit".

Note well that it is an error to leave out a keyword.
In::

    match Jacob 5

the "5" is ignored, so the above is the same as "match Jacob".
Most commands have a single argument that does not need
a keyword, but any following arguments do need a keyword
if they are explicitly set, though
defaults are always available for any keyword argument.

Now suppose you want to print out a block of lines
immediately following the match of some string?
The simple way is just::

    match Jacob
    next
    dumpline
    .
    .
    .
    dumpline
 
or better::

    match Jacob
    next
    dumplines 3

if you wanted the next three lines to be printed after the
match.

If you wanted to repeat that entire operation several
times, use repeat/endrepeat::

    repeat 5
        match Jacob
        next
        dumplines 3
    endrepeat

Because structures like that occur so often,
a single command is provided to replace that loop::

    matchnextdump Jacob nfind 5 increment 1 nlines 3

Very useful outgrab programs often consist
solely a series of matchnextdump commands plus
possibly a few prints. This is an easy way to crunch
a large output file into manageable portions.

remember / forget, dumpsection, dumpuntilmatch
--------------------------------------------------------------

What if the section you wish to print is defined
not by a number of lines but by
a match at the beginning and a match at the end?
Here is one way to do it using labels::

    match rolled
    next
    remember mystart
    match Rachel
    remember myend
    dumpsection mystart myend

This prints out all the lines after the "rolled" match,
up to and including the "Rachel" match and then sets
the focus of outgrab to the next line. It prints out
genesis 29:4 - 29:6. If you want to use the same labels
several times, it might be good to "delete" them after
they are created with the "forget" command to avoid
confusion.

The same effect could be obtained with::

    match rolled
    dumpuntilmatch Rachel start False end True

Note the use of the start and end parameters.
By default, dumpuntilmatch does not dump the input
line which is in focus at its start and it does not
dump the line corresonding to its "match". If
"start True" is used, the starting line is printed and
if "end True" is used, the match line is printed.
Perhaps combined with some "next" or "back" commands,
this is a common way to find and print large sections
of the input file.


dumpfields, holdfields
--------------------------------------------------------------

All of our examples so far have printed entire lines.
This is often not the desired effect.  The "dumpfields"
command allows you to print portions of a line defined
by

1. whitespace-delimited fields, or
2. column or character counts

If you want the third and seventh words from a line
to be printed, the command is "dumpfields $field3 $field7"::

    goto bottom
    dumpfields $field3 $field7

should print::

    Joseph hundred

If you want a section of the line defined by character
positions within the line you can use::

    goto bottom
    dumpfields 1:5 24:40

which prints::

    50:26 being an hundred  

The section captured by n:m is called a slice, as
in python. The different field types can be mixed
in any order and combined with text::

    goto bottom
    dumpfields $field7 24:40 $field3 "Here is some text" 1:5

yields::

    hundred being an hundred  Joseph Here is some text 50:26

Sometimes it is useful to combine information from two
different lines of an input file. The holdfields 
command, in conjuction with dumpdields, allows this.
You use holdfields just like dumpfields, but it
doesn't print anything. To print the captured fields,
add them to the arguments of a subsequent dumpfields
command like this::

    goto top
    holdfields 1:30 
    goto bottom
    print "Genesis. Beginning to end:"
    dumpfields $hold1 " ...  "  68:200

This prints::

    Genesis. Beginning to end:
    In the beginning God created  ...   embalmed him, and he was put in a coffin in Egypt. 
 
The first capture by holdfields becomes $hold1, the
second becomes $hold2 etc.,
when used in the subsequent dumpfields. Note that
in a slice, you can specify an ending character position
(e.g. 200 above) which is beyond the end of the
input line and dumpfields will capture
all characters up to the end of the line.

joinlast, switchlast, remove, replace
-------------------------------------------

There are other commands which modify the output,
but do more than print lines::

    goto top
    dumpline
    dumpline
    switchlast

reverses the order of the final two lines of the
input file::

    1:2: And the earth was without form, and void; and darkness was upon the face of the deep.  And the Spirit of God moved upon the face of the waters.
    1:1: In the beginning God created the heaven and the earth.

Adding "joinlast" to the above program,
concatentes the last two lines::

    1:2: And the earth was without form, and void; and darkness was upon the face of the deep.  And the Spirit of God moved upon the face of the waters.1:1: In the beginning God created the heaven and the earth.

The only other commands which modify a line of the output once
it has been dumped are "remove" and "replace". This program::

    goto top
    dumpline
    remove : 2

removes the (ugly) second ":" found in the line, to produce::

   1:1 In the beginning God created the heaven and the earth.

and:: 

    goto top
    dumpline
    replace : " | " 2

produces::

    1:1 |  In the beginning God created the heaven and the earth.

by replacing the 2nd ":" with " | "


Manipulating Input and Output Files
-----------------------------------

Files created when outgrab starts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a bit of potentially confusing terminology
that we've used in discussing outgrab. A file
(on disk) is called a file, but we've
also used that term for the internal structure which
holds the contents of a file-on-disk in memory. We could more
properly call the structures in memory that one can access
with outgrab, "internal files". There are usually at least
four internal files created when outgrab starts:

1. an output file called "output"
2. an input file called "$file1"
3. a program file called "$file0" or "program"
4. a utility file called "scratch"

The output file is built up line by line as we have seen.
The input file is held in memory and gets filled with
the contents of the external file which comes in via
stdin.  The program file is filled with the contents
of the .grab program via the -p or --program flag to
outgrab.py.  The scratch file, initialized as empty, shares
characteristics with both input files and output files.
It can be written to as the target of "dump" commands
and later be navigated via goto and match commands,
and read from, as the source for different dump commands
that, presumably, will write to "output". 

Additional input files, called "$file2", "$file3", etc.
or by their names as used in the operating system, are
brought in via the -i or --inputfiles flags.

The actual externally created output file (or the output
to the screen) is only produced at the end of outgrab,
after the internal version of that file is completely
built and all outgrab commands have been executed.

readinput, switchinputto, setinputfile 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We've discussed getting input information from the stdin and
the -i and --inputfile flags. Another way is via the "readinput"
command. Using this one can programmatically link to an
input file, switch the focus of the program to that file,
and start reading from there and dumping to output. For example,
if you had a standard header file, you could do this::

    readinput standardheader.txt
    switchinputto standardheader.txt
    dumpsection top bottom
    switchinputto $file1
    dumpline

and the result is::

    |-----------------------------------------------------|
    |                                                     |
    |    My Standard Header                               |
    |    Copyright 1856 Alfred A. Jones                   |
    |                                                     |
    |-----------------------------------------------------|
    
    1:1: In the beginning God created the heaven and the earth.

if the provided standardheader.txt file is used. Don't forget
to switch the input back to the 'normal' input file
(from stdin) if that is what you want to do, which it
usually is.

If you don't like the fact that the 'normal' input file
is named "$file1", you could put the following command
at the top of your programs to add a name for it
that is easier for you to remember::

    setinputfile $file1 standardin

and use "standardin", e.g. "switchinputto standardin" instead
of "switchinputto $file1". There is an analogous setoutputfile
command and either one can be used on any of the appropriate
input or output files if you know one name for them.

Outgrab does not have subroutines or functions, but for
sections of code that you want to repeat or use in different
programs, you can put the code in a separate file and "include"
it in your current program. So, to add the standard header with
one line, you would do::

    include standardheader.grab

in your outgrab program and inside of the file, "standardheader.grab", 
you would place the command lines above starting with 
"readinput standardheader.txt". When outgrab processes the include
command, it removes it and inserts all the lines of the inserted
file into the current program.

switchoutputto, writefile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We've mentioned the scratch file and here we want to motivate
a possible reason for using it. If you wanted to print out all
lines that include both "Jacob" and "Rachel", you could do it
with a complex regular expression using look-aheads::

    matchnextdump (?=.*Jacob)(?=.*Rachel) nfind all

(Note the use of the special argument "nfind all" rather than
something like "nfind 10000") This basically says look for
all instances of "Jacob" followed by "Rachel" or
instances of "Rachel" followed by "Jacob". If you are very familiar
with regular expressions, this might be easy to remember,
but for some of us it is not. The result
(with long lines truncated) is::

    29:10: And it came to pass, when Jacob saw Rachel ...
    29:11: And Jacob kissed Rachel, and lifted up his voice, and wept.
    29:12: And Jacob told Rachel ...
    29:18: And Jacob loved Rachel; ...
    29:20: And Jacob served seven years for Rachel; ...
    29:28: And Jacob did so, and fulfilled her week: and he gave him Rachel ...
    30:1: And when Rachel saw that she bare Jacob ...
    30:2: And Jacob's anger was kindled against Rachel: ...
    30:7: And Bilhah Rachel's maid conceived again, and bare Jacob a second son.
    30:25: And it came to pass, when Rachel had born Joseph, that Jacob ...
    31:4: And Jacob sent and called Rachel ...
    31:32: With whomsoever ...  For Jacob knew not that Rachel had stolen them.
    31:33: And Laban went into Jacob's tent, ... into Rachel's tent.
    33:1: And Jacob lifted up his eyes, ...  Rachel, and unto the two handmaids.
    35:20: And Jacob set a pillar upon her grave: that is the pillar of Rachel's grave unto this day.
    46:19: The sons of Rachel Jacob's wife; Joseph, and Benjamin.
    46:22: These are the sons of Rachel, which were born to Jacob: all the souls were fourteen.
    46:25: These are ... Rachel his daughter, and she bare these unto Jacob: all the souls were seven.

Another way to get the same result,
that is longer, but may be easier to remember,  
is to first find all the matches for "Jacob" and then search
*those* for ones that match "Rachel". You can use the scratch
file to do this::

    switchoutputto scratch
    matchnextdump Jacob nfind all
    switchoutputto output
    switchinputto scratch
    goto top
    matchnextdump Rachel nfind all

The result is the same as in the matchnextdump example.

If you ever want to see an intermediate state for one
of the internal files, or potentially want to produce
a second output file, you can use the writefile command
to produce a disk-file. Adding::

    writefile scratch myscratchfile.txt

to the above program produces a file, 
"myscratchfile.txt" containing the entire contents of
the scratch file--all of the lines containing "Jacob".

We've seen all of the current stable of outgrab commands
and hopefully you can see how to combine them to produce
condensed forms of useful information from large files.
There may be more realistic examples included in an
examples directory.


