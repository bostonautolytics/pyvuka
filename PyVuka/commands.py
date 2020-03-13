import sys
import os.path
from . import data_obj as data, plot, fitfxns, fileio, Modules, commands, numericalmethods, inputprocessing
import math
import numpy as np
import copy


class Command(object):
    """extend with do_something  method to handle your commands"""

    def __init__(self, quit_commands=['q', 'quit', 'exit'], help_commands=['help', '?', 'h']):
        self._quit_cmd = quit_commands
        self._help_cmd = help_commands

    def __call__(self, line):
        if line is None or line == '':
            return ''
        cmd, args = self.__parse_cmd_line(line)
        safe_commands = ['read', 'rea', 'exec', 'cwd']
        if cmd in self._quit_cmd:
            return False
        elif cmd in self._help_cmd:
            return self.help(args[0] if args else None)
        elif cmd not in safe_commands and data.matrix.get() == []:
            return "\n No Data In Memory! Read data with command: rea ."
        elif hasattr(self, 'do_' + cmd):
            return getattr(self, 'do_' + cmd)(*args)
        elif hasattr(self, 'do_' + cmd[:4]):
            return getattr(self, 'do_' + cmd[:4])(*args)
        elif hasattr(self, 'do_' + cmd[:3]):
            return getattr(self, 'do_' + cmd[:3])(*args)
        elif hasattr(self, 'do_' + cmd[:2]):
            return getattr(self, 'do_' + cmd[:2])(*args)
        else:
            return "\nUnknown Command: %s\n" % cmd

    def __parse_cmd_line(self, line):
        '''Parses commandline input.  line is space delimited except when double quotes are used'''
        dbl_qoute_idicies = [pos for pos, char in enumerate(line) if char == '"']
        dbl_qoute_bounds = []
        white_spaces = ['', ' ', '  ', '"', ' " ', ' "', ' "']
        tokens = []
        args=[]

        if len(dbl_qoute_idicies) > 1:
            for x in range(0, int(math.floor(len(dbl_qoute_idicies)/2),), 2):
                dbl_qoute_bounds.append([dbl_qoute_idicies[x], dbl_qoute_idicies[x+1]])

            min_bound = 0
            for bound in dbl_qoute_bounds:
                max_bound = bound[0]
                temp = line[min_bound:max_bound].split(' ')
                tokens.extend(temp)
                tokens.append(line[bound[0]:bound[1]].replace('"', ""))
                min_bound = bound[1]
            if min_bound < len(line):
                tokens.extend(line[min_bound:len(line)].split(' '))
        else:
            tokens = line.split(' ')

        tokens = [seg for seg in tokens if seg not in white_spaces]

        cmd = tokens[0].lower()
        if len(tokens) > 1:
            args = tokens[1:]
        return cmd, args


    def do_pl(selfself, *args):
        """\nCommand: Plot Limits\n
        Description: Specifies global x range of data to be used for drawing, fitting, writing, and manipulating data.

        Example Usage:
        \tpl on                  (Makes Plot Limits active)
        \tpl off                 (Disables Plot Limits)
        \tpl 1 10 20 100         (Plot limits = buffers 1-10, x range 20-100 by point index)
        \tpl -v 1 10 5.36 2000.1 (Plot limits = buffers 1-10, x range 5.36-2000.1 by x value)

        Default Inputs: on [first buffer] [last buffer] [x min of shortest buffer] [x max of shortest buffer]

        Default Options: N/A

        Options:
        \t-v option uses x values instead of point indicies to set limits
        """

        inparse = inputprocessing.InputParser()
        lastbuffer = data.matrix.length()
        shortestxdata = 0
        if data.matrix.length() == 0:
            return "No Data in Matrix!"
        if ((len(args) == 1 and args[0].lower() in ['on','-v']) or len(args) == 0) and data.plot_limits.is_active:
            return "Plot Limits Are Already Active"
        elif len(args) == 1 and args[0].lower() == 'off' and not data.plot_limits.is_active:
            return "Plot Limits Are Already Inactive"
        if (len(args) > 0 and args[0].lower() == 'off') and data.plot_limits.is_active:
            data.plot_limits.off()
            return "Plot Limits Off!"

        min_x_val = min([data.matrix.buffer(i).data.x.min() for i in range(1, data.matrix.length() + 1)])
        max_x_val = max([data.matrix.buffer(i).data.x.max() for i in range(1, data.matrix.length() + 1)])

        if "-v" in args:
            inparse.prompt = ["First Buffer", "Last Buffer", "Min x Val", "Max x Val"]
            inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [-1E100, 1E100], [-1E100, 1E100]]
            inparse.defaultinput = ['1', str(lastbuffer), str(min_x_val), str(max_x_val)]
        else:
            min_idx = data.matrix.buffer(1).data.x.nearest_index_to_value(min_x_val) + 1
            max_idx = data.matrix.buffer(1).data.x.nearest_index_to_value(max_x_val) + 1
            inparse.prompt = ["First Buffer", "Last Buffer", "First Point", "Last Point"]
            inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer],
                                   [1, min_idx],
                                   [1, max_idx]]
            inparse.defaultinput = ['1', str(lastbuffer), str(min_idx), str(max_idx)]
        if not inparse(args):
            return "Invalid input!"
        else:
            if not inparse.getparams():
                return "\nNo changes Have Been Made to Plot Limits!"
            if 'on' or '-on' in inparse.modifiers and not data.plot_limits.is_active:
                brange = sorted([int(inparse.userinput[0]), int(inparse.userinput[1])])
                data.plot_limits.buffer_range.set(brange)
                minindex = []
                maxindex = []
                if '-v' in inparse.cmdflags:
                    min_x = float(inparse.userinput[2])
                    max_x = float(inparse.userinput[3])
                    for i in range(min(brange), max(brange) + 1):
                        minindex.append(data.matrix.buffer(i).data.x.nearest_index_to_value(min_x))
                        maxindex.append(data.matrix.buffer(i).data.x.nearest_index_to_value(max_x))
                    data.plot_limits.x_range.set([min(minindex) + 1, min(maxindex) + 1])
                else:
                    pointnummin=int(inparse.userinput[2])
                    pointnummax=int(inparse.userinput[3])
                    data.plot_limits.x_range.set([pointnummin, pointnummax])
                data.plot_limits.on()

        if not data.plot_limits.is_active and 'off' or '-off' in inparse.modifiers:
            data.plot_limits.off()
            return "Plot Limits Off!"
        elif data.plot_limits.is_active == True:
            return "Plot Limits On!"
        else:
            return "Error Configuring Plot Limits!"

    def do_rea(self, *args):
        """\nCommand: REAd\n
        Description: Read in data from various file types. Horizontally repeating units will be read. Each data block will be saved in memory as one data buffer

        Example Usage:
        \tread -txt -xy c:\data\data.txt (Read specified ascii test file with xy data structure.  Structure definitions will be prompted)
        \tread -xlsx -xy c:\data\data.txt 0 3 0 0 0 (Read specified xlsx file with xy data structure, 3 row header, and default structure options)

        Default Input: N/A

        Default Options: -txt -xy  (if no file format given and extension matches a format, the extension will be used)

        Usage Options:
        \t-cwd  (uses cwd as base directory [used for for multiple file formats only])

        File Format Options:
        \t-txt (ascii text, tab or comma delimited)
        \t-xlsx (excel xlsx)
        \t-svb (legacy savuka binary)
        \t-fb (fortebio raw files)
        \t-pvk (pyvuka xml file)
        \t-i3x (SpectraMax i3x text file)

        \tData Block Configuration Options:
        \t-y  (first column is common x to single or repeating y columns.)
        \t-xy
        \t-xyz
        \t-ye
        \t-xye
        \t-xeye
        \t-xeyeze
        \t-cye  (First column is category (non-numeric), second is Y-val, third is Y-Error.)
        \t-cyz  (First column is category (non-numeric), second is Y-val, third is Z-val.)
        \t-ccz  (First column is category (non-numeric), second is category (non-numeric), third is Z-val.)
        """
        inparse = inputprocessing.InputParser()
        if not inparse(args):
            return "Invalid input!"
        formatoptions = ["txt", "xlsx", "svb", "fb", "pvk", "i3x"]
        userflags = inparse.cmdflags
        comparams = inparse.userinput

        if "-cwd" in userflags:
            if not inparse.modifiers:
                inparse.modifiers = [data.directories.working.get()]
            else:
                inparse.modifiers[0] = data.directories.working.get()

        if len(inparse.modifiers) == 0:
            return "No input file specified!"
        else:
            filetoread = inparse.modifiers[0]
            if not os.path.exists(filetoread):
                return "Invalid Filename!"
        try:
            ext = filetoread.split('.')[-1]
            if ext.lower() == 'csv':
                ext = 'txt'
            if ext in formatoptions and ('-' + ext) not in userflags:
                userflags.append('-' + ext)
        except:
            ext = None
        if len(userflags) == 1:
            userflags.append("-xy")
        try:
            if "-txt" in userflags:
                if "-y" in userflags:
                    return fileio.readtxt(filetoread, "-y", comparams)
                elif "-xy" in userflags:
                    return fileio.readtxt(filetoread, "-xy", comparams)
                elif "-xyz" in userflags:
                    return fileio.readtxt(filetoread, "-xyz", comparams)
                elif "-ye" in userflags:
                    return fileio.readtxt(filetoread, "-ye", comparams)
                elif "-xye" in userflags:
                    return fileio.readtxt(filetoread, "-xye", comparams)
                elif "-xeye" in userflags:
                    return fileio.readtxt(filetoread, "-xeye", comparams)
                elif "-xeyeze" in userflags:
                    return fileio.readtxt(filetoread, "-xeyeze", comparams)
                elif "-cye" in userflags:
                    return fileio.readtxt(filetoread, "-cye", comparams)
                elif "-cyz" in userflags:
                    return fileio.readtxt(filetoread, "-cyz", comparams)
                elif "-ccz" in userflags:
                    return fileio.readtxt(filetoread, "-ccz", comparams)
                else:
                    return "No txt file structure given."
            elif "-xlsx" in userflags:
                if "-y" in userflags:
                    return fileio.readxlsx(filetoread, "-y", comparams)
                elif "-xy" in userflags:
                    return fileio.readxlsx(filetoread, "-xy", comparams)
                elif "-xyz" in userflags:
                    return fileio.readxlsx(filetoread, "-xyz", comparams)
                elif "-ye" in userflags:
                    return fileio.readxlsx(filetoread, "-ye", comparams)
                elif "-xye" in userflags:
                    return fileio.readxlsx(filetoread, "-xye", comparams)
                elif "-xeye" in userflags:
                    return fileio.readxlsx(filetoread, "-xeye", comparams)
                elif "-xeyeze" in userflags:
                    return fileio.readxlsx(filetoread, "-xeyeze", comparams)
                elif "-cye" in userflags:
                    return fileio.readtxt(filetoread, "-cye", comparams)
                elif "-cyz" in userflags:
                    return fileio.readtxt(filetoread, "-cyz", comparams)
                elif "-ccz" in userflags:
                    return fileio.readtxt(filetoread, "-ccz", comparams)
                else:
                    return "No xlsx file structure given."
            elif "-svb" in userflags:
                if "-y" in userflags:
                    return fileio.readsvb(filetoread, "-y", comparams)
                elif "-xy" in userflags:
                    return fileio.readsvb(filetoread, "-xy", comparams)
                elif "-xye" in userflags:
                    return fileio.readsvb(filetoread, "-xye", comparams)
                else:
                    return "No svb file structure given."
            elif "-fb" in userflags:
                return fileio.readfb(filetoread)
            elif "-pvk" in userflags:
                return fileio.readpvk(filetoread)
            elif "-i3x" in userflags:
                return fileio.readi3x(filetoread)
            else:
                return "Invalid file type or structure given!"
        except:
            return "Specified File Format Does Not Match File Structure"

    def do_wri(self, *args):
        """\nCommand: WRIte\n
        Description: Write matrix data to various file types.

        Example Usage:
        \twri -txt  c:\data\data.txt (Wrtie matrix to tab delimited txt)
        \twri -xlsx c:\data\data.txt (Write matrix to xlsx file with figures)

        Default Input: N/A

        Default Options: -txt -xy  (if no file format given and extension matches a format, the xlsx extension will be used)

        Usage Options:
        \tN/A

        File Format Options:
        \t-txt (ascii text, tab or comma delimited)
        \t-xlsx (excel xlsx)

        """
        inparse = inputprocessing.InputParser()
        if not inparse(args):
            return "Invalid input!"
        formatoptions = ["txt", "xlsx"]
        userflags = inparse.cmdflags
        comparams = inparse.userinput

        if len(inparse.modifiers) == 0:
            return "No output file specified!"
        else:
            filetowrite = inparse.modifiers[0]
            if os.path.exists(filetowrite):
                return "Filename already exists!"
        try:
            ext = filetowrite.split('.')[-1]
            if ext.lower() == 'csv':
                ext = 'txt'
            if ext in formatoptions and ('-' + ext) not in userflags:
                userflags.append('-' + ext)
        except:
            ext = None
        if len(userflags) == 0:
            userflags.append("-xlsx")
        try:
            if "-txt" in userflags:
                    return "No txt file structure programmed!"
            elif "-xlsx" in userflags:
                fileio.writexlsx(filetowrite, sheet_name='Output', header_list=[], col_width_list=[], row_heights=152)
            else:
                return "Invalid file type or structure given!"
        except:
            e = sys.exc_info()[0]
            return "<p>Error: %s</p>" % e
        return "Data Written Successfully!"

    def do_test(self, *args):
        """"TESTING"""
        return "Testing"

    def do_exec(self, *args):
        """\nCommand: EXECute\n
        Description: Runs script of native commands from a txt file, line-by-line.

        Example Usage:
        \texec c:\data\script.txt (Executes line-by-line Pyvuka commands from specified file)
        \texec -script script_name (Executes line-by-line Pyvuka commands from specified script located in pyvuka Script directory)
        \texec -i c:\data\script.txt (Executes line-by-line Pyvuka commands from specified file, in interactive mode)
        \texec -module filename.py def_function (Executes custom Python function from module python files within Pyvuka Modules directory)

        Default Input: N/A

        Default Options: N/A

        Options:
        \t-i (interactive mode)
        """

        inparse = inputprocessing.InputParser()
        if not inparse(args):
            return "Invalid input!"
        userflags = inparse.cmdflags
        comparams = inparse.userinput

        if len(inparse.modifiers) == 0:
            return "No input file specified!"
        else:
            if len(inparse.modifiers) > 2 and "-module" in userflags:
                fixmethod = ' '.join(inparse.modifiers[1:])
                inparse.modifiers = [inparse.modifiers[0], fixmethod]
            filetoread = inparse.modifiers[0]
            interactivemode = False
            if "-module" in userflags:
                runmodule = "Modules."
                inparse.modifiers = [x.strip() for x in inparse.modifiers]
                for val in inparse.modifiers:
                    if val[-3:].lower() == ".py":
                        runmodule += val[:-2]
                        break
                for val in inparse.modifiers:
                    if ".py" not in val.lower():
                        runmodule += val
                        break
                if runmodule[-1:] != ")":
                    runmodule += "()"
                exec(runmodule)
                return "\nModule Run Successfully! Command Entered: " + runmodule
            if "-i" in userflags:
                interactivemode = True
            if "-script" in userflags:
                if '.' not in filetoread:
                    filetoread += ".txt"
                filetoread = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Scripts", filetoread)
                if not os.path.exists(filetoread):
                    return "File Does Not Exist!"
                print("\nRunning Script: [" + filetoread + "]\tInteractive Mode: " + str(interactivemode) + "\n")
                return runscript(filetoread, interactivemode)
        return "Script Ran Successfully!"

    def do_cwd(self, *args):
        """\nCommand: Current Working Directory\n
        Description: Displays the current working directory.

        Example Usage:
        \tcwd (Displays current working directory)
        \tcwd -set c:\data\ (Sets current working directory)
        \tcwd -default (Sets current working directory to Pyvuka install directory)
        \tcwd -output (Sets output directory for write related modules)

        Default Input: N/A

        Default Options: N/A

        Options:
        \t-set (changes current working directory)
        """
        args_list = list(args)
        inparse = inputprocessing.InputParser()
        userflags = inparse.cmdflags

        if "-default" in userflags:
            data.directories.working.set(os.path.dirname(os.path.abspath(__file__)))
            return "Current working directory SET to: " + data.directories.working.get()

        if not inparse.modifiers:
            # inparse.modifiers is populated when path is entered.  Spaces and numbers in path are removed in this
            # object.  So we revert to args to determine path input for '-set'
            if '-set' in args_list:
                args_list.remove('-set')
                arg_dir = os.path.abspath(" ".join(args_list))
                if os.path.isdir(arg_dir):
                    data.directories.working.set(arg_dir)
                    return f"Current working directory SET to: {data.directories.working.get()}"
                else:
                    return f"Invalid Directory! Current working directory: {data.directories.working.get()}"
            elif '-output' in args_list:
                args_list.remove('-output')
                arg_dir = " ".join(args_list)
                path_check = [os.path.exists(arg_dir), os.access(os.path.dirname(arg_dir), os.W_OK)]
                if True not in path_check:
                        return "Invalid Directory! No output directory has been set!"
                data.directories.output.set(arg_dir)
                return f"Current output directory SET to: {data.directories.output.get()}"
        return f"No changes made. Current working directory: {data.directories.working.get()}"

    def do_cl(self, *args):
        """\nCommand: CLear\n
        Description: Clears buffer data by buffer range

        Example Usage:
        \tcl 1       (Clears first buffer)
        \tcl 1 10    (Clears buffers 1-10, inclusive)
        \tcl 1 10 2  (Clears buffers 1-10, every 2. Removes buffers: 1,3,5,7,9)
        \tcl all     (Clears all buffers)

        Default Inputs: N/A

        Default Options: N/A

        Options: N/A"""
        inparse = inputprocessing.InputParser()
        lastbuffer = data.matrix.length()

        inparse.prompt = ["First Buffer", "Last Buffer", "Index Increment"]
        inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [1, lastbuffer]]
        inparse.defaultinput = ['1', lastbuffer, '1']
        if not inparse(args):
            return "Invalid input!"
        else:
            if len(inparse.userinput) == 1:
                inparse.userinput.append(inparse.userinput[0])
                inparse.userinput.append('1')
            elif len(inparse.userinput) == 2:
                inparse.userinput.append('1')
            if "all" in inparse.modifiers:
                data.matrix.clear()
                return "All Data Cleared!"
            gotparams = inparse.getparams()
        if not gotparams:
            return "No Buffers Were Cleared!"
        else:
            comparams = [int(val) for val in inparse.userinput]
            delarray = []
            for i in range(comparams[0], comparams[1]+1, comparams[2]):
                delarray.append(i-1)
            delarray.sort()
            for i in list(reversed(delarray)):
                data.matrix.remove_buffer_by_number(i+1)
            delarray = [val+1 for val in delarray]
            return "Buffers: " + str(delarray) + " removed!"

    def do_now(self, *args):
        """\nCommand: NOW\n
        Description: Displays current buffer information as it exists 'NOW'

        Example Usage: now

        Default Input: N/A

        Default Options: N/A

        Options: N/A"""
        if data.matrix.length() == 0:
            return "No data in memory!"
        else:
            # header
            print('{:7s}\t{:8s}\t{:18s}\t{:18s}\t{:18s}\t{:50s}'.format("Buffer#", "#Points", "   X    ", "   Y     ",
                      "   Z     ", 21*' ' + "Comments" + 21*' '))
            # boarder
            print('{:7s}\t{:8s}\t{:18s}\t{:18s}\t{:18s}\t{:50s}\n'.format(7*'-', 8*'-', 18*'-', 18*'-', 18*'-', 50*'-'))
            boarder = [7*'-', 8*'-', 18*'-', 18*'-', 18*'-', 50*'-']

            # buffer info
            for i in range(1, data.matrix.length()+1, 1):
                buffer = data.matrix.buffer(i)
                pnt = ' '
                x = ' '
                y = ' '
                z = ' '
                comments = ' '

                # get point #
                pnt = int(max([buffer.data.x.length(), buffer.category.x.length(),
                               buffer.data.y.length(), buffer.category.y.length(),
                               buffer.data.z.length(), buffer.category.z.length()]))
                if pnt < 1:
                    pnt = '????'

                # Get X range
                if buffer.data.x.length() > 0:
                    x = "{:.2f}".format(buffer.data.x.min()) + ' - ' + "{:.2f}".format(buffer.data.x.max())
                elif buffer.category.x.length() > 0:
                    xi = buffer.category.x.value_at_index(0)
                    xf = buffer.category.x.value_at_index(-1)
                    if len(xi) > 4:
                        xi = xi[:4] + "..."
                    if len(xf) > 4:
                        xf = xf[:4] + "..."
                    x = xi + ' - ' + xf

                # Get Y range
                if buffer.data.y.length() > 0:
                    y = "{:.2f}".format(buffer.data.y.min()) + ' - ' + "{:.2f}".format(buffer.data.y.max())
                elif buffer.category.y.length() > 0:
                    yi = buffer.category.y.value_at_index(0)
                    yf = buffer.category.y.value_at_index(-1)
                    if len(yi) > 4:
                        yi = yi[:4] + "..."
                    if len(yf) > 4:
                        yf = yf[:4] + "..."
                    y = yi + ' - ' + yf

                # Get Z range
                if buffer.data.z.length() > 0:
                    z = "{:.2f}".format(buffer.data.z.min()) + ' - ' + "{:.2f}".format(buffer.data.z.max())
                elif buffer.category.z.length() > 0:
                    zi = buffer.category.z.value_at_index(0)
                    zf = buffer.category.z.value_at_index(-1)
                    if len(zi) > 4:
                        yi = yi[:4] + "..."
                    if len(zf) > 4:
                        zf = zf[:4] + "..."
                    y = zi + ' - ' + zf

                # Get comments
                comments = buffer.comments.all_as_string()
                if len(comments) > 50:
                    comments = comments[:-3] + "..."

                print('{:7s}\t{:8s}\t{:18s}\t{:18s}\t{:18s}\t{:50s}'.format(str(i), str(pnt), x, y, z, comments))

        return '\n'

    def do_sbf(self, *args):
        """\nCommand: Subtract Buffer From\n
        Description:
        \tSubtracts indicated buffer from range of buffers (y-values), point-wise. Existing buffers are modified.
        \tSubtraction automatically truncates the buffers to the smallest size

        Example Usage:
        \t sbf 1 1 10 (subtracts data in buffer 1 from all buffers in range 1-10)
        \t sbf 1 10   (subtracts data in buffer 1 from only buffer 10)

        Default Input: N/A

        Default Options: N/A

        Options: N/A
        """
        inparse = inputprocessing.InputParser()
        lastbuffer = data.matrix.length()
        inparse.prompt = ["Buffer to Subtract", "First Buffer", "Last Buffer"]
        inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [1, lastbuffer]]
        inparse.defaultinput = ['1', '1', str(lastbuffer)]
        if not inparse(args):
            return "Invalid input!"
        else:
            if len(inparse.userinput) == 2:
                inparse.userinput.append(inparse.userinput[2])
            gotparams = inparse.getparams()
        if not gotparams:
            return "No buffers to subtract!"
        else:
            comparams = [int(val) for val in inparse.userinput]
            subtractionbuffer = data.matrix.buffer(comparams[0]).data.y.get()
            subtractionye = data.matrix.buffer(comparams[0]).data.ye.get()
            for i in range(comparams[1], comparams[2]+1, 1):
                buffer = data.matrix.buffer(i)
                data_y = buffer.data.y.get()
                error_y = buffer.data.ye.get()
                minlen = min([len(data_y), len(subtractionbuffer)])
                data_y = data_y[:minlen] - subtractionbuffer[:minlen]
                if len(error_y) > 0 and len(subtractionye) > 0:
                    error_y = math.pow(math.pow(error_y[:minlen], 2) + math.pow(subtractionye[:minlen], 2), 0.5)
                buffer.comments.add("Buffer[" + str(comparams[0]) + "] Subtracted Data")

                buffer.data.y.set(data_y)
                buffer.data.ye.set(error_y)
                if buffer.data.x.length() > 0:
                    buffer.data.x.set(buffer.data.x.get()[:minlen])
                if buffer.data.xe.length() > 0:
                    buffer.data.xe.set(buffer.data.xe.get()[:minlen])
                if buffer.data.z.length() > 0:
                    buffer.data.z.set(buffer.data.z.get()[:minlen])
                if buffer.data.ze.length() > 0:
                    buffer.data.ze.set(buffer.data.ze.get()[:minlen])
            return "Buffer Subtraction Completed!"

    def do_res(self, *args):
        """\nCommand: RESample Data\n
        Description:
        \tResamples data within a buffer range to the number of points indicated bvy the used.
        \tResampled data is appended to the end of the data matrix as copied buffers.

        Example Usage:
        \tres 1 1 100   (resamples data in buffer 1 to have 100 data points)
        \tsbf 1 10 100  (resamples data in buffers 1 through 10 to have 100 data points)

        Default Input: N/A

        Default Options: N/A

        Options: NOT YET ADDED
        \t-log         (logarithmically resamples data)
        \t-antilog     (anti-logarithmically resamples data)
        \t-rand        (randomly resamples data)

        Notes:
        \tMinimum number of points to result from resampling is 3.
        """
        inparse = inputprocessing.InputParser()
        flags = inparse.cmdflags
        lastbuffer = data.matrix.length()

        shortest = data.matrix.shortest_x_length()

        inparse.prompt = ["First Buffer", "Last Buffer", "Number of Resulting Points"]
        inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [3, shortest]]
        inparse.defaultinput = ['1', str(lastbuffer), str(shortest)]
        if not inparse(args):
            return "Invalid Input!"
        if not inparse.getparams():
            return"\nNo Data Was Resampled!"
        inparse.userinput = [int(val) for val in inparse.userinput]
        firstbuffer, lastbuffer, npoints = inparse.userinput

        for i in range(firstbuffer, lastbuffer+1):
            buffer = copy.deepcopy(data.matrix.buffer(i))
            xtemp = []
            xetemp = []
            ytemp = []
            yetemp = []
            ztemp = []
            zetemp = []
            xlen = buffer.data.x.length()
            if xlen <= npoints:
                data.matrix.add_buffer(buffer)
                continue
            stepsize = int(np.floor(xlen/npoints))
            if stepsize > 1:
                for j in range(0, xlen, stepsize):
                    if buffer.data.x.length() > 0:
                        xtemp.append(buffer.data.x.value_at_index(j))
                    if buffer.data.xe.length() > 0:
                        xetemp.append(buffer.data.xe.value_at_index(j))
                    if buffer.data.y.length() > 0:
                        ytemp.append(buffer.data.y.value_at_index(j))
                    if buffer.data.ye.length() > 0:
                        yetemp.append(buffer.data.ye.value_at_index(j))
                    if buffer.data.z.length() > 0:
                        ztemp.append(buffer.data.z.value_at_index(j))
                    if buffer.data.ze.length() > 0:
                        zetemp.append(buffer.data.ze.value_at_index(j))
            else:
                xtemp = buffer.data.x.get()
                xetemp = buffer.data.xe.get()
                ytemp = buffer.data.y.get()
                yetemp = buffer.data.ye.get()
                ztemp = buffer.data.z.get()
                zetemp = buffer.data.ze.get()
            if len(xtemp) > npoints and npoints > 3:
                if len(xtemp) > 0:
                    temp = xtemp[1:-1][:npoints-2]
                    temp.append(xtemp[-1])
                    xtemp = xtemp[:1] + temp
                if len(xetemp) > 0:
                    temp = xetemp[1:-1][:npoints-2]
                    temp.append(xetemp[-1])
                    xetemp = xetemp[:1] + temp
                if len(ytemp) > 0:
                    temp = ytemp[1:-1][:npoints-2]
                    temp.append(ytemp[-1])
                    ytemp = ytemp[:1] + temp
                if len(yetemp) > 0:
                    temp = yetemp[1:-1][:npoints-2]
                    temp.append(yetemp[-1])
                    yetemp = yetemp[:1] + temp
                if len(ztemp) > 0:
                    temp = ztemp[1:-1][:npoints-2]
                    temp.append(ztemp[-1])
                    ztemp = ztemp[:1] + temp
                if len(zetemp) > 0:
                    temp = zetemp[1:-1][:npoints-2]
                    temp.append(zetemp[-1])
                    zetemp = zetemp[:1] + temp
            buffer.data.x.set(xtemp)
            buffer.data.xe.set(xetemp)
            buffer.data.y.set(ytemp)
            buffer.data.ye.set(yetemp)
            buffer.data.z.set(ztemp)
            buffer.data.ze.set(zetemp)
            buffer.comments.add("Data Resampled to %s points" % npoints)
            data.matrix.add_buffer(buffer)
        return '\nData Successfully Resampled!'

    def do_tri(self, *args):
        """\nCommand: TRIm Data\n
        Description:
        \tTrims data to index or X-value range defined by the user.
        \tTrimmed data overwrites the existing buffer.

        Example Usage:
        \ttri 1 2 10 1000     (trims data in buffers 1 through 2 to only include the points indexed from 10 to 1000)
        \ttri 1 2 0 100 -val  (trims data in buffers 1 through 2 to only include the points with X values between 0 and 100, inclusive)

        Default Input: N/A

        Default Options: N/A

        Options: NOT YET ADDED
        \t-v       (trims data based on X-val instead of point index)
        \t-val     (alias for above)
        \t-value   (alias for above)

        Notes:
        \tPoint index begins at 1, not 0
        """
        inparse = inputprocessing.InputParser()
        lastbuffer = data.matrix.length()
        shortest = data.matrix.shortest_x_length()
        useval = False

        inparse.prompt = ["First Buffer", "Last Buffer", "First Point Index", "Last Point Index"]
        inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [1, shortest], [1, shortest]]
        inparse.defaultinput = ['1', lastbuffer, '1', str(shortest)]
        if '-v' in args or '-val' in args or '-value' in args:
            useval = True
            inparse.prompt = ["First Buffer", "Last Buffer", "Min X-val", "Max X-val"]
            inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [-np.inf, np.inf], [-np.inf, np.inf]]
            inparse.defaultinput = ['1', lastbuffer,
                                    str(data.matrix.buffer(1).data.x.get()[0]),
                                    str(data.matrix.buffer(1).data.x.get()[-1])]
        if not inparse(args):
            return "Invalid Input!"
        if not inparse.getparams():
            return"\nNo Data Was Trimmed!"

        firstbuffer, lastbuffer = [int(x) for x in inparse.userinput[:2]]
        for i in range(firstbuffer, lastbuffer + 1):
            buffer = data.matrix.buffer(i)

            if useval:
                firstbuffer, lastbuffer, vali, valf = inparse.userinput
                indexi = buffer.data.x.nearest_index_to_value(vali)
                indexf = buffer.data.x.nearest_index_to_value(valf)
            else:
                firstbuffer, lastbuffer, indexi, indexf = inparse.userinput

            low = min([indexi, indexf])
            high = max([indexi, indexf])
            if buffer.data.x.length() > 0:
                buffer.data.x.set(buffer.data.x.get()[low:high])
            if buffer.data.xe.length() > 0:
                buffer.data.xe.set(buffer.data.xe.get()[low:high])
            if buffer.data.y.length() > 0:
                buffer.data.y.set(buffer.data.y.get()[low:high])
            if buffer.data.ye.length() > 0:
                buffer.data.ye.set(buffer.data.ye.get()[low:high])
            if buffer.data.z.length() > 0:
                buffer.data.z.set(buffer.data.z.get()[low:high])
            if buffer.data.ze.length() > 0:
                buffer.data.ze.set(buffer.data.ze.get()[low:high])

            data.matrix.set_buffer_by_number(buffer, i)
        return '\nData Successfully Trimmed!'

    def do_shi(self, *args):
        """\nCommand: SHIft Data\n
        Description:
        \tShifts data to by adding value defined by the user along the user defined axis. Default axis is X.
        \tShifted data overwrites the existing buffer.

        Example Usage:
        \tshi 1 2 -100        (Adds -100 to each X value in buffers 1 through 2)
        \tshi -y 1 2 -100     (Adds -100 to each Y value in buffers 1 through 2)

        Default Input: N/A

        Default Options: -x

        Options: NOT YET ADDED
        \t-x     (adds defined constant all X-value)
        \t-y     (adds defined constant all Y-value)
        \t-z     (adds defined constant all Z-value)

        Notes:
        \tN/A
        """
        inparse = inputprocessing.InputParser()
        lastbuffer = data.matrix.length()

        inparse.prompt = ["First Buffer", "Last Buffer", "Constant Value"]
        inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [-np.inf, np.inf]]
        inparse.defaultinput = [1, lastbuffer, 0.00]

        if not inparse(args):
            return "Invalid Input!"
        if not inparse.getparams():
            return"\nNo Data Was Shifted!"

        inparse.userinput = [int(val) for val in inparse.userinput]
        firstbuffer, lastbuffer, const = inparse.userinput

        for i in range(firstbuffer, lastbuffer + 1):
            buffer = data.matrix.buffer(i)
            # add const to Z axis
            if "-z" in inparse.cmdflags:
                buffer.data.z.set(buffer.data.z.get() + const)
            # add const to Y axis
            if "-y" in inparse.cmdflags:
                buffer.data.y.set(buffer.data.y.get() + const)
            # add const to X axis if specified or as default with no flags
            if ("-x" in inparse.cmdflags) or ("-y" not in inparse.cmdflags and "-z" not in inparse.cmdflags):
                buffer.data.x.set(buffer.data.x.get() + const)
        return '\nData Successfully Shifted!'

    def do_mul(self, *args):
        """\nCommand: MULtiply data by constant\n
        Description:
        \tSkews data by multiplying a constant value, defined by the user, along the user defined axis. Default axis is X.
        \tMultiplied data overwrites the existing buffer.

        Example Usage:
        \tmul 1 2 0.5        (Multiplies each Y value by 0.5 in buffers 1 through 2)
        \tmul -x 1 2 0.5     (Multiplies each X value by 0.5 in buffers 1 through 2)

        Default Input: N/A

        Default Options: -y

        \t-x     (multiplies defined constant all X-value)
        \t-y     (multiplies defined constant all Y-value)
        \t-z     (multiplies defined constant all Z-value)

        Notes:
        \tN/A
        """
        inparse = inputprocessing.InputParser()
        lastbuffer = data.matrix.length()

        inparse.prompt = ["First Buffer", "Last Buffer", "Constant Value"]
        inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [-np.inf, np.inf]]
        inparse.defaultinput = [1, lastbuffer, 0.00]

        if not inparse(args):
            return "Invalid Input!"
        if not inparse.getparams():
            return "\nNo Data Was Multiplied!"

        inparse.userinput = [int(val) for val in inparse.userinput]
        firstbuffer, lastbuffer, const = inparse.userinput

        for i in range(firstbuffer, lastbuffer + 1):
            buffer = data.matrix.buffer(i)
            # mul const to Z axis
            if "-z" in inparse.cmdflags:
                buffer.data.z.set(buffer.data.z.get() * const)
            # mul const to Y axis
            if "-x" in inparse.cmdflags:
                buffer.data.x.set(buffer.data.x.get() * const)
            # mul const to X axis if specified or as default with no flags
            if ("-y" in inparse.cmdflags) or ("-x" not in inparse.cmdflags and "-z" not in inparse.cmdflags):
                buffer.data.y.set(buffer.data.y.get() * const)
        return '\nData Successfully Multiplied!'

    def do_mod(self, *args):
        """\nCommand: MODel data with current parameters\n
        Description:
        \tModels defined function with defined parameters

        Example Usage:
        \tmod 1 2         (Models function for buffers 1 through 2)
        \tmod -all        (Models function for all buffers)

        Default Input: N/A

        Default Options: N/A

        \t-all     (Models function for all buffers)

        Notes:
        \tN/A
        """
        inparse = inputprocessing.InputParser()
        lastbuffer = data.matrix.length()
        firstbuffer = 1

        if '-all' not in args and 'all' not in args:
            inparse.prompt = ["First Buffer", "Last Buffer"]
            inparse.inputbounds = [[firstbuffer, lastbuffer], [firstbuffer, lastbuffer]]
            inparse.defaultinput = [firstbuffer, lastbuffer]

            if not inparse(args):
                return "Invalid Input!"
            if not inparse.getparams():
                return "\nNo Data Was Modeled!"

            inparse.userinput = [int(val) for val in inparse.userinput]
            firstbuffer, lastbuffer= inparse.userinput

        xr = data.plot_limits.x_range.get()
        yr = data.plot_limits.y_range.get()
        zr = data.plot_limits.z_range.get()
        br = data.plot_limits.buffer_range.get()
        ma = data.plot_limits.is_active

        commander = commands.Command()
        pti = 1 if not xr else min(xr)
        ptf = data.matrix.buffer(1).data.x.length() if not xr else max(xr)
        commander(f'pl off')
        commander(f'pl {firstbuffer} {lastbuffer} {pti} {ptf}')
        commander(f'pl on')
        commander(f'fit')
        commander(f'pl off')

        data.plot_limits.x_range.set(xr)
        data.plot_limits.y_range.set(yr)
        data.plot_limits.z_range.set(zr)
        data.plot_limits.buffer_range.set(br)
        data.plot_limits.is_active = ma
        return '\nData Successfully Modeled!'


    def do_ori(self, *args):
        """\nCommand: ORIgin\n
        Description:
        \tSets desired point index to origin (0,0,0).
        \tModified data overwrites the existing buffer.

        Example Usage:
        \tori 1 2 10        (Sets point #10 in buffers 1 through 2 as the XYZ origin)
        \tori -y 1 2 10     (Sets point #10 in buffers 1 through 2 as Y=0)

        Default Input: N/A

        Default Options: -x -y -z

        Options: NOT YET ADDED
        \t-x     (X=0 for defined point index)
        \t-y     (Y=0 for defined point index)
        \t-z     (Z=0 for defined point index)

        Notes:
        \tN/A
        """
        inparse = inputprocessing.InputParser()
        lastbuffer = data.matrix.length()

        inparse.prompt = ["First Buffer", "Last Buffer", "Point Index"]
        inparse.inputbounds = [[1, lastbuffer], [1, lastbuffer], [1, np.inf]]
        inparse.defaultinput = [1, lastbuffer, 1]

        if not inparse(args):
            return "Invalid Input!"
        if not inparse.getparams():
            return "\nNo Data Was Shifteded!"

        inparse.userinput = [int(val) for val in inparse.userinput]
        firstbuffer, lastbuffer, point_index = inparse.userinput
        point_index = point_index - 1  # 1->inf in user input, 0->inf in array

        if not inparse.cmdflags:
            inparse.cmdflags = ['-x', '-y', '-z']

        for i in range(firstbuffer, lastbuffer + 1):
            buffer = data.matrix.buffer(i)
            # sub const to Z axis
            if "-z" in inparse.cmdflags and buffer.data.z.length() > 0:
                const = buffer.data.z.value_at_index(point_index)
                buffer.data.z.set(buffer.data.z.get() - const)
                buffer.plot.axis.z.lines.set(buffer.plot.axis.z.lines.get() - const)
            # sub const to Y axis
            if "-y" in inparse.cmdflags:
                const = buffer.data.y.value_at_index(point_index)
                buffer.data.y.set(buffer.data.y.get() - const)
                buffer.plot.axis.y.lines.set(buffer.plot.axis.y.lines.get() - const)
            # sub const to X axis
            if "-x" in inparse.cmdflags:
                const = buffer.data.x.value_at_index(point_index)
                buffer.data.x.set(buffer.data.x.get() - const)
                buffer.plot.axis.x.lines.set(buffer.plot.axis.x.lines.get() - const)
        return '\nData Successfully Shifted!'

    def do_dr(self, *args):
        """\nCommand: DRaw\n
        Description: Draws requested plots in graphical output.

        Example Usage:
        \tdr (draws first buffer)
        \tdr all (draws all buffers)
        \tdr 1 10 2 (draws buffers 1-10, every 2.  Output is drawing 1, 3, 5, 7, 9)
        \tdr -l 1 3 5 7 9  (Draws a list of buffers. Output is drawing 1, 3, 5, 7, 9)

        Default Input: 1 1 1

        Default Options: N/A

        Options:
        \t -l (reads user input as list instead of incremental plotting)

        NOTES: Legacy Savuka "stack depth" (sd) is now controlled at the individual buffer level.  Similarly the
        following legacy options are depricated and are controlled at the individual buffer level:
        \t-err
        \t-nolegend
        \t-noweight
        Multiplot parameters will override individual settings."""
        inparse = inputprocessing.InputParser()
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
        inparse.prompt = ["First Buffer", "Last Buffer", "Index Increment"]
        inparse.inputbounds = [[firstbuffer, lastbuffer], [firstbuffer, lastbuffer], [firstbuffer, lastbuffer]]
        inparse.defaultinput = ['1', str(lastbuffer), '1']
        if not inparse(args):
            return "Invalid input!"
        modifiers = inparse.modifiers
        userflags = inparse.cmdflags
        comparams = inparse.userinput
        pltarray = []
        modifiers = [val.lower() for val in modifiers]
        for i in range(len(comparams)):
            if data.plot_limits.is_active:
                comparams[i] = int(comparams[i]) if firstbuffer <= comparams[i] else firstbuffer
                comparams[i] = int(comparams[i]) if comparams[i] <= lastbuffer else lastbuffer
            else:
                comparams[i] = int(comparams[i]) if comparams[i] <= lastbuffer else lastbuffer

        plotwindow = plot.plotter()
        if 'all' in modifiers:
            pltarray = [buf for buf in range(firstbuffer, lastbuffer + 1)]
        elif "-l" in userflags:
            comparams = [val for val in comparams]
            pltarray = comparams
        elif len(comparams) == 0:
            pltarray = [1]
        elif len(comparams) == 1:
            pltarray = [int(comparams[0])]
        elif len(comparams) == 2:
            for i in range(comparams[0], comparams[1] + 1):
                pltarray.append(i)
        elif len(comparams) > 2:
            for i in range(comparams[0], comparams[1] + 1, comparams[2]):
                pltarray.append(i)
        return plotwindow(pltarray)

    def do_sca(self, *args):
        """\nCommand: SCAn\n
               Description: Draws specified plots one at a time. Pressing any key will draw the next plot int he series.

               Example Usage:
               \tsca (Draws all buffers, one at a time)
               \tsca 1 10 2 (Draws buffers 1-10, every 2.  Output is drawing 1, 3, 5, 7, 9, one at a time)

               Default Input: 1 [last buffer index] 1

               Default Options: N/A

               Options:
               \t-auto (Automatically iterates through plots with 0.5 second delay between plots)
               \t-auto=# (Auto function with delay of 0.5 sec overridden by specified # of sec.

               NOTES: Multiplot parameters are ignored, individual settings will be used."""
        delay = 0.5  # time in seconds
        auto = False
        inparse = inputprocessing.InputParser()
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
        inparse.prompt = ["First Buffer", "Last Buffer", "Index Increment"]
        inparse.inputbounds = [[firstbuffer, lastbuffer], [firstbuffer, lastbuffer], [1, lastbuffer]]
        inparse.defaultinput = ['1', str(lastbuffer), '0']
        if not inparse(args):
            return "Invalid input!"
        userflags = inparse.cmdflags
        comparams = inparse.userinput
        if len(comparams) == 0:
            inparse.userinput = inparse.defaultinput
        plotwindow = plot.plotter()
        pltarray = []
        comparams = [int(val) for val in comparams]
        userflags = [st for st in userflags if "-auto" in st]
        if len(userflags) > 0:
            auto = True
            try:
                delay = float(userflags[0].split('=')[1])
            except:
                delay = 0.5
            pltarray = [buf for buf in range(firstbuffer-1, lastbuffer)]
            return plotwindow(pltarray, scan=True, auto=auto, delay=delay)
        gotparams = inparse.getparams()
        if not gotparams:
            return "\nNo Data to Scan!"
        comparams = [int(val) for val in inparse.userinput]
        for i in range(comparams[0], comparams[1]+1, comparams[2]):
                pltarray.append(i-1)
        return plotwindow(pltarray, scan=True, auto=auto, delay=delay)

    def do_fun(self, *args):
        """\nCommand: FUNction\n
        Description: Sets the functions or string of functions to be used for fitting data.
        Entering an index of 0 will stop concatenating functions.

        Example Usage:
        \tfun            (shows current list of available functions)
        \tfun info       (displays available function indexes for which info is available)
        \tfun info 27    (displays detailed information about function with index 27)
        \tfun 2 1 0      (sets the selected functions to 2 and 1)

        Default Input: N/A

        Default Options: N/A

        Options: N/A"""
        fail = "Invalid Input!"
        success = "Please input default parameters (see command: ap).\nFunction(s) set: "
        fitter = fitfxns.datafit()
        count = 1
        userin = 100
        fxnlist = fitter.getfxnlist()
        fxnlist = [int(val) for val in fxnlist]
        args = [val.lower() for val in args]
        # Parse user arguments
        inparse = inputprocessing.InputParser()
        inparse(args)

        if len(args) == 0:  # If no arguments provided, return list of available functions
            return fitter.showfxntable()
        elif data.matrix.length() == 0:  # If data matrix is invalid, return call
            return "No Data in Memory! Functions Cannot Be Applied!"
        elif 'info' in inparse.modifiers:  # If info in args, show function info
            return fitter(args)
        elif len(inparse.userinput) > 0 and inparse.userinput[-1] == 0: # If function request is closed, define fitter
            for num in inparse.userinput[:-1]:
                try:
                    temp = int(num)
                    if temp in fxnlist:
                        fitter.funcindex.append(temp)
                except ValueError:
                    return fail
            if len(fitter.funcindex) == 0:
                return fail
            else:
                if fitter.applyfxns():
                    return success + str(fitter.funcindex)
                else:
                    return"\nInvalid Functions Specified!"
        elif len(inparse.userinput) > 0 and inparse.userinput[-1] != 0: # If  function request is not closed, append function to fitter definition
            for val in inparse.userinput:
                try:
                    temp = int(val)
                    if temp in fxnlist:
                        fitter.funcindex.append(temp)
                        count += 1
                except ValueError:
                    return fail

        # prompt user to complete fxn definition
        print("\nEnter functions to concatenate, enter 0 to stop.\n")
        while userin > 0:
            userin = input("Enter Function #" + str(count)+" :  ")
            try:
                userin = int(userin)
            except ValueError:
                print(fail)
            if userin in fxnlist:
                count += 1
                fitter.funcindex.append(userin)
            elif userin != 0:
                print("Not a Valid Function!")
        # Apply fxn definitions to fitter object and return success/fail
        if fitter.applyfxns():
            return success + str(fitter.funcindex)
        else:
            "\nInvalid Functions Specified!"

    def do_fit(self, *args):
        commander = commands.Command()
        args = [val.lower() for val in args]
        ### Pre-flight check for any parameter linking ###
        linked = False
        plon = False
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
            firstpoint, lastpoint = data.plot_limits.x_range.get()
            plon = True
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
            firstpoint = 1
            lastpoint = data.matrix.shortest_x_length()

        for i in range(firstbuffer, lastbuffer + 1):
            buffer = data.matrix.buffer(i)
            linked = True if len([x for x in buffer.fit.link.get() if x is not None]) >= 1 else False
            if linked:
                break

        ### if independent fit override, all links will be copied and removed for fit--added back after ###
        alllinks = []
        if "-ind" in args:
            for i in range(firstbuffer, lastbuffer + 1):
                buffer = data.matrix.buffer(i)
                alllinks.append(buffer.fit.link.get())
            commander("unl -all")
        ### If data is not linked or override to independent fitting and restore link and plot limit states###
        if not linked:
            for i in range(firstbuffer, lastbuffer + 1):
                com_list = [i, i, firstpoint, lastpoint]
                command = "pl {} {} {} {}".format(*com_list)
                commander("pl off")
                commander(command)
                commander("pl on")
                print(fitfxns.dofit(*args))
            commander("pl off")
            if plon:
                com_list = [firstbuffer, lastbuffer, firstpoint, lastpoint]
                command = "pl {} {} {} {}".format(*com_list)
                commander(command)
                commander("pl on")
            else:
                commander("pl off")
        if "-ind" in args:  ### if -ind flag, restore original links ###
            for i in range(firstbuffer, lastbuffer + 1):
                buffer = data.matrix.buffer(i)
                buffer.fit.link.set(alllinks[i - 1])
            return "\nIndependent Fitting Complete!"
        elif not linked:
            return "\nIndependent Fitting Complete!"
        else:  ### if data is linked we run global fitting ###
            print(fitfxns.dofit(*args))
            return "\nGlobal Fitting Complete!"

    def do_ap(self, *args):
        """\nCommand: Alter Parameters\n
        Description: Prompts users to enter parameters for specified buffers.
        Enter 'q' to exit prompt cycle.

        Example Usage:
        \tap                      (Prompt user for all parameter information)
        \tap -all                 (Run a single cycle to collect parameters, applies to all buffers within plot limits)
        \tap all                  (Run a single cycle to collect parameters, applies to all buffers within plot limits)
        \tap 1 -1.56 2.7          (Sets parameters 1 & 2  to -1.56 and 2.7, for buffer 1)
        \tap -all -1.56 2.7       (Sets parameters 1 & 2  to -1.56 and 2.7, for all buffers within plot limits)
        \tap -cp                  (Prompts user for buffer to copy parameters from and buffer range to copy parameters to)
        \tap -cp 1 2 10           (Copies parameters from buffer 1 to all buffers in range 2-10)

        Default Input: N/A

        Default Options: N/A

        Options:
        \t-all        (Applies parameter input to all buffers within plot limits)
        \t-cp         (Copies parameters from specified buffer to all buffers in specified range)
        \t-cpp        (Same as above)
        \t-copy       (Same as above)

        Modifiers
        \tall         (Applies parameter input to all buffers within plot limits)

        Notes: Parameter links and fix states are preserved with copy functions
        """
        inparse = inputprocessing.InputParser()
        inparse(args)
        userincount = len(inparse.userinput)
        applyall = False
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
        elif userincount == 1:
            firstbuffer = int(inparse.userinput[0])
            lastbuffer = int(inparse.userinput[0])
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
        if len(data.matrix.buffer(firstbuffer).fit.function.get()) == 0:
            updatefixlnk()
            return "\nNo Function Defined. Try command: fun ."
        if "-all" in inparse.cmdflags or "all" in inparse.modifiers:
            applyall = True
        if "-cp" in inparse.cmdflags or "-cpp" in inparse.cmdflags or "-copy" in inparse.cmdflags:
            inparse.prompt = ["Buffer to copy parameters from"]
            inparse.inputbounds = [[firstbuffer, lastbuffer]]
            inparse.defaultinput = [str(firstbuffer)]
            userinsave = inparse.userinput
            inparse.userinput = inparse.userinput[:1]
            if not inparse.getparams():
                return "\nNo Parameters Were Copied!"
            parambuffer = int(inparse.userinput[0])
            inparse.userinput = userinsave[1:]
            if applyall:
                inparse.userinput = [firstbuffer, lastbuffer]
            inparse.prompt = ["First Buffer to Apply Parameters to", "Last buffer to apply parameters to"]
            inparse.inputbounds = [[firstbuffer,lastbuffer], [firstbuffer,lastbuffer]]
            inparse.defaultinput = [str(firstbuffer), str(lastbuffer)]
            if not inparse.getparams():
                return "\nNo Parameters Were Copied!"
            inparse.userinput = [int(val) for val in inparse.userinput]
            paramstocopy = data.matrix.buffer(parambuffer).fit.parameter.get()
            for i in range(inparse.userinput[0], inparse.userinput[1]+1):
                data.matrix.buffer(i).fit.parameter.set(paramstocopy[:])
            updatefixlnk()
            return "\nParameters copied from Buffer[" + str(parambuffer) + "] to Buffers[" + \
                   str(inparse.userinput[0]) + " - " + str(inparse.userinput[1]) + "] !"

        i = firstbuffer
        while i <= lastbuffer:
            fitparams = fitfxns.datafit()
            fitparams.update(data.matrix.buffer(i).fit.function_index.get())
            if not applyall:
                inparse.prompt = ["Buffer Number"]
                inparse.inputbounds = [[firstbuffer, lastbuffer]]
                inparse.defaultinput = [str(i)]
            inparse.prompt.extend([str(val) for val in fitparams.paramid])
            inparse.inputbounds.extend(fitparams.parambounds)
            inparse.defaultinput.extend([str(val) for val in fitparams.paramdefaults])
            inparse.previousvals = [str(i)] + [str(val) for val in data.matrix.buffer(i).fit.parameter.get()]
            if not inparse.getparams():
                return "Changes Made Before Aborting Operation Have Been Kept!"
            inparse.userinput = [float(val) for val in inparse.userinput]
            i = int(inparse.userinput[0])
            if not applyall:
                data.matrix.buffer(i).fit.parameter.set(inparse.userinput[1:])
            if applyall:
                #need use extend method to prevent linking dictionary values by reference // replaced with deepcopy
                for j in range(firstbuffer, lastbuffer + 1):
                    data.matrix.buffer(j).fit.parameter.set(copy.deepcopy(inparse.userinput))
                updatefixlnk()
                return "\nAll Initial Parameters Set!"
            if userincount > 0:
                updatefixlnk()
                return "\nInitial Parameters Set for Buffer[%s]!" % int(inparse.userinput[0])
            inparse.clear()
            fitparams.clear()
            i += 1
        updatefixlnk()
        return "\nInitial Parameters Set!"

    def do_lnk(self, *args):
        """\nCommand: LiNK parameters\n
        Description: Prompts users to enter parameter linkage information.
        Enter 'q' to exit prompt cycle.

        Example Usage:
        \tlnk                     (Prompt user for all parameter linkage information)
        \tlnk -all                (Links each parameter across all buffers)
        \tlnk all                 (Links each parameter across all buffers)
        \tlnk 1                   (Links parameter 1 for all buffers within plot limits)
        \tlnk 2 7 1 2             (Links Buffer 2, parameter 7 to Buffer 1, Parameter 2)

        Default Input: N/A

        Default Options: N/A

        Options:
        \t-all        (Applies parameter input to all buffers within plot limits)

        Modifiers"
        \tall         (Applies parameter input to all buffers within plot limits)
        """
        fitparams = fitfxns.datafit()
        inparse = inputprocessing.InputParser()
        inparse(args)
        applyall = False
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
        if len(data.matrix.buffer(firstbuffer).fit.parameter.get()) < 1:
            return "\nNo Initial Parameters Defined! Try command: ap ."
        if "-all" in inparse.cmdflags or "all" in inparse.modifiers:
            applyall = True
        if len(args) == 1:
            if applyall:
                for i in range(firstbuffer, lastbuffer - 1):
                    buffer = data.matrix.buffer(i)
                    fitparams.update(buffer.fit.function_index.get())
                    links = copy.deepcopy(buffer.fit.link.get())
                    if i != firstbuffer:
                        for j in range(len(links)):
                            links[j] = f"{fitparams.paramid[j]}_{j+1}_{firstbuffer}"
                    data.matrix.buffer(i).fit.link.set(links)
                return "\nAll Parameters Linked!"
            elif len(inparse.userinput) > 0:
                try:
                    for i in range(firstbuffer, lastbuffer + 1):
                        fitparams.update(data.matrix.buffer(i).fit.function_index.get())
                        if i != firstbuffer:
                            links = copy.deepcopy(data.matrix.buffer(i).fit.link.get())
                            links[int(inparse.userinput[0]) - 1] = fitparams.paramid[int(inparse.userinput[0])-1] + "_{}_{}".format(int(inparse.userinput[0]), firstbuffer)
                            data.matrix.buffer(i).fit.link.set(links)
                except:
                    return "\nInvalid Parameter Specified!"
                return "\nParameter %s Linked Across All Buffers!" % str(int(inparse.userinput[0]))
        else:
            inparse.prompt = ["Buffer to link", "Parameter to link", "Buffer to link to", "Parameter to link to"]
            inparse.inputbounds = [[firstbuffer, lastbuffer], [1, np.inf], [firstbuffer, lastbuffer], [1, np.inf]]
            inparse.defaultinput = [firstbuffer, 1, lastbuffer, 1]
            if not inparse.getparams():
                return"\nNo Buffers Were Linked!"
            fitparams.update(data.matrix.buffer(int(inparse.userinput[0])).fit.function_index.get())
            try:
                links = data.matrix.buffer(int(inparse.userinput[0])).fit.link.get()
                links[int(inparse.userinput[1]) - 1] = fitparams.paramid[int(inparse.userinput[1])-1] + "_{}_{}".format(int(inparse.userinput[3]), int(inparse.userinput[2]))
                data.matrix.buffer(int(inparse.userinput[0])).fit.link.set(links)
                return "\nParameter " + str(inparse.userinput[1]) + " of Buffer " + str(inparse.userinput[0]) + \
                       " Linked to Parameter " + str(inparse.userinput[3]) + " of Buffer " + str(inparse.userinput[2])
            except:
                return "\nInvalid Parameter Specified!"

        return "\nInvalid Command!"

    def do_unl(self, *args):
        """\nCommand: UNLink parameters\n
        Description: Prompts users to enter parameter linkage information.
        Enter 'q' to exit prompt cycle.

        Example Usage:
        \tunl                     (Prompt user for all parameter linkage information)
        \tunl -all                (Unlinks each parameter across all buffers)
        \tunl all                 (Unlinks each parameter across all buffers)
        \tunl 1                   (Unlinks parameter 1 for all buffers within plot limits)
        \tunl 1 3                 (Unlinks parameter 3 of Buffer 1)

        Default Input: N/A

        Default Options: N/A

        Options:
        \t-all        (Applies parameter input to all buffers within plot limits)

        Modifiers"
        \tall         (Applies parameter input to all buffers within plot limits)
        """
        inparse = inputprocessing.InputParser()
        inparse(args)
        applyall = False
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
        if len(data.matrix.buffer(firstbuffer).fit.parameter.get()) < 1:
            return "\nNo Initial Parameters Defined! Try command: ap ."
        if "-all" in inparse.cmdflags or "all" in inparse.modifiers:
            applyall = True
        if len(args) == 1:
            if applyall:
                for i in range(firstbuffer, lastbuffer+1):
                    unlinks = [None] * len(data.matrix.buffer(i).fit.link.get())
                    data.matrix.buffer(i).fit.link.set(unlinks)
                return "\nAll Parameters Unlinked!"
            elif len(inparse.userinput) > 0:
                try:
                    for i in range(firstbuffer, lastbuffer+1):
                        links = data.matrix.buffer(i).fit.link.get()
                        links[int(inparse.userinput[0]) - 1] = None
                        data.matrix.buffer(i).fit.link.set(links)
                except:
                    return "\nInvalid Parameter Specified!"
                return "\nParameter %s Unlinked Across All Buffers!" % str(int(inparse.userinput[0]))
        else:
            inparse.prompt = ["Buffer to modify", "Parameter to unlink"]
            inparse.inputbounds = [[firstbuffer, lastbuffer], [1, np.inf]]
            inparse.defaultinput = [firstbuffer, 1]
            if not inparse.getparams():
                return "\nNo Parameter Was Linked!"
            try:
                links = data.matrix.buffer(int(inparse.userinput[0])).fit.link.get()
                links[int(inparse.userinput[1]) - 1] = None
                data.matrix.buffer(int(inparse.userinput[0])).fit.link.set(links)
                return "\nParameter " + str(inparse.userinput[1]) + " of Buffer " + \
                       str(inparse.userinput[0]) + " Unlinked!"
            except:
                return "\nInvalid Parameter Specified!"

        return "\nInvalid Command!"

    def do_fix(self, *args):
        """\nCommand: FIX parameters\n
        Description: Prompts users to enter parameter free/fix information.
        Enter 'q' to exit prompt cycle.

        Example Usage:
        \tfix                     (Prompt user for all parameter Fix information)
        \tfix -all                (Fixes each parameter across all buffers)
        \tfix all                 (Fixes each parameter across all buffers)
        \tfix 3                   (Fixes parameter 3 for all buffers within plot limits)
        \tfix 1 3                 (Fixes parameter 3 of Buffer 1)

        Default Input: N/A

        Default Options: N/A

        Options:
        \t-all        (Applies parameter input to all buffers within plot limits)

        Modifiers:
        \tall         (Applies parameter input to all buffers within plot limits)
        """
        inparse = inputprocessing.InputParser()
        inparse(args)
        applyall = False
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
        if len(data.matrix.buffer(firstbuffer).fit.parameter.get()) < 1:
            return "\nNo Initial Parameters Defined! Try command: ap ."
        if "-all" in inparse.cmdflags or "all" in inparse.modifiers:
            applyall = True
        if len(args) == 1:
            if applyall:
                for i in range(firstbuffer, lastbuffer+1):
                    new_free = [False] * len(data.matrix.buffer(i).fit.free.get())
                    data.matrix.buffer(i).fit.free.set(new_free)
                return "\nAll Parameters Fixed!"
            else:
                for i in range(firstbuffer, lastbuffer+1):
                    free = data.matrix.buffer(i).fit.free.get()
                    free[int(inparse.userinput[0]) - 1] = False
                    data.matrix.buffer(i).fit.free.set(free)
            return "\nParameter %s Fixed!" % str(int(inparse.userinput[0]))
        else:
            inparse.prompt = ["Buffer to modify", "Parameter to fix"]
            inparse.inputbounds = [[firstbuffer, lastbuffer], [1, np.inf]]
            inparse.defaultinput = [firstbuffer, 1]
            if not inparse.getparams():
                return "\nNo Parameter Was Fixed!"
            free = data.matrix.buffer(int(inparse.userinput[0])).fit.free.get()
            free[int(inparse.userinput[1]) - 1] = False
            data.matrix.buffer(int(inparse.userinput[0])).fit.free.set(free)
            return "Parameter " + str(int(inparse.userinput[1])) + " of buffer " + \
                   str(int(inparse.userinput[1])) + " Fixed!"

    def do_fre(self, *args):
        """\nCommand: FREe parameters\n
        Description: Prompts users to enter parameter free/fix information.
        Enter 'q' to exit prompt cycle.

        Example Usage:
        \tfre                     (Prompt user for all parameter Free information)
        \tfre -all                (Frees each parameter across all buffers)
        \tfre all                 (Frees each parameter across all buffers)
        \tfre 3                   (Frees parameter 3 for all buffers within plot limits)
        \tfre 1 3                 (Frees parameter 3 of Buffer 1)

        Default Input: N/A

        Default Options: N/A

        Options:
        \t-all        (Applies parameter input to all buffers within plot limits)

        Modifiers:
        \tall         (Applies parameter input to all buffers within plot limits)
        """
        inparse = inputprocessing.InputParser()
        inparse(args)
        applyall = False
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
        if len(data.matrix.buffer(firstbuffer).fit.parameter.get()) < 1:
            return "\nNo Initial Parameters Defined! Try command: ap ."
        if "-all" in inparse.cmdflags or "all" in inparse.modifiers:
            applyall = True
        if len(args) == 1:
            if applyall:
                for i in range(firstbuffer, lastbuffer+1):
                    free = [True] * len(data.matrix.buffer(i).fit.free.get())
                    data.matrix.buffer(i).fit.free.set(free)
                return "\nAll Parameters Freed!"
            else:
                for i in range(firstbuffer, lastbuffer+1):
                    free = data.matrix.buffer(i).fit.free.get()
                    free[int(inparse.userinput[0]) - 1] = True
                    data.matrix.buffer(i).fit.free.set(free)
            return "\nParameter %s Freed!" % str(int(inparse.userinput[0]))
        else:
            inparse.prompt = ["Buffer to modify", "Parameter to free"]
            inparse.inputbounds = [[firstbuffer, lastbuffer], [1, np.inf]]
            inparse.defaultinput = [firstbuffer, 1]
            if inparse.getparams():
                free = data.matrix.buffer(int(inparse.userinput[0])).fit.free.get()
                free[int(inparse.userinput[1]) - 1] = True
                data.matrix.buffer(int(inparse.userinput[0])).fit.free.set(free)
                return "Parameter " + str(int(inparse.userinput[1])) + " of buffer " + \
                       str(int(inparse.userinput[1])) + " Freed!"
            else:
                return "Changes Made Prior to Aborting Have Been Kept!"

    def do_lp(self, *args):
        """\nCommand: List Parameters\n
                Description: List parameter information for the specified buffer or range of buffers.

                Example Usage:
                \tlp                     (Prompt user for buffers to show parameter information of)
                \tlp -all                (Shows parameter information for all buffers all buffers)
                \tlp all                 (Shows parameter information for all buffers all buffers)
                \tlp 1                   (Shows parameter information for all buffer 1)
                \tlp 1 3                 (Shows parameter information for all buffers 1 through 3)

                Default Input: N/A

                Default Options: N/A

                Options:
                \t-all        (Shows parameter information for all buffers within plot limits)

                Modifiers:
                \tall         (Shows parameter information for all buffers within plot limits)
                """
        inparse = inputprocessing.InputParser()
        inparse(args)
        fitparams = fitfxns.datafit()
        if data.plot_limits.is_active:
            firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
        else:
            lastbuffer = data.matrix.length()
            firstbuffer = 1
        if len(data.matrix.buffer(firstbuffer).fit.parameter.get()) < 1:
            return "\nNo Initial Parameters Defined! Try command: ap ."
        if "-all" in inparse.cmdflags or "all" in inparse.modifiers:
            inparse.userinput = [str(firstbuffer), str(lastbuffer)]
        if len(inparse.userinput) == 1:
            inparse.userinput.append(inparse.userinput[0])
        inparse.prompt = ["First Buffer", "Last Buffer"]
        inparse.inputbounds = [[firstbuffer, lastbuffer], [firstbuffer, lastbuffer]]
        inparse.defaultinput = [firstbuffer, lastbuffer]
        if not inparse.getparams():
            return "\nNo Changes Have Been Made!"
        firstbuffer, lastbuffer = inparse.userinput
        firstbuffer = int(firstbuffer)
        lastbuffer = int(lastbuffer)
        header = ["Buffer", "Parameter", "Value", "Error", "Linked", "Fixed"]
        line = '-'*120
        spacer = ' '*20
        table = '\n\n'
        for i in range(firstbuffer, lastbuffer+1):
            fitparams.update(data.matrix.buffer(i).fit.function_index.get())
            if len(data.matrix.buffer(i).fit.parameter_error.get()) != len(data.matrix.buffer(i).fit.parameter.get()):
                data.matrix.buffer(i).fit.parameter_error.set([None] * len(data.matrix.buffer(i).fit.parameter.get()))
            temp = []
            if i == firstbuffer:
                for val in header:
                    temp.append(val + spacer[:len(spacer) - len(val)])
                table += ''.join(temp) + "\n" + line + "\n"
            for j in range(len(data.matrix.buffer(i).fit.parameter.get())):
                if j == 0:
                    buffer = str(i)
                else:
                    buffer = ''
                if str(data.matrix.buffer(i).fit.free.get()[j]) == "True":
                    fixed = "False"
                else:
                    fixed = "True"
                lineout = [buffer, fitparams.paramid[j], str(data.matrix.buffer(i).fit.parameter.get()[j]),
                           str(data.matrix.buffer(i).fit.parameter_error.get()[j]),
                           str(data.matrix.buffer(i).fit.link.get()[j]), fixed]
                temp = []
                for val in lineout:
                    temp.append(val + spacer[:len(spacer) - len(val)])
                table += ''.join(temp) + "\n"
        return table

    def do_der(self, *args):
        """\nCommand: calculate DERivative\n
               Description: Calculates the Derivative of a buffer.

               Example Usage:
               \tder 1 10   (Calculates the derivative of data in buffers 1 through 10)

               Default Input: N/A

               Default Options: N/A

               Options: N/A

               Notes: Derivatized data is appended to data matrix as new buffers
               """
        matrixlen = data.matrix.length()
        inparse = inputprocessing.InputParser()
        inparse.prompt = ["First Buffer", "Last Buffer"]
        inparse.inputbounds = [[1, matrixlen], [1, matrixlen]]
        inparse.defaultinput = ['1', str(matrixlen)]
        if not inparse(args):
            return "Invalid input!"
        modifiers = inparse.modifiers
        userflags = inparse.cmdflags
        comparams = inparse.userinput

        min_buf = int(min(comparams))
        max_buf = int(max(comparams))
        for i in range(min_buf, max_buf+1, 1):
            new_buffer = data.Buffer()
            new_buffer.comments.set(data.matrix.buffer(i).comments.all_as_string() + ' (derivative)')
            new_buffer.plot.series.name = data.matrix.buffer(i).plot.series.name + ' (derivative)'
            new_buffer.plot.series.color.set(data.matrix.buffer(i).plot.series.color.get())
            x, y = numericalmethods.calc_derivative(data.matrix.buffer(i).data.x.get(),
                                                    data.matrix.buffer(i).data.y.get())
            new_buffer.data.x.set(x)
            new_buffer.data.y.set(y)
            data.matrix.append_new_buffer(new_buffer)

        return "\n Derivative Data for Buffer: {} through {} are written as Buffers {} through {}".format(*[min_buf, max_buf, matrixlen + 1, matrixlen + (max_buf-min_buf) + 1])

    def do_int(self, *args):
        """\nCommand: calculate running INTegral\n
               Description: Calculates the running integral of a buffer.

               Example Usage:
               \tint 1 10   (Calculates the running integral of data in buffers 1 through 10)

               Default Input: N/A

               Default Options: N/A

               Options: N/A

               Notes: Integral data is appended to data matrix as new buffers
               """
        matrixlen = data.matrix.length()
        inparse = inputprocessing.InputParser()
        inparse.prompt = ["First Buffer", "Last Buffer"]
        inparse.inputbounds = [[1, matrixlen], [1, matrixlen]]
        inparse.defaultinput = ['1', str(matrixlen)]
        if not inparse(args):
            return "Invalid input!"
        modifiers = inparse.modifiers
        userflags = inparse.cmdflags
        comparams = inparse.userinput

        min_buf = int(min(comparams))
        max_buf = int(max(comparams))
        for i in range(min_buf, max_buf + 1, 1):
            new_buffer = data.Buffer()
            new_buffer.comments.set(data.matrix(i).comments.all_as_string() + ' (integral)')
            new_buffer.plot.series.name = data.matrix.buffer(i).plot.series.name + ' (integral)'
            new_buffer.plot.series.color = data.matrix.buffer(i).plot.series.color
            x, y = numericalmethods.calc_integral(data.matrix.buffer(i).data.x.get(),
                                                  data.matrix.buffer(i).data.y.get())
            data.matrix.append_new_buffer(new_buffer)

        return "\n Integral Data for Buffer: {} through {} are written as Buffers {} through {}".format(
            *[min_buf, max_buf, matrixlen + 1, matrixlen + (max_buf - min_buf) + 1])

    def do_pbf(self, *args):
        """\nCommand: Print BuFfer\n
               Description: Displays all details of given buffer.

               Example Usage:
               \tpbf   (Displays all details of first buffer)
               \tpbf 1 (Displays all details of buffer 1)

               Default Input: 1

               Default Options: N/A

               Options: N/A
               """
        inparse = inputprocessing.InputParser()
        if not inparse(args):
            return "Invalid input!"
        userflags = inparse.cmdflags
        comparams = inparse.userinput

        if len(comparams) == 0:
            comparams.append(1)
        buf = int(comparams[0])
        if buf > data.matrix.length():
            buf = data.matrix.length()
        if buf < 1:
            buf = 1

        # code to print dictionary here:
        for key, value in data.matrix.buffer(buf).to_dict().items():
            print(f'{str(key)}: {str(value)}')

        return "\n Showing Details of Buffer: " + str(buf)


    def help(self, cmd=None):
        def std_help():
            qc = '|'.join(self._quit_cmd)
            hc = '|'.join(self._help_cmd)
            res = '\n\tType [%s] command_name to get more help about particular command\n' % hc
            res += '\n\tType [%s] to quit program\n' % qc
            cl = [name[3:] for name in dir(self) if name.startswith('do_') and len(name) > 3]
            res += '\n\tAvailable commands: \n\t%s' % ('  '.join(sorted(cl))) + "\n"
            return res

        if not cmd:
            return std_help()
        else:
            try:
                fn = getattr(self, 'do_' + cmd)
                doc = fn.__doc__
                return doc or 'No documentation available for %s' % cmd
            except AttributeError:
                return std_help()

########################################################################################################################
########################################################################################################################
#############################                Command Related Methods Below                 #############################
########################################################################################################################
########################################################################################################################


def updatefixlnk():
    if data.plot_limits.is_active:
        firstbuffer, lastbuffer = data.plot_limits.buffer_range.get()
    else:
        lastbuffer = data.matrix.length()
        firstbuffer = 1
    for i in range(firstbuffer, lastbuffer+1):
        if len(data.matrix.buffer(i).fit.link.get()) != len(data.matrix.buffer(i).fit.parameter.get()):
            data.matrix.buffer(i).fit.link.set([None] * len(data.matrix.buffer(i).fit.parameter.get()))
            data.matrix.buffer(i).fit.free.set([True] * len(data.matrix.buffer(i).fit.parameter.get()))
    return True


def runscript(scriptfile, interactivemode):
    user_input = None
    commander = commands.Command()
    with open(scriptfile) as script:
        commandlist = script.readlines()
        for command in commandlist:
            if command[0] == "#" or command[0] == '\n':
                continue
            elif command[0] == "!":
                print(command[1:])
                continue
            elif command[0] == "?":
                user_input = input("\n" + command[1:] + "\nResponse: ")
            else:
                if user_input is not None and "[user_input]" in command:
                    command.replace("[user_input]", str(user_input))
                output = commander(command)
                if output and command.lower().strip() != 'quit' and command.lower().strip() != 'q':
                    print(output)
                    user_input = None
                else:
                    sys.exit(0)
            if interactivemode:
                interactiveinput = input("\nPress [q] to stop script, any other key to continue:  ")
                if interactiveinput.lower() == "q":
                    break
    return "\nScript Executed Successfully!"
