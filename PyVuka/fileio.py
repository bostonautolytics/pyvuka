import numpy as np
import xlrd
import xlsxwriter as XL
import xml.etree.ElementTree as xmlio
import base64
from . import plot, fitfxns, inputprocessing
from matplotlib import pyplot as pl
import os
import chardet
import array
import string
from matplotlib import rcParams
import io
from io import BytesIO as BIO
rcParams.update({'figure.autolayout': True})


class IO(object):
    def __init__(self, data_instance):
        self.data = data_instance.data

    def writepvk(self, filename):
        return "File type does not exist yet!"

    def readpvk(self, filename):
        #filetype does not exist yet
        return "File type does not exist yet!"

    def readsvb(self, filename, filestruct):
        return "File read fxn not written yet!"

    def readtxt(self, filename, filestruct, comparams):
        print("Copying text file to memory (process is slow with large files)...\n")
        in_txt = []
        row = "temp"
        col = "temp"
        numstruct = "temp"
        numlines = "temp"
        valerror = "Non-numeric input! Process interrupted!"
        structwidth = 0
        onexcol = False
        xindex = None
        xeindex = None
        yindex = None
        yeindex = None
        zindex = None
        zeindex = None
        iscat = False

        delim = detect_delimiter(filename)

        with open(filename) as textFile:
            for line in textFile:
                in_txt.append(line.split(delim))

        if filestruct == "-y":
            structwidth = 1
            onexcol = True
            yindex = 0
        if filestruct == "-xy" or filestruct == "-ye":
            structwidth = 2
            xindex = 0
            yindex = 1
            if filestruct == "-ye":
                onexcol = True
                xindex = None
                yindex = 0
                yeindex = 1
        elif filestruct == "-xyz" or filestruct == "-xye" or filestruct == "-cye" \
                or filestruct == "-cyz" or filestruct == "-ccz":
            structwidth = 3
            if filestruct == "-xyz":
                xindex = 0
                yindex = 1
                zindex = 2
            elif filestruct == "-xye":
                xindex = 0
                yindex = 1
                yeindex = 2
            elif filestruct == "-cye":
                structwidth = 3
                iscat = True
                xindex = 0
                yindex = 1
                yeindex = 2
            elif filestruct == "-cyz":
                structwidth = 3
                iscat = True
                xindex = 0
                yindex = 1
                zindex = 2
            elif filestruct == "-ccz":
                structwidth = 3
                iscat = True
                xindex = 0
                yindex = 1
                zindex = 2
        elif filestruct == "-xeye":
            structwidth = 4
            xindex = 0
            xeindex = 1
            yindex = 2
            yeindex = 3
        elif filestruct == "-xeyeze":
            structwidth = 6
            xindex = 0
            xeindex = 1
            yindex = 2
            yeindex = 3
            zindex = 4
            zeindex = 5
        inparse = inputprocessing.InputParser()
        inparse.prompt = ["Number of rows from top to skip", "Number of columns from left to skip",
                  "Number of datasets to read (0 is until end of file)", "Number of lines to read (0 is until end of file)"]
        inparse.inputbounds = [[0,1E100],[0,1E100],[0,1E100],[0,1E100]]
        inparse.defaultinput = ['0', '0', '0', '0']
        inparse.userinput = comparams
        row, col, numstruct, numlines = [int(x) for x in inparse.getparams()]
        inparse.userinput = comparams
        if numstruct <= 0:
            numstruct = int(int(len(in_txt[row]) - col)/structwidth)
        if numlines <= 0:
            numlines = int(len(in_txt) - row)
        count = 0
        commonx = []
        maxrow = int(numlines+row)
        maxcol = int((numstruct*structwidth)+col)
        if onexcol:
            for rows in range(row, maxrow):
                commonx.append(float(in_txt[rows][col]))
            col = col+1
        while (col+count < maxcol):
            newbuffer = self.data.new_buffer()
            print("Last column read: " + str(count+structwidth) + " of " + str(maxcol))
            skipped = 0
            for rows in range(row, maxrow):
                valindex = 0
                for cols in range(col + count, col + count + structwidth):
                    if xindex is not None and valindex == xindex:
                        xtemp = in_txt[rows][cols]
                        if xtemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.x.append(float(xtemp))
                            except ValueError:
                                return valerror
                    if xeindex is not None and valindex == xeindex:
                        xetemp = in_txt[rows][cols]
                        if xetemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.xe.append(float(xetemp))
                            except ValueError:
                                return valerror
                    if yindex is not None and valindex == yindex:
                        ytemp = in_txt[rows][cols]
                        if ytemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.y.append(float(ytemp))
                            except ValueError:
                                return valerror
                    if yeindex is not None and valindex == yeindex:
                        yetemp = in_txt[rows][cols]
                        if yetemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.ye.append(float(yetemp))
                            except ValueError:
                                return valerror
                    if zindex is not None and valindex == zindex:
                        ztemp = in_txt[rows][cols]
                        if ztemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.z.append(float(ztemp))
                            except ValueError:
                                return valerror
                    if zeindex is not None and valindex == zeindex:
                        zetemp = in_txt[rows][cols]
                        if zetemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.ze.append(float(zetemp))
                            except ValueError:
                                return valerror
                    if skipped >= 8:
                        break
                    valindex += 1
            count += structwidth
            print(f"\tLines read into buffer: {newbuffer.data.x.length()}")
            if onexcol:
                newbuffer.data.x.set(commonx)
            if iscat:
                newbuffer.category.x.set([str(x) for x in newbuffer.data.x.get()])
                newbuffer.data.x.clear()
            if iscat and filestruct == "-ccz":
                newbuffer.category.y.set([str(x) for x in newbuffer.data.y.get()])
                newbuffer.data.y.clear()
            self.data.matrix.add_buffer(newbuffer)
        self.colorallseries()
        self.buffertoseries()
        self.seriestotitle()
        return "Data has been read into memory."

    def readxlsx(self, filename, filestruct, comparams):
        print("Copying XLSX file to memory (process is slow with large files)...\n")
        in_xlsx = xlrd.open_workbook(filename)
        print("XLSX Sheet Names:")
        row = "temp"
        col = "temp"
        sheet = "temp"
        numstruct = "temp"
        numlines = "temp"
        valerror = "Non-numeric input! Process interrupted!"
        structwidth = 0
        onexcol = False
        xindex = None
        xeindex = None
        yindex = None
        yeindex = None
        zindex = None
        zeindex = None
        iscat = False

        if filestruct == "-y":
            structwidth = 1
            onexcol = True
            yindex = 0
        if filestruct == "-xy" or filestruct == "-ye":
            structwidth = 2
            xindex = 0
            yindex = 1
            if filestruct == "-ye":
                onexcol = True
                xindex = None
                yindex = 0
                yeindex = 1
        elif filestruct == "-xyz" or filestruct == "-xye" or filestruct == "-cye" \
                or filestruct == "-cyz" or filestruct == "-ccz":
            structwidth = 3
            if filestruct == "-xyz":
                xindex = 0
                yindex = 1
                zindex = 2
            elif filestruct == "-xye":
                xindex = 0
                yindex = 1
                yeindex = 2
            elif filestruct == "-cye":
                structwidth = 3
                iscat = True
                xindex = 0
                yindex = 1
                yeindex = 2
            elif filestruct == "-cyz":
                structwidth = 3
                iscat = True
                xindex = 0
                yindex = 1
                zindex = 2
            elif filestruct == "-ccz":
                structwidth = 3
                iscat = True
                xindex = 0
                yindex = 1
                zindex = 2
        elif filestruct == "-xeye":
            structwidth = 4
            xindex = 0
            xeindex = 1
            yindex = 2
            yeindex = 3
        elif filestruct == "-xeyeze":
            structwidth = 6
            xindex = 0
            xeindex = 1
            yindex = 2
            yeindex = 3
            zindex = 4
            zeindex = 5
        inparse = inputprocessing.InputParser()
        inparse.prompt = ["Sheet to read in", "Number of rows from top to skip", "Number of columns from left to skip",
                  "Number of datasets to read (0 is until end of file)", "Number of lines to read (0 is until end of file)"]
        inparse.inputbounds = [[0,1E100],[0,1E100],[0,1E100],[0,1E100],[0,1E100]]
        inparse.defaultinput = ['0', '0', '0', '0', '0']
        inparse.userinput = comparams
        sheet_names = in_xlsx.sheet_names()
        if len(sheet_names) == 1:
            if len(inparse.userinput) > 0:
                inparse.userinput[0] = '0'
            else:
                inparse.userinput.append('0')
        else:
            for name in range(len(sheet_names)):
                print("\t[" + str(name) + "] " + sheet_names[name])
            print("\n")
        sheet, row, col, numstruct, numlines = [int(x) for x in inparse.getparams()]
        inparse.userinput = comparams
        if numstruct <=0:
            numstruct = int(int(in_xlsx.sheet_by_index(sheet).ncols - col)/structwidth)
        if numlines <= 0:
            numlines = int(in_xlsx.sheet_by_index(sheet).nrows - row)
        count = 0
        commonx = []
        maxrow = int(numlines+row)
        maxcol = int((numstruct*structwidth)+col)
        if onexcol:
            for rows in range(row, maxrow):
                commonx.append(float(in_xlsx.sheet_by_index(sheet).cell_value(rows, col)))
            col = col+1
        while (col+count < maxcol):
            newbuffer = self.data.new_buffer()
            print("Last column read: " + str(count+structwidth) + " of " + str(maxcol))
            skipped = 0
            for rows in range(row, maxrow):
                valindex = 0
                for cols in range(col + count, col + count + structwidth):
                    if xindex is not None and valindex == xindex:
                        xtemp = in_xlsx.sheet_by_index(sheet).cell_value(rows, cols)
                        if xtemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.x.append(float(xtemp))
                            except ValueError:
                                return valerror
                    if xeindex is not None and valindex == xeindex:
                        xetemp = in_xlsx.sheet_by_index(sheet).cell_value(rows, cols)
                        if xetemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.xe.append(float(xetemp))
                            except ValueError:
                                return valerror
                    if yindex is not None and valindex == yindex:
                        ytemp = in_xlsx.sheet_by_index(sheet).cell_value(rows, cols)
                        if ytemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.y.append(float(ytemp))
                            except ValueError:
                                return valerror
                    if yeindex is not None and valindex == yeindex:
                        yetemp = in_xlsx.sheet_by_index(sheet).cell_value(rows, cols)
                        if yetemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.ye.append(float(yetemp))
                            except ValueError:
                                return valerror
                    if zindex is not None and valindex == zindex:
                        ztemp = in_xlsx.sheet_by_index(sheet).cell_value(rows, cols)
                        if ztemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.z.append(float(ztemp))
                            except ValueError:
                                return valerror
                    if zeindex is not None and valindex == zeindex:
                        zetemp = in_xlsx.sheet_by_index(sheet).cell_value(rows, cols)
                        if zetemp == '':
                            skipped += 1
                        else:
                            try:
                                newbuffer.data.ze.append(float(zetemp))
                            except ValueError:
                                return valerror
                    if skipped == 6:
                        break
                    valindex += 1
            count += structwidth
            t = newbuffer.data.x.length()
            print(f"\tLines read into buffer: {newbuffer.data.x.length()}")
            if onexcol:
                newbuffer.data.x.set(commonx)
            if iscat:
                newbuffer.category.x.set([str(x) for x in newbuffer.data.x.get()])
                newbuffer.data.x.clear()
            if iscat and filestruct == "-ccz":
                newbuffer.category.y.set([str(x) for x in newbuffer.data.y.get()])
                newbuffer.data.y.clear()
            self.data.matrix.add_buffer(newbuffer)
        self.colorallseries()
        self.buffertoseries()
        self.seriestotitle()
        return "Data has been read into memory."

    def readfb(self, experimentdirectory):
        if not os.path.exists(experimentdirectory):
            return False
        experiment = []
        for files in os.listdir(experimentdirectory):
            if files.endswith('.frd') and not files.startswith('._'):
                Xdata = []
                Ydata = []
                StepName = []
                ActualTime = []
                StepStatus = []
                StepType = []
                Concentration = []
                MolarConcentration = []
                SampleID = []
                WellType = []
                MW = []
                Flags =[]
                SampleGroup = []
                StepLoc = []
                loadingsample = ''
                loadingstart = 0
                loadingend = 0
                loadingwell =''
                infile = xmlio.parse(os.path.join(experimentdirectory, files)).getroot()
                for expinfo in infile.findall('ExperimentInfo'):
                    SensorName = expinfo.find('SensorName').text
                    SensorType = expinfo.find('SensorType').text
                    SensorRole = expinfo.find('SensorRole').text
                    SensorInfo = expinfo.find('SensorInfo').text
                for kindata in infile.findall('KineticsData'):
                    for stepdata in kindata.findall('Step'):
                        for commondata in stepdata.findall('CommonData'):

                            WellType.append(commondata.find('WellType').text)
                            Concentration.append(commondata.find('Concentration').text)
                            MolarConcentration.append(commondata.find('MolarConcentration').text)
                            SampleID.append(commondata.find('SampleID').text)
                            if commondata.find('SampleGroup') is not None:
                                SampleGroup.append(commondata.find('SampleGroup').text)
                            else:
                                SampleGroup.append(None)
                            MW.append(commondata.find('MolecularWeight').text)
                            Xdata.append(np.array(array.array('f', base64.b64decode(stepdata.find('AssayXData').text))))
                            Ydata.append(np.array(array.array('f', base64.b64decode(stepdata.find('AssayYData').text))))
                            StepName.append(stepdata.find('StepName').text)
                            ActualTime.append(stepdata.find('ActualTime').text)
                            StepStatus.append(stepdata.find('StepStatus').text)
                            StepLoc.append(commondata.find('SampleRow').text + commondata.find('SampleLocation').text)
                            StepType.append(stepdata.find('StepType').text)
                            if StepType[-1].upper() == 'LOADING' and SampleID[-1] is not None:
                                loadingsample = SampleID[-1]
                                loadingstart = Ydata[-1][0]
                                loadingend = Ydata[-1][-1]
                                loadingwell = StepLoc[-1]
                for status in StepStatus:
                    if not status == 'OK':
                        Flags.append('Sensor:' + status)
                        break

                newbuffer = self.data.new_buffer()

                ### copy and paste of 'interstepcorrection' method from historical fortebiopkg. edited to suit
                for j in range(0, len(Ydata) - 1):
                    if Ydata[j][-1] > Ydata[j + 1][0]:
                        ydif = Ydata[j][-1] - Ydata[j + 1][0]
                        for k in range(0, len(Ydata[j + 1])):
                            Ydata[j + 1][k] += ydif
                    else:
                        ydif = Ydata[j + 1][0] - Ydata[j][-1]
                        for k in range(0, len(Ydata[j + 1])):
                            Ydata[j + 1][k] -= ydif
                for j in range(0, len(Xdata) - 1):
                    if Xdata[j][-1] < Xdata[j + 1][0]:
                        xdif = Xdata[j + 1][0] - Xdata[j][-1]
                        for k in range(0, len(Xdata[j + 1])):
                            Xdata[j + 1][k] -= xdif
                    else:
                        xdif = Xdata[j][-1] - Xdata[j + 1][0]
                        for k in range(0, len(Xdata[j + 1])):
                            Xdata[j + 1][k] -= xdif

                for segment in Xdata:
                    newbuffer.data.x.append(segment)
                    newbuffer.plot.axis.x.lines.append(segment[0])

                newbuffer.data.x.set(np.concatenate(Xdata, axis=None))
                newbuffer.data.y.set(np.concatenate(Ydata, axis=None))
                ###
                newbuffer.data.z.set([float(MolarConcentration[-2])] * newbuffer.data.y.length())

                newbuffer.comments.set([str(SensorInfo) + " on " + str(SensorType) + " vs " +
                                           str(SampleID[-2]) + " @ " + str(MolarConcentration[-2]) + "nM"])
                newbuffer.plot.series.name.set(newbuffer.comments.get())
                newbuffer.plot.title.set(newbuffer.comments.get())
                newbuffer.plot.axis.x.title.set("Time (s)")
                newbuffer.plot.axis.y.title.set("Response (nm)")
                newbuffer.plot.axis.x.lines.show()
                newbuffer.meta_dict = {'xData': Xdata, 'yData': Ydata,
                                       'stepName': StepName, 'actualTime': ActualTime, 'sensorType': SensorType,
                                       'stepStatus': StepStatus, 'stepType': StepType, 'concentration': Concentration,
                                       'molarConcentration':MolarConcentration, 'sampleID':SampleID,
                                       'wellType': WellType, 'mw': MW, 'flags':Flags, 'sampleGroup': SampleGroup,
                                       'stepLocation': StepLoc, 'loadingSample': loadingsample, 'sensorInfo': SensorInfo,
                                       'loadingStart':loadingstart, 'loadingEnd':loadingend, 'loadingWell':loadingwell,
                                       'inFile':infile, 'sensorName':SensorName}
                self.data.matrix.add_buffer(newbuffer)
        self.colorallseries()
        return "ForteBio data read into memory."

    def readi3x(self, experimentdirectory):
        if not os.path.exists(experimentdirectory):
            return False
        experiment = {"Well": [], "Sample_ID": [], "Y_Signal": [], "Concentration": []}
        filecount = 0
        for files in os.listdir(experimentdirectory):
            if files.endswith('.txt') and ('[' in files and ']' in files):
                filename = os.path.join(experimentdirectory, files)
                concentration = filename.split('[')[1].split(']')[0]
                if concentration[-2:] == "ng":
                    concentration = float(concentration[:-2])*1E-9
                elif concentration[-2:] == "ug":
                    concentration = float(concentration[:-2])*1E-6
                elif concentration[-2:] == "mg":
                    concentration = float(concentration[:-2])*1E-3
                with open(filename) as rawdata:
                    datalines = rawdata.readlines()
                    readdata = False
                    for line in datalines:
                        line = filter(lambda x: x in string.printable, line)
                        if "Sample\tWells\tValue" in line:
                            readdata = True
                        if readdata and "Sample\tWells\tValue" not in line:
                            if "Group Column\tFormula Name" in line or line == '\r\n':
                                break
                            if filecount == 0:
                                temp = line.split('\t')
                                experiment["Sample_ID"].append(temp[0])
                                experiment["Well"].append(temp[1])
                                experiment["Y_Signal"].append([float(temp[2])])
                                experiment["Concentration"].append([concentration])
                            else:
                                temp = line.split('\t')
                                wellindex = experiment["Well"].index(temp[1])
                                experiment["Y_Signal"][wellindex].append(float(temp[2]))
                                experiment["Concentration"][wellindex].append(concentration)
                filecount += 1
        for i in range(len(experiment["Well"])):
            newbuffer = self.data.new_buffer()
            experiment["Concentration"][i], experiment["Y_Signal"][i] = (list(t) for t in zip(*sorted(zip(experiment["Concentration"][i], experiment["Y_Signal"][i]))))
            newbuffer.data.x.set(experiment["Concentration"][i])
            newbuffer.data.y.set(experiment["Y_Signal"][i])
            newbuffer.plot.series.name.set(experiment["Sample_ID"][i] + " (Well: " + experiment["Well"][i] + ")")
            newbuffer.comments.add("Well: "+experiment["Well"][i])
            newbuffer.comments.add("Sample_ID: " + experiment["Sample_ID"][i])
            self.data.matrix.add_buffer(newbuffer)
        self.colorallseries()
        self.seriestotitle()
        return "Data has been read into memory."

    def writexlsx(self, filename, **kwargs):
        xlsx = xlsx_out(filename)
        xlsx.sheet_name = kwargs.get("sheet_name")
        xlsx.add_header(kwargs.get("header_list"))
        xlsx.set_col_widths(kwargs.get("col_width_list"))
        xlsx.set_row_heights(kwargs.get("row_heights"))

        plot_out = plot.plotter()

        fitter = fitfxns.datafit()
        fitter.funcindex = self.data.matrix.buffer(1).fit.function_index.get()
        fitter.applyfxns()

        if not xlsx.header:
            auto_header = ['Sample']
            for val in fitter.paramid:
                auto_header.extend([val, str(val + '_error')])
            auto_header.extend(['xsq', 'rsq', 'plot'])
            xlsx.add_header(auto_header)

        if not xlsx.row_heights:
            xlsx.set_row_heights(152)

        if not xlsx.col_widths:
            xlsx.set_col_widths([20] * len(xlsx.header))

        if not xlsx.sheet_name:
            xlsx.sheet_name = "Output"

        for i in range(1, self.data.matrix.length() + 1):
            xl_line = []
            buffer = self.data.matrix.buffer(i)
            xl_line.extend([buffer.plot.series.name.get()])
            for j in range(len(buffer.fit.parameter.get())):
                xl_line.extend([buffer.fit.parameter.get()[j]])
                xl_line.extend([buffer.fit.parameter_error.get()[j]])
            xl_line.append(buffer.fit.chisq.get())
            xl_line.append(buffer.fit.rsq.get())
            xl_line.append(BIO(plot_out([i], get_bytes=True)))
            xlsx.add_line(xl_line)
        xlsx.write_xlsx()

        for i in range(1, self.data.matrix.length() + 1):
            xlsx = xlsx_out(filename[:-5] + f"_sensor{i}_raw.xlsx")
            xlsx.sheet_name = "Output"
            xlsx.add_line([buffer.plot.series.name.get(), 'X', 'Y', 'X-breaks']) #header
            buffer = self.data.matrix.buffer(i)
            tbufx = buffer.data.x.get()
            tbufy = buffer.data.y.get()
            tbreakx = buffer.plot.axis.x.lines.get()
            for j in range(len(tbufx)):
                if j < len(tbreakx):
                    xlsx.add_line(['', tbufx[j], tbufy[j], tbreakx[j]])
                else:
                    xlsx.add_line(['', tbufx[j], tbufy[j]])
            xlsx.write_xlsx()
        return

    def colorallseries(self):
        start = 0.0
        stop = 1.0
        number_of_buffers = self.data.matrix.length()
        cm_subsection = np.linspace(start, stop, number_of_buffers)

        colors = [pl.cm.gist_rainbow(x) for x in cm_subsection]

        for i, color in enumerate(colors):
            self.data.matrix.buffer(i).plot.series.color.set(color)
        return True

    def buffertoseries(self):
        for i in range(self.data.matrix.length()):
            self.data.matrix.buffer(i).plot.series.name.set(f"Buffer {i + 1}")
        return True

    def seriestotitle(self):
        for i in range(self.data.matrix.length()):
            self.data.matrix.buffer(i).plot.title.set(self.data.matrix.buffer(i).plot.series.name.get())
        return True


class xlsx_out(object):
    def __init__(self, filename):
        """Return an xlsx object whose name is filename """
        self.filename = filename
        self.matrix = []
        self.header = []
        self.col_widths = []
        self.row_heights = []
        self.sheet_name = 'output'

    def add_line(self, write_array):
        self.matrix.append(write_array)
        return

    def add_header(self, write_array):
        self.header = write_array
        return

    def set_col_widths(self, widths):
        if not widths:
            return
        maxcol = -10
        if ',' in str(widths):
            array_out = list(widths)
        else:
            if not self.header:
                self.col_widths = widths
                return
            if len(self.header) > maxcol:
                maxcol = len(self.header)
            for line in self.matrix:
                if len(line) > maxcol:
                    maxcol = len(line)
            array_out = [widths for j in range(maxcol)]
        self.col_widths = array_out
        return

    def set_row_heights(self, heights):
        if not self.header:
            header = 0
        else:
            header = 1
        if not heights:
            return
        maxrow = -10
        if ',' in str(heights):
            array_out = list(heights)
        else:
            if not self.matrix:
                self.row_heights = heights
                return
            elif len(self.matrix) > maxrow:
                maxrow = len(self.matrix)
            array_out = [heights for j in range(maxrow + header)]
        self.row_heights = array_out
        return

    def write_xlsx(self):
        self.set_row_heights(self.row_heights)
        self.set_col_widths(self.col_widths)
        wb = XL.Workbook(self.filename)
        ws = []
        ws.append(wb.add_worksheet(self.sheet_name))
        header = 0

        if self.header:
            for i in range(len(self.header)):
                ws[0].write(0, i, self.header[i])
            ws[0].freeze_panes(1, 0)
            header = 1

        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[i])):
                var_type = str(type(self.matrix[i][j]))
                if '_io.BytesIO' in var_type:
                    ws[0].insert_image(i + header, j, 'figure.png',
                                       {'image_data': self.matrix[i][j], 'x_scale': 1, 'y_scale': 1})
                else:
                    ws[0].write(i + header, j, self.matrix[i][j])

        if self.col_widths:
            for i in range(len(self.col_widths)):
                ws[0].set_column(i, i, self.col_widths[i])

        if self.row_heights:
            for i in range(len(self.row_heights)):
                ws[0].set_row(i, self.row_heights[i])
            if self.header:
                ws[0].set_row(0, 18)

        wb.close()
        return


def detect_delimiter(filename):
    '''Determine if comma or tab delimited'''
    encode_type = predict_encoding(filename)
    with io.open(filename, 'r', encoding=encode_type) as textFile:
        linein = textFile.readline()
        if len(linein.split(',')) < len(linein.split('\t')):
            return '\t'
        else:
            return ','


def predict_encoding(file_path, n_lines=20):
    '''Predict a file's encoding using chardet'''
    # Open the file as binary data
    with open(file_path, 'rb') as f:
        # Join binary lines for specified number of lines
        rawdata = b''.join([f.readline() for _ in range(n_lines)])
    return chardet.detect(rawdata)['encoding']

