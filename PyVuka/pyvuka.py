#!/usr/bin/env python
#title           :pyvuka.py
#description     :This program is used for manipulating and fitting scientific
#                 data. Functions include global analysis, figure generation,
#                 and general statistical analysis of data.
#usage           :python pyvuka.py sys.argv[]
#python_version  :3.7
#==============================================================================
import sys
import os
from PyVuka import commands, data_obj as data

__author__ = "R. Paul Nobrega"
__copyright__ = "Copyright 2017, www.BostonAutoLytics.com"
__credits__ = "R. Paul Nobrega, Osman Bilsel, & David G. Lambright"
__license__ = "GPL"
__version__ = "0.1.3"
__maintainer__ = "R. Paul Nobrega"
__email__ = "Paul@BostonAutoLytics.com"
__status__ = "Development"



def homescreen():
    print("\n\n  ____        __     __       _     ")
    print(r" |  _ \  _   _\ \   / /_   _ | | __ __ _ ")
    print(r" | |_) || | | |\ \ / /| | | || |/ // _` |")
    print(r" |  __/ | |_| | \ V / | |_| ||   <| (_| |")
    print(r" |_|     \__, |  \_/   \__,_||_|\_\\__,_|")
    print(r"         |___/   ")
    print('\n'+__copyright__+'\n'+str(__credits__)+'\nVersion '+__version__+' ('+__status__+')')
    print("Questions or comments? Email: %s" % __email__)
    print("\n------------------------------------------")
    print("Type 'help' for information\nType 'q' to quit")
    print("------------------------------------------\n")
    return


def start():
    homescreen()
    exitflag = False
    commander = commands.Command()
    workingdir = os.getcwd()
    data.init()
    data.directories.working.set(workingdir)
    print("Current Working Directory: %s\n" % data.directories.working.get())
    if len(sys.argv[1:]) >= 1:
        if os.path.exists(sys.argv[1]):
            commander("cwd -set "+str(sys.argv[1]))
            initargs = " ".join(map(str, sys.argv[2:])).split(';')
        else:
            initargs = " ".join(map(str, sys.argv[1:])).split(';')
        for initarg in initargs:
            print("PyVUKA> " + initarg)
            print(commander(initarg))
    while not exitflag:
        userinput = input("\nPyVUKA> ")
        userinput = userinput.split(';')
        for command in userinput:
            output = commander(command)
            if output == '':
                continue
            elif not output:
                exitflag = True
            else:
                print(output + "\n")


if __name__ == '__main__':
    start()
