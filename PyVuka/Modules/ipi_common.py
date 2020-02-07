#!/usr/bin/env python
#title           :ipi_common.py
#author          :R. Paul Nobrega, IPI
#contact         :Paul.Nobrega@ProteinInnovation.com
#description     :This file is a collection of common modules for the Institue
#                 of Protein Innovation custom python scripts. Functions are
#                 specific to data IO and general data handling.
#usage           :Pyvuka module
#python_version  :3.7
#==============================================================================
import datetime
import os
import re
import io
import xlsxwriter as XL
import scipy
import chardet
import matplotlib
matplotlib.use('Agg')
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
import matplotlib.pyplot as pl
from matplotlib.ticker import MaxNLocator
import matplotlib.patheffects as pe
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
from io import BytesIO as BIO
from PIL import Image
import shutil
import errno
import multiprocessing
import psutil
import smtplib
from PyVuka import data_obj as data
import stat


##################################################
####  Suportting  Functions Below This Point  ####
##################################################
def local_matrix_to_global_matrix(datamatrix):
    data.matrix = datamatrix
    return True


def find_peaks(one_D_val_list, amp_co, distance_co, rel_peak_co, max_peak_num):
    y_vals = one_D_val_list

    # Get all peaks
    peaks, _ = scipy.signal.find_peaks(y_vals, height=amp_co, distance=distance_co)

    # Sort peaks by y-val
    peak_indx_y = []
    for i in range(len(peaks)):
        peak_indx_y.append([peaks[i], y_vals[peaks[i]]])
    peak_indx_y = sorted(peak_indx_y, key=lambda k: [k[1], k[0]])

    # del items that do not fit rel_peak parameter
    if rel_peak_co is not None:
        max_peak_y = -1E6
        if peak_indx_y:
            max_peak_y = peak_indx_y[-1][1]
        for i in reversed(range(len(peak_indx_y))):
            if (peak_indx_y[i][1] / max_peak_y) * 100 < rel_peak_co:
                del peak_indx_y[i]

    # del peaks that are not local maxima
    idx_shift = int(len(y_vals)*.025)
    for i in reversed(range(len(peak_indx_y))):
        if int(peak_indx_y[i][0]) - idx_shift > 0 and int(peak_indx_y[i][0]) + idx_shift < len(y_vals) - 1:
            trunc_y = y_vals[int(peak_indx_y[i][0]) - idx_shift:int(peak_indx_y[i][0]) + idx_shift]
            if peak_indx_y[i][1] < max(trunc_y):
                del peak_indx_y[i]
        else:
            del peak_indx_y[i]

    # trim to peak counts corresponding to max_peak_num
    peak_indx_y.reverse()
    if len(peak_indx_y) > max_peak_num:
        peak_indx_y = peak_indx_y[:max_peak_num]

    # reconstruct peak list
    peaks = []
    for pair in peak_indx_y:
        peaks.append(pair[0])
    return peaks


def remove_outliers_2d(matrix, SD_CO=2, bins=100, *, slice='xy'):
    '''Assume input xy list constructs 2D XY scatter. This method will bin X and Y values to remove points outside SD limit'''
    # sort incoming list smallest to largest
    y_sorted_matrix = sorted(matrix, key=lambda k: [k[1], k[0]])
    x_sorted_matrix = sorted(matrix, key=lambda k: [k[0], k[1]])
    y_del_map = [False] * len(y_sorted_matrix)
    x_del_map = [False] * len(x_sorted_matrix)
    x_val, y_val = zip(*y_sorted_matrix)
    min_x = min(x_val)
    max_x = max(x_val)
    min_y = min(y_val)
    max_y = max(y_val)
    x_bin_inc = (max_x - min_x + 1)/bins
    y_bin_inc = (max_y - min_y + 1) / bins
    x_bounds = []
    y_bounds = []
    #########################################################
    # Bin by Y and filter out based on x val
    #########################################################
    if 'y' in slice.lower():
        start_index = 0
        stop_index = 0
        for i in range(bins):
            y_band_min = min_y + (y_bin_inc * i)
            y_band_max = y_band_min + y_bin_inc
            for j in range(start_index, len(y_val), 1):
                if y_val[j] <= y_band_min:
                    start_index = j
                elif y_val[j] <= y_band_max:
                    stop_index = j
                else:
                    break
            if start_index < stop_index:
                mean = np.mean(x_val[start_index:stop_index], axis=0)
                sd = np.std(x_val[start_index:stop_index], axis=0)
                avg_y = np.mean(y_val[start_index:stop_index], axis=0)
                x_bounds.append([tuple([mean-(sd*SD_CO), avg_y]), tuple([mean+(sd*SD_CO), avg_y])])
                for k in range(start_index, stop_index, 1):
                    if y_sorted_matrix[k][0] < mean - SD_CO * sd or y_sorted_matrix[k][0] > mean + SD_CO * sd:
                        y_del_map[k] = True
            start_index = stop_index

    #########################################################
    # Bin by X and filter out based on y val
    #########################################################
    if 'x' in slice.lower():
        x_val, y_val = zip(*x_sorted_matrix)
        start_index = 0
        stop_index = 0
        for i in range(bins):
            x_band_min = min_x + (x_bin_inc * i)
            x_band_max = x_band_min + x_bin_inc
            for j in range(start_index, len(x_val), 1):
                if x_val[j] <= x_band_min:
                    start_index = j
                elif x_val[j] <= x_band_max:
                    stop_index = j
                else:
                    break
            if start_index < stop_index:
                mean = np.mean(y_val[start_index:stop_index], axis=0)
                sd = np.std(y_val[start_index:stop_index], axis=0)
                avg_x = np.mean(x_val[start_index:stop_index], axis=0)
                y_bounds.append([tuple([avg_x, mean-(sd*SD_CO)]), tuple([avg_x, mean+(sd*SD_CO)])])
                for k in range(start_index, stop_index, 1):
                    if x_sorted_matrix[k][1] < mean - SD_CO * sd or x_sorted_matrix[k][1] > mean + SD_CO * sd:
                        x_del_map[k] = True
            start_index = stop_index

    #########################################################
    # Apply del map to sorted_matrix
    #########################################################
    clean_matrix = []
    for i in range(len(y_sorted_matrix)):
        if not y_del_map[i]:
            clean_matrix.append(y_sorted_matrix[i])
    del_clean_matrix = [False] * len(clean_matrix)
    for i in range(len(x_sorted_matrix)):
        if x_del_map[i] and x_sorted_matrix[i] in clean_matrix:
            del_clean_matrix[clean_matrix.index(x_sorted_matrix[i])] = True
    for i in reversed(range(len(clean_matrix))):
        if del_clean_matrix[i]:
            del clean_matrix[i]

    return clean_matrix, x_bounds, y_bounds


def calc_integral(buffer, start_idx, stop_idx):
    # not the best way to calculate this, but output matches AKTA software
    integral = 0.000
    min_y = min(buffer.item['y_val'])
    x_vals = np.array(buffer.item['x_val'][start_idx:stop_idx])
    y_vals = np.array(buffer.item['y_val'][start_idx:stop_idx]) - min_y
    temp = np.average(np.diff(x_vals))
    integral = sum(y_vals * temp)
    return integral


def calc_linear_fit(x_list, y_list):
    """ Computes the least-squares solution to a linear matrix equation. """
    N = len(x_list)
    x_avg = sum(x_list) / N
    y_avg = sum(y_list) / N
    var_x, cov_xy = 0, 0
    for x, y in zip(x_list, y_list):
        temp = x - x_avg
        var_x += temp ** 2
        cov_xy += temp * (y - y_avg)
    slope = cov_xy / var_x
    y_interc = y_avg - slope * x_avg
    return (slope, y_interc)


def predict_encoding(file_path, n_lines=20):
    '''Predict a file's encoding using chardet'''
    # Open the file as binary data
    with open(file_path, 'rb') as f:
        # Join binary lines for specified number of lines
        rawdata = b''.join([f.readline() for _ in range(n_lines)])

    return chardet.detect(rawdata)['encoding']


def txt_to_list(filename):
    # Read in text file
    in_txt = []
    encode_type = predict_encoding(filename)
    delim = detect_delimiter(filename)
    with io.open(filename, 'r', encoding=encode_type) as textFile:
        for line in textFile:
            in_txt.append(line.split(delim))
    return in_txt


def detect_delimiter(filename):
    '''Determine if comma or tab delimited'''
    encode_type = predict_encoding(filename)
    with io.open(filename, 'r', encoding=encode_type) as textFile:
        linein = textFile.readline()
        if len(linein.split(',')) < len(linein.split('\t')):
            return '\t'
        else:
            return ','


def is_float(input):
    try:
        num = float(input)
    except ValueError:
        return False
    return True


def is_int(input):
    try:
        num = int(input)
    except ValueError:
        return False
    return True


def get_file_list(folder, ext):
    '''Returns filelist of all files within a folder having a prescribed extension

    Parameters
    ----------
    folder: types.StringType object
        Description of 'folder'. Valid OS path of directory containing files to construct a list of
    ext: types.StringType object
        Description of 'ext'. File extension to filter file list by

    Returns
    ----------
    types.ListType object of types.StringType objects
        Returns list of valid OS path filenames
    '''
    file_list = list(filter(lambda x: x.lower().endswith(ext), os.listdir(folder)))
    # Make full path and sort for most recent modification date first, and return
    return sorted([os.path.join(folder, f) for f in file_list], key=(lambda x: os.path.getmtime(x))) if len(file_list) > 0 else []


def get_file_list_nested(folder, ext):
    '''Returns filelist of all files within a folder and subfolders when having a prescribed extension

    Parameters
    ----------
    folder: types.StringType object
        Description of 'folder'. Valid OS path of directory containing files to construct a list of
    ext: types.StringType object
        Description of 'ext'. File extension to filter file list by

    Returns
    ----------
    types.ListType object of types.StringType objects
        Returns list of valid OS path filenames
    '''

    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(folder):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]

    return_list = sorted(list(filter(lambda x: x.lower().endswith(ext), listOfFiles)))

    return return_list if len(return_list) > 0 else []


def change_file_ext(filename, new_ext):
    if new_ext[0] != '.':
        new_ext = '.' + new_ext
    base, _ = os.path.splitext(filename)
    # if file already exists, make change
    if os.path.isfile(filename):
        os.rename(filename, base + new_ext)
    # return new filename
    return base + new_ext


'''def find_nearest(array, value):
    array = np.asarray(array)
    subarray = np.abs(array - value)
    idx = subarray.argmin()
    return idx'''


def colorallseries(datamatrix):
    start = 0.0
    stop = 1.0
    number_of_buffers = len(datamatrix)
    cm_subsection = np.linspace(start, stop, number_of_buffers)

    colors = [pl.cm.gist_rainbow(x) for x in cm_subsection]

    for i, color in enumerate(colors):
        datamatrix[i].item['series_color'] = color
    return datamatrix


def seriestotitle(datamatrix):
    for i in range(1, len(datamatrix) + 1):
        datamatrix.buffer(i).plot.title.set(datamatrix.buffer(i).plot.series.name.get())
    return datamatrix


def native_extract_nested_zip(zippedFile, toFolder):
    """ Extract a zip file including any nested zip files
        Delete the zip file(s) after extraction
        7zip used for windows and unzip for unix.

        System level operations are waaayyy faster than zipfile
    """
    command = 'unzip -n \"{}\" -d \"{}\"'.format(*[zippedFile, toFolder])
    if os.name == 'nt':
        if os.path.isfile(r"C:\Program Files\7-Zip\7z.exe"):
            zipexc = r'C:\PROGRA~1\7-Zip\7z.exe'
        else:
            zipexc = '7z.exe'
        command = '{} x \"{}\" -o\"{}\" -aos'.format(*[zipexc, zippedFile, toFolder])
    os.system(command)
    #os.remove(zippedFile)
    for root, dirs, files in os.walk(toFolder):
        for filename in files:
            if re.search(r'\.zip$', filename):
                fileSpec = os.path.join(root, filename)
                command = 'unzip -n \"{}\" -d \"{}\"'.format(*[fileSpec, root])
                if os.name == 'nt':
                    if os.path.isfile(r"C:\Program Files\7-Zip\7z.exe"):
                        zipexc = r'C:\PROGRA~1\7-Zip\7z.exe'
                    else:
                        zipexc = '7z.exe'
                    command = '{} x \"{}\" -o\"{}\" -aos'.format(*[zipexc, fileSpec, root])
                os.system(command)
                #os.remove(fileSpec)
                for new_file in os.listdir(root):
                    if '.zip' not in new_file:
                        file_out = os.path.basename(root) + '!' + new_file
                        if not os.path.isfile(os.path.join(toFolder, file_out)):
                            shutil.copy(os.path.join(root, new_file), os.path.join(toFolder, file_out))
    return True


def native_copy(src, dest):
    """For Large Files, This is waaayyyy faster than shutil"""
    command = 'copy' if os.name == 'nt' else 'cp'
    os.system('{} \"{}\" \"{}\"'.format(*[command, src, dest]))
    return True


def native_copy_nested(src, dest):
    """For Large File trees, This is waaayyyy faster than shutil"""
    if os.name == 'nt':
        os.system('Xcopy /E /I /Y \"{}\" \"{}\"'.format(*[src, dest]))
    else:
        os.system('yes | cp -a \"{}.\" \"{}\"'.format(*[src, dest]))
    return True


def remove_all_folder(folder):
    def on_rm_error(func, path, exc_info):
        # path contains the path of the file that couldn't be removed
        # let's just assume that it's read-only and unlink it.
        os.chmod(path, stat.S_IWRITE)
        os.unlink(path)

    shutil.rmtree(folder, onerror=on_rm_error)
    return True


def move_file(src, dest):
    return shutil.move(src, dest)


def move_entire_directory(src, dest):
    try:
        shutil.copytree(src, dest)
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        else:
            return 'ERROR: Directory not copied: %s' % str(e)
    shutil.rmtree(src, True, None)
    return dest


def create_IPI_output_dir(parent_output_dir):
    today = datetime.date.today()
    month = today.strftime('%m')
    day = today.strftime('%d')
    year = today.strftime('%Y')
    year_dir = os.path.join(parent_output_dir, year)
    month_dir = os.path.join(year_dir,month)
    day_dir = os.path.join(month_dir, day)
    dir_hierarchy = [parent_output_dir, year_dir, month_dir, day_dir]
    return list(map(lambda x: check_directory(x), dir_hierarchy))[-1]


def check_directory(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name


def calc_derivative(x_list, y_list):
    x_out = []
    y_out = []
    for i in range(len(x_list)):
        if i == 0:
            x_out.append(x_list[i])
            y_out.append((y_list[i+1] - y_list[i]) / (x_list[i+1] - x_list[i]))
        else:
            x_out.append(x_list[i])
            y_out.append((y_list[i] - y_list[i-1]) / (x_list[i] - x_list[i-1]))
    return x_out, y_out


def safe_execute(default, exception, function, *args):
    '''
    Executes passed function in try / except
    Borrowed from: https://stackoverflow.com/questions/36671077/one-line-exception-handling/36671208
    :param default: Value to return upon exception
    :param exception: Specific Exception to catch
    :param function: Function to evaluate within try
    :param args: Arguments for function being passed
    :return: Result of successful execution of function or 'default' upon Exception
    '''
    try:
        return function(*args)
    except exception:
        return default
##################################################
####      Object Classes Below This Point     ####
##################################################
class buffer(object):
    def __init__(self):
        self.item = {}
        self.item['x_val'] = []
        self.item['xe_val'] = []
        self.item['y_val'] = []
        self.item['ye_val'] = []
        self.item['z_val'] = []
        self.item['ze_val'] = []
        self.item['x_category'] = []
        self.item['y_category'] = []
        self.item['x_model'] = []
        self.item['y_model'] = []
        self.item['z_model'] = []
        self.item['x_residuals'] = []
        self.item['y_residuals'] = []
        self.item['z_residuals'] = []
        self.item['instrument_response_x'] = []
        self.item['instrument_response_y'] = []
        self.item['instrument_response_z'] = []
        self.item['fit_fxn'] = []
        self.item['fit_fxn_index'] = []
        self.item['parameters'] = []
        self.item['parameters_error'] = []
        self.item['fit_xsq'] = 0
        self.item['fit_rsq'] = 0
        self.item['link'] = []
        self.item['free'] = []
        self.item['comments'] = []
        self.item['series_name'] = ''
        self.item['series_color'] = ''
        self.item['series_type'] = ''
        self.item['series_weight'] = 10
        self.item['plot_stack'] = []
        self.item['data_point_range'] = []
        self.item['plot_type'] = ""
        self.item['plot_title'] = ""
        self.item['plot_x_axis_title'] = ""
        self.item['plot_y_axis_title'] = ""
        self.item['plot_z_axis_title'] = ""
        self.item['plot_x_axis_type'] = "linear"
        self.item['plot_y_axis_type'] = "linear"
        self.item['plot_z_axis_type'] = "linear"
        self.item['plot_x_axis_range'] = []
        self.item['plot_y_axis_range'] = []
        self.item['plot_z_axis_range'] = []
        self.item['plot_y_lines'] = []
        self.item['plot_x_lines'] = []
        self.item['plot_polygons'] = []
        self.item['plot_peak_bounds'] = []
        self.item['plot_peaks'] = []
        self.item['plot_integrals'] = []
        self.item['plot_show_y_lines'] = False
        self.item['plot_show_x_lines'] = False
        self.item['plot_show_polygons'] = False
        self.item['plot_show_peak_bounds'] = False
        self.item['plot_show_peaks'] = False
        self.item['plot_show_integrals'] = False
        self.item['plot_show_unity'] = False
        self.item['plot_show_x_error_bars'] = False
        self.item['plot_show_y_error_bars'] = False
        self.item['plot_show_z_error_bars'] = False
        self.item['plot_show_integrals'] = False
        self.item['plot_show_peak_bounds'] = False
        self.item['plot_show_peaks'] = False
        self.item['plot_show_legend'] = False
        self.item['plot_unweighted_residuals'] = False


class xlsx_out(object):

    def __init__(self, filename):
        """Return an xlsx object whose name is filename """
        self.filename = filename
        self.matrix = []
        self.header = []
        self.col_widths = []
        self.row_heights = []
        self.sheet_name = 'output'
        self.lims_upload = True
        self.manual_review = False
        self.experiment = 'None'

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

    def __copy_to_lims_dir(self):
        output_full_name = self.filename
        file_name = os.path.basename(self.filename)
        main_dir = os.path.abspath(os.path.splitdrive(output_full_name)[0])
        upload_dir_file = os.path.join(main_dir, 'lims_upload', file_name)
        print("\nCopying processed data to LIMS dir: " + upload_dir_file)
        print(output_full_name + ' --> ' + os.path.splitext(upload_dir_file)[0] + '_' + self.experiment.upper() + os.path.splitext(upload_dir_file)[1])
        shutil.copy(output_full_name, os.path.splitext(upload_dir_file)[0] + '_' +
                    self.experiment.upper() + os.path.splitext(upload_dir_file)[1])

    def write_xlsx(self):
        self.set_row_heights(self.row_heights)
        self.set_col_widths(self.col_widths)
        wb = XL.Workbook(self.filename)
        ws = []
        ws.append(wb.add_worksheet(self.sheet_name))
        header = 0
        fail_format = wb.add_format({'bold': True, 'bg_color': '#FFC7CE'})
        pass_format = wb.add_format({'bold': True, 'bg_color': '#C6EFCE'})

        if self.header:
            for i in range(len(self.header)):
                ws[0].write(0, i, self.header[i])
            ws[0].freeze_panes(1, 0)
            header = 1

        if self.col_widths:
            if not isinstance(self.col_widths, list):
                self.col_widths = [float(self.col_widths)] * int(len(self.header))
            for i in range(len(self.col_widths)):
                ws[0].set_column(i, i, self.col_widths[i])

        if self.row_heights:
            if not isinstance(self.row_heights, list):
                self.row_heights = [float(self.row_heights)] * int(len(self.header))
            for i in range(len(self.row_heights)):
                ws[0].set_row(i, self.row_heights[i])
            if self.header:
                ws[0].set_row(0, 18)

        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[i])):
                var_type = str(type(self.matrix[i][j])).lower()
                var_to_str = str(self.matrix[i][j]).lower()
                if 'bytesio' in var_type:
                    # if image, scale to cell height
                    img_out = Image.open(self.matrix[i][j])
                    img_width, img_height = img_out.size
                    # 1.33 is used to correct xlsx cell height to px
                    scalar = (self.row_heights[i+header] * 1.33)/img_height
                    # insert image, with scaling
                    ws[0].insert_image(i+header, j, 'figure.png',
                                   {'image_data': self.matrix[i][j], 'x_scale': scalar, 'y_scale': scalar})
                elif var_to_str in ['true', 'pass'] or 'true' in var_to_str:
                    ws[0].write(i + header, j, self.matrix[i][j], pass_format)
                elif var_to_str in ['false', 'fail'] or 'fail' in var_to_str:
                    ws[0].write(i + header, j, self.matrix[i][j], fail_format)
                elif var_to_str in ['inf', '-inf', 'nan'] and ('float' in var_type or 'int' in var_type):
                    ws[0].write(i + header, j, -1)
                else:
                    ws[0].write(i+header, j, self.matrix[i][j])
        wb.close()
        if self.lims_upload:
            self.__copy_to_lims_dir()
        else:
            new_name = os.path.splitext(self.filename)[0] + '_' + self.experiment + os.path.splitext(self.filename)[1]
            if os.path.isfile(new_name):
                os.remove(new_name)
            os.rename(self.filename, new_name)
            if self.manual_review:
                email = emailer()
                email.send_to_all('ATTN: Review Data',
                                  'The following data requires manual review before upload to the LIMS. '
                                  'Please edit the XLSX file accordingly, then copy the file to the '
                                  '\'lims_upload\' directory within the'
                                  ' Automation folder.\n\nFile:\t{}'.format(new_name))
        return


class plotter(object):
    def __init__(self):
        pl.close('all')
        print("Plotting...")

    def __call__(self, buffer, *args, **kwargs):
        return_bytes = False
        dpi = 50

        if 'get_bytes' in kwargs:
            return_bytes = bool(kwargs['get_bytes'])
        if 'dpi' in kwargs:
            dpi = int(kwargs['dpi'])

        plot_type = self.__get_plot_type(buffer)

        if plot_type == 'heatmap':
            pl = self.__heatmap(buffer, *args, **kwargs)
        else:
            pl = self.__scatterline(buffer, plot_type, *args, **kwargs)

        if return_bytes:
            return self.__get_byte_png(pl, dpi=dpi)
        return "Plotting Complete"

    def __get_plot_type(self, buffer):
        all_plots = ['scatter', 'line', 'heatmap']
        default = 'scatter'

        plot_type = buffer.item['plot_type']

        if plot_type.lower() in all_plots:
            return plot_type.lower()

        X = np.array(buffer.item['x_val'])
        XE = np.array(buffer.item['xe_val'])
        Y = np.array(buffer.item['y_val'])
        YE = np.array(buffer.item['ye_val'])
        Z = np.array(buffer.item['z_val'])
        ZE = np.array(buffer.item['ze_val'])
        X_model = np.array(buffer.item['x_model'])
        Y_model = np.array(buffer.item['y_model'])
        Z_model = np.array(buffer.item['z_model'])
        X_cat = buffer.item['x_category']
        Y_cat = buffer.item['y_category']

        if len(X) > 1 and len(Y) > 1 and len(Z) == 0 and (len(X_model) == 0 or len(Y_model) == 0):
            return 'line'
        elif len(X_cat) > 1 and len(Y_cat) > 1 and len(Z) > 1:
            return 'heatmap'
        return default

    def __heatmap(self, buffer, *args, **kwargs):
        X = np.array(buffer.item['x_val'])
        Y = np.array(buffer.item['y_val'])
        Z = np.array(buffer.item['z_val'])
        X_cat = buffer.item['x_category']
        Y_cat = buffer.item['y_category']
        X_title = buffer.item['plot_x_axis_title']
        Y_title = buffer.item['plot_y_axis_title']
        Z_title = buffer.item['plot_z_axis_title']
        plot_title = buffer.item['plot_title']

        X_axis = X if not X_cat else X_cat
        Y_axis = Y if not Y_cat else Y_cat

        data = Z.reshape((len(Y_axis), len(X_axis)))

        data = np.array(data)

        fig, ax = pl.subplots()
        pl.rcParams["font.size"] = 10
        pl.gca().tick_params(axis='y', pad=8)
        pl.gca().tick_params(axis='x', pad=8)

        # Plot the heatmap
        im = ax.imshow(data, cmap=matplotlib.cm.rainbow)

        # We want to show all ticks...
        ax.set_xticks(np.arange(data.shape[1]))
        ax.set_yticks(np.arange(data.shape[0]))
        # ... and label them with the respective list entries.
        ax.set_xticklabels(X_axis)
        ax.set_yticklabels(Y_axis)
        pl.xlabel(X_title)
        pl.ylabel(Y_title)

        # Let the horizontal axes labeling appear on top.
        ax.tick_params(top=True, bottom=False,
                       labeltop=True, labelbottom=False)

        # Rotate the tick labels and set their alignment.
        pl.setp(ax.get_xticklabels(), rotation=-30, ha="right",
                 rotation_mode="anchor")

        # Turn spines off and create white grid.
        for edge, spine in ax.spines.items():
            spine.set_visible(False)
        ax.set_xticks(np.arange(data.shape[1] + 1) - .5, minor=True)
        ax.set_yticks(np.arange(data.shape[0] + 1) - .5, minor=True)
        ax.grid(which="minor", color="w", linestyle='-', linewidth=2)
        ax.tick_params(which="minor", bottom=False, left=False)

        # Loop over data dimensions and create text annotations.
        for i in range(len(Y_axis)):
            for j in range(len(X_axis)):
                ax.text(j, i, data[i, j], ha="center", va="center", color='k')

        if len(plot_title) > 1:
            ax.set_title(plot_title, pad=30, loc='center')

        # Create colorbar
        # create an axes on the right side of ax. The width of cax will be 5%
        # of ax and the padding between cax and ax will be fixed at 0.1 inch.
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        cbar = pl.colorbar(im, cax=cax)
        cbar.ax.set_ylabel(Z_title, rotation=-90, va="bottom", labelpad=5)

        fig.canvas.flush_events()
        return pl

    def __scatterline(self, buffer, plot_type, *args, **kwargs):
        return_bytes = False
        black_models = False

        if 'get_bytes' in kwargs:
            return_bytes = bool(kwargs['get_bytes'])
        if 'black_models' in kwargs:
            black_models = kwargs['black_models']

        # Plot Data-model
        xmin = min(buffer.item['x_val'])
        xmax = max(buffer.item['x_val'])

        #####################################
        # declare variables to tidy up code #
        # ___________________________________#
        X = np.array(buffer.item['x_val'])
        XE = np.array(buffer.item['xe_val'])
        Y = np.array(buffer.item['y_val'])
        YE = np.array(buffer.item['ye_val'])
        Z = np.array(buffer.item['z_val'])
        ZE = np.array(buffer.item['ze_val'])
        X_model = np.array(buffer.item['x_model'])
        Y_model = np.array(buffer.item['y_model'])
        Z_model = np.array(buffer.item['z_model'])
        X_resid = np.array(buffer.item['x_residuals'])
        Y_resid = np.array(buffer.item['y_residuals'])
        Z_resid = np.array(buffer.item['z_residuals'])
        series_color = [val if val != '' else 'red' for val in [buffer.item['series_color']]][0]
        series_weight = float(buffer.item['series_weight'])
        x_axis_title = str(buffer.item['plot_x_axis_title'])
        y_axis_title = str(buffer.item['plot_y_axis_title'])
        z_axis_title = str(buffer.item['plot_z_axis_title'])
        show_x_lines = bool(buffer.item['plot_show_x_lines'])
        x_lines = buffer.item['plot_x_lines']
        show_y_lines = bool(buffer.item['plot_show_y_lines'])
        y_lines = buffer.item['plot_y_lines']
        show_peaks = bool(buffer.item['plot_show_peaks'])
        peak_indicies = buffer.item['plot_peaks']
        show_peak_bounds = buffer.item['plot_show_peak_bounds']
        peak_bounds_indicies = buffer.item['plot_peak_bounds']
        show_integrals = bool(buffer.item['plot_show_integrals'])
        integral_indicies_pairs = buffer.item['plot_integrals']
        show_polygons = bool(buffer.item['plot_show_polygons'])
        polygon_verticies = buffer.item['plot_polygons']
        x_axis_type = str(buffer.item['plot_x_axis_type'])
        y_axis_type = str(buffer.item['plot_y_axis_type'])
        z_axis_type = str(buffer.item['plot_z_axis_type'])
        x_axis_range = buffer.item['plot_x_axis_range']
        y_axis_range = buffer.item['plot_y_axis_range']
        z_axis_range = buffer.item['plot_z_axis_range']
        # ___________________________________#
        # END Local Variable Definitions    #
        #####################################

        fig, ax = pl.subplots(nrows=1, ncols=1, figsize=(8, 6), sharey=True, sharex=True)
        ax.plot(1, 1)
        ax.set_xscale(x_axis_type)
        ax.set_yscale(y_axis_type)
        pl.rcParams["font.size"] = 10
        pl.gca().tick_params(axis='y', pad=8)
        pl.gca().tick_params(axis='x', pad=8)

        if len(x_axis_range) > 0:
            # do nothing
            pass
        else:
            x_axis_range = (min(X), max(X))

        if len(y_axis_range) > 0:
            # do nothing
            pass
        else:
            padding = (max(Y) - min(Y)) * 0.05
            y_axis_range = (min(Y) - padding, max(Y) + padding)

        # Set Plot Labels
        pl.xlim(min(x_axis_range), max(x_axis_range))
        pl.ylim(min(y_axis_range), max(y_axis_range))
        pl.xlabel(x_axis_title)
        pl.ylabel(y_axis_title)

        # If Z data, treat as heatmap scatter
        if len(Z) == 0:
            if plot_type == 'scatter':
                ax.scatter(X, Y, color=series_color, s=series_weight * 4, zorder=0)  # weight is by area, correct to height val
            else:
                ax.plot(X, Y, color=series_color, linestyle='-', linewidth=series_weight, zorder=0)
        else:
            # color points by z value and sort to not obscure data in plot
            sorted_X, sorted_Y, sorted_Z = self.__sort_by_z(X, Y, Z)
            if plot_type == 'scatter':
                ax.scatter(sorted_X, sorted_Y, c=sorted_Z, s=series_weight * 4, cmap=matplotlib.cm.rainbow, zorder=0)  # weight is by area, correct to height val
            else:
                ax.plot(sorted_X, sorted_Y, c=sorted_Z, linestyle='-', linewidth=series_weight, cmap=matplotlib.cm.rainbow, zorder=0)

        #####################################
        #            Residual Plot          #
        # ___________________________________#
        if len(X_model) > 0:
            if black_models:
                ax.plot(X_model, Y_model, linestyle='-', color='k', linewidth=series_weight / 5, zorder=1)
            else:
                ax.plot(X_model, Y_model, linestyle='-', color=series_color, linewidth=series_weight / 5,
                        path_effects=[pe.Stroke(linewidth=series_weight / 2.5, foreground='k'), pe.Normal()],
                        zorder=1)
            # residuals plot
            divider = make_axes_locatable(ax)
            ax2 = divider.append_axes("bottom", size="20%", pad=0)
            ax.figure.add_axes(ax2)
            ax2.set_xscale(x_axis_type)
            ax2.set_yscale(y_axis_type)
            # end residuals plot
            ax.set_xticklabels([])
            pl.gca().yaxis.set_major_locator(MaxNLocator(prune='upper'))
            # Set x bounds to match data plot
            pl.xlim(min(x_axis_range), max(x_axis_range))
            pl.xlabel(x_axis_title)
            ax2.plot(X, Y_resid, linestyle='-', color=series_color, linewidth=series_weight / 5)
            ax2.axhline(y=0, linestyle='-', color='k', linewidth=2, zorder=0)
            ax2.grid()
        # ___________________________________#
        #        END Residual Plot          #
        #####################################

        #####################################
        #     X-line and Y-line Plotting    #
        # ___________________________________#
        if show_x_lines and len(x_lines) >= 1:
            for line in x_lines:
                ax.axvline(x=line, linestyle='--', color='gray', linewidth=series_weight / 5, zorder=2,
                           path_effects=[pe.Stroke(linewidth=series_weight / 2.5, foreground='k'), pe.Normal()])
        if show_y_lines and len(y_lines) >= 1:
            for line in y_lines:
                ax.axhline(y=line, linestyle='--', color='gray', linewidth=series_weight / 5, zorder=2,
                           path_effects=[pe.Stroke(linewidth=series_weight / 2.5, foreground='k'), pe.Normal()])
        # ___________________________________#
        #  END X-line and Y-line Plotting   #
        #####################################

        #####################################
        #           Peak Plotting           #
        # ___________________________________#
        if show_peaks and len(peak_indicies) >= 1:
            peak_x = []
            peak_y = []
            for p in peak_indicies:
                peak_x.append(X[p])
                peak_y.append(Y[p])
            ax.plot(peak_x, peak_y, "d", markerfacecolor='gainsboro', markeredgecolor='k', zorder=3)
        if show_peak_bounds and len(peak_bounds_indicies) >= 1:
            peak_bound_x = []
            peak_bound_y = []
            for p in peak_bounds_indicies:
                p_start = p[0]
                p_end = p[1]
                peak_bound_x.append(X[p_start])
                peak_bound_y.append(Y[p_start])
                peak_bound_x.append(X[p_end])
                peak_bound_y.append(Y[p_end])
            ax.plot(peak_bound_x, peak_bound_y, "d", markerfacecolor='gainsboro', markeredgecolor='k', zorder=3)
        # ___________________________________#
        #       END Peak Plotting           #
        #####################################

        #####################################
        #         Integral  Plotting        #
        # ___________________________________#
        if show_integrals and len(integral_indicies_pairs) >= 1:
            if not isinstance(series_color, tuple):
                series_color = matplotlib.colors.to_rgba(series_color)
            int_color = list(series_color)
            int_color[3] = 0.4
            int_color = tuple(int_color)
            int_x = []
            int_y = []
            xy_vals = list(zip(X, Y))
            for int_indx in integral_indicies_pairs:
                int_start = (X[int_indx[0]], Y[int_indx[0]])
                int_end = (X[int_indx[-1]], Y[int_indx[-1]])
                verts = [(int_start[0], 0)] + xy_vals[int_indx[0]:int_indx[1]] + [(int_end[0], 0)]
                poly = matplotlib.patches.Polygon(verts, facecolor=int_color, edgecolor='gainsboro', zorder=0)
                ax.add_patch(poly)
        # ___________________________________#
        #     END  Integral  Plotting       #
        #####################################

        #####################################
        #        Polygon Plotting           #
        # ___________________________________#
        if show_polygons and len(polygon_verticies) >= 1:
            for polygon in polygon_verticies:
                poly_x, poly_y = zip(*polygon)
                ax.plot(poly_x, poly_y, linestyle='-', color='gainsboro', linewidth=series_weight / 5, zorder=4,
                        path_effects=[pe.Stroke(linewidth=series_weight / 2.5, foreground='k'), pe.Normal()])
        # ___________________________________#
        #       END  Polygon Plotting       #
        #####################################

        ax.grid()
        fig.canvas.flush_events()

        return pl

    def __get_byte_png(self, pl, dpi=50):
        BIOstream = BIO()
        pl.tight_layout()
        pl.savefig(BIOstream, format='png', dpi=dpi, bbox_inches='tight')
        BIOstream.seek(0)
        im = Image.open(BIOstream)
        im2 = im.convert('RGB').convert('P', palette=Image.ADAPTIVE)
        im2 = im2.resize(im2.size, Image.ANTIALIAS)
        BIOstream = BIO()
        im2.save(BIOstream, format='PNG', quality=95)
        BIOstream.seek(0)
        byte_png = BIOstream.getvalue()
        pl.close()
        return byte_png

    def __sort_by_z(self, X, Y, Z):
        idx = Z.argsort()
        sorted_x, sorted_y, sorted_z = X[idx], Y[idx], Z[idx]
        return sorted_x, sorted_y, sorted_z


class multiproc(object):
    def __init__(self, target_def):
        """Run a method on all available cpus"""
        self.__target = target_def
        self.args = []
        self.__cpu_num = psutil.cpu_count(logical=True)
        self.result = []

    def add_args(self, arg_lst):
        self.args.append(arg_lst)
        return

    def set_cpu_num(self, cpu):
        self.__cpu_num = int(cpu)
        return

    def start(self):
        number_of_processes = self.__cpu_num
        arg_set = [tuple(a) for a in self.args]
        with multiprocessing.Pool(processes=number_of_processes) as pool:
            results = pool.starmap(self.__target, arg_set)
        if isinstance(results, list) and isinstance(results[0], list):
            for item in results:
                self.result.extend(item)
        else:
            self.result = results


class emailer(object):
    def __init__(self):
        #common e-mail related parameters
        self.__admin_addr = 'paul.nobrega@proteininnovation.org'
        self.__all_addr = 'paul.nobrega@proteininnovation.org' #'lab@proteininnovation.org'
        self.__from_addr = 'Automation@ProteinInnovation.org'
        self.__from_pwd = '3qPKdUcEtU'
        self.__smtp_port = 587
        self.__smtp_host = 'smtp.gmail.com'
        self.__sys_name = 'IPI_Automation'

    def __send_email(self, message, to_user):
        try:
            print(f"Sending e-mail to {to_user}...")
            server = smtplib.SMTP(self.__smtp_host, self.__smtp_port)
            server.ehlo()
            server.starttls()
            server.login(self.__from_addr, self.__from_pwd)
            server.sendmail(self.__from_addr, self.__all_addr, message)
            server.close()
            return True
        except Exception as e:
            print(f"Failed to send e-mail to {to_user}!\n\n" + str(e))
            return False

    def send_to_all(self, subject, body):
        to_user = 'ALL'
        # Sends experiment related messages to All of IPI
        body = f"Hi All,\n\nThe following is an automated message from {self.__sys_name}:\n\n{body}\n\nThanks!"
        message = "\r\n".join([f"From: {self.__from_addr}", f"To: {self.__all_addr}",f"Subject: {subject}", "", body])
        return self.__send_email(message, to_user)

    def send_to_admin(self, subject, body):
        to_user = 'ADMIN'
        #sends maintinence related messages to Admin
        body = f"Hi Admin!\n\n{self.__sys_name} is currently having" \
               f" the following issues that need to be addressed:\n\n{body}\n\nThanks!"
        message = "\r\n".join([f"From: {self.__from_addr}", f"To: {self.__admin_addr}", f"Subject: {subject}", "", body])
        return self.__send_email(message, to_user)
