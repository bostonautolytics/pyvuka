#!/usr/bin/env python
#title           :toPyVuka.py
#author          :R. Paul Nobrega, IPI
#contact         :Paul.Nobrega@ProteinInnovation.com
#description     :This file contains code that interfaces code within PyVuka modules to the global PyVuka classes:
#                     -gvars [global variables]
#                     -plot  [plotting class]
#                     -commands [class to process native PyVuka commands]
#                 These adapter functions permit facile invocation of native PyVuka plotting functions and direct
#                 manipulation of the existing buffers and datamatrix
#usage           :Pyvuka module
#python_version  :3.7
#==============================================================================
#
# !ATTENTION!
# Modules accept the buffer matrix from Pyvuka. Additional data can be passed into the function, but "datamatrix"
# must remain at the first position and is always returned even if not altered.
#
# The PyVuka data buffer matrix is a list of object_buffer dictionaries
#
#######################################################################################################################
from PyVuka import commands, plot, data_obj as data
from PIL import Image
from io import BytesIO as BIO
import os


def initialize_instance():
    if not hasattr(data, 'matrix'):
        data.init()


def new_datamatrix():
    return data.Data().matrix


def new_buffer():
    return data.Buffer()


def get_datamatrix():
    return data.matrix


def append_datamatrix(datamatrix_to_append):
    for i in range(1, datamatrix_to_append.length() +1):
        data.matrix.add_buffer(datamatrix_to_append.buffer(i))


def write_buffer_at_buffer_number(buffer, buffer_number):
    if not 1 <= buffer_number <= data.matrix.length():
        raise ValueError('Supplied matrix index is invalid!')
    if isinstance(buffer, type(data.Buffer())):
        data.matrix.buffer[buffer_number] = buffer
        return data.matrix
    raise TypeError('Supplied buffer object is not a valid instance of a PyVuka DataMatrix Data Buffer!')


def set_datamatrix(input_datamatrix):
    if isinstance(input_datamatrix, type(data.matrix)) and \
            input_datamatrix.length() > 0 and isinstance(input_datamatrix.buffer(1), type(data.Buffer())):
        data.matrix = input_datamatrix
        return data.matrix
    raise TypeError('Invalid PyVuka datamatrix Object!')


def add_buffer_to_datamatrix(buffer):
    if isinstance(buffer, type(data.Buffer())):
        data.matrix.add_buffer(buffer)
        return data.matrix
    raise TypeError('Supplied buffer object is not a valid instance of a PyVuka DataMatrix Data Buffer!')


def remove_buffer_from_datamatrix(buffer_number):
    try:
        data.matrix.remove_buffer_by_number(buffer_number)
        return data.matrix
    except Exception as e:
        raise IndexError(f'Invalid buffer index:\n\t{str(e)}')


def get_plot_limit_params():
    return data.plot_limits


def set_plot_limit_params(plot_limit_parameter_obj):
    if isinstance(plot_limit_parameter_obj, type(data.plot_limits)):
        data.plot_limits = plot_limit_parameter_obj
        return data.plot_limits
    raise TypeError('Invalid PyVuka Plot Limits Object!')


def get_system_variables():
    return data.directories


def set_system_variables(system_variables_obj):
    if isinstance(system_variables_obj, type(data.directories)):
        data.directories = system_variables_obj
        return data.directories
    raise TypeError('Invalid PyVuka System Variables Object!')


def get_current_working_directory():
    return data.directories.working.get()


def set_current_working_directory(working_directory_full_path):
    if os.path.exists(working_directory_full_path):
        data.directories.working.set(working_directory_full_path)
        return data.directories.working.get()
    raise TypeError('Invalid PyVuka System Variables Object!')


def get_output_directory():
    return data.directories.output.get()


def set_output_directory(output_directory_full_path):
    if os.path.exists(output_directory_full_path) or os.access(os.path.dirname(output_directory_full_path), os.W_OK):
        data.directories.output.set(output_directory_full_path)
        return data.directories.output.get()
    raise TypeError('Invalid PyVuka System Variables Object!')


def show_plot(list_of_datamatrix_idicies, *args, **kwargs):
    list_of_datamatrix_idicies = __single_int_to_list(list_of_datamatrix_idicies)
    dpi = 50
    tight = True
    black_models = True

    if 'dpi' in kwargs:
        try:
            dpi = int(kwargs['dpi'])
        except:
            pass
    if 'tight' in kwargs:
        try:
            tight = bool(kwargs['tight'])
        except:
            pass
    if 'black_models' in kwargs:
        try:
            black_models = bool(kwargs['black_models'])
        except:
            pass

    img = plot.plotter()
    try:
        return img(list_of_datamatrix_idicies, get_bytes=False, dpi=dpi, tight=tight, black_models=black_models)
    except Exception as e:
        raise Exception(f'Could not generate plot:\n\t{str(e)}')


def get_plot_as_bytestring(list_of_datamatrix_idicies, *args, **kwargs):
    list_of_datamatrix_idicies = __single_int_to_list(list_of_datamatrix_idicies)
    dpi = 50
    tight = True
    black_models = True

    if 'dpi' in kwargs:
        try:
            dpi = int(kwargs['dpi'])
        except:
            pass
    if 'tight' in kwargs:
        try:
            tight = bool(kwargs['tight'])
        except:
            pass
    if 'black_models' in kwargs:
        try:
            black_models = bool(kwargs['black_models'])
        except:
            pass

    img = plot.plotter()
    #try:
    return BIO(img(list_of_datamatrix_idicies, get_bytes=True, dpi=dpi, tight=tight, black_models=black_models))
    #except Exception as e:
    #    raise Exception(f'Could not generate plot:\n\t{str(e)}')


def __single_int_to_list(list_of_datamatrix_idicies):
    if isinstance(list_of_datamatrix_idicies, int):
        return [list_of_datamatrix_idicies]
    elif isinstance(list_of_datamatrix_idicies, list):
        return list_of_datamatrix_idicies
    else:
        raise TypeError(f'Invalid list of buffer indicies: {str(list_of_datamatrix_idicies)}\nExpecting list of int')


def save_plot(list_of_datamatrix_idicies, output_image_file_path, *args, **kwargs):
    dpi = 50
    if 'dpi' in kwargs:
        try:
            dpi = int(kwargs['dpi'])
        except:
            pass
    # get image as bytes through call to existing function.  Will raise appropriate error on failure
    output_png = get_plot_as_bytestring(list_of_datamatrix_idicies, dpi=dpi)
    try:
        img = Image.open(output_png)
        img.save(output_image_file_path, format='PNG')
        return output_image_file_path
    except Exception as e:
        raise OSError(f"Can not write image to path as supplied: {output_image_file_path}")


def run_pyvuka_command(native_pyvuka_command):
    if not isinstance(native_pyvuka_command, str):
        raise ValueError(f'PyVuka command is not a valid string object!')
    try:
        commander = commands.Command()
        return commander(native_pyvuka_command)
    except Exception as e:
        raise ValueError(f'Invalid PyVuka command!\n\t{str(e)}')

