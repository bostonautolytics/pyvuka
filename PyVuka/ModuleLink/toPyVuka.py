#!/usr/bin/env python
# title           :toPyVuka.py
# author          :R. Paul Nobrega, IPI
# contact         :Paul.Nobrega@ProteinInnovation.com
# description     :This file contains code that interfaces code within PyVuka modules to the global PyVuka classes:
#                     -gvars [global variables]
#                     -plot  [plotting class]
#                     -commands [class to process native PyVuka commands]
#                 These adapter functions permit facile invocation of native PyVuka plotting functions and direct
#                 manipulation of the existing buffers and datamatrix
# usage           :Pyvuka module
# python_version  :3.7
# ==============================================================================
#
# !ATTENTION!
# Modules accept the buffer matrix from Pyvuka. Additional data can be passed into the function, but "datamatrix"
# must remain at the first position and is always returned even if not altered.
#
# The PyVuka data buffer matrix is a list of object_buffer dictionaries
#
#######################################################################################################################
from .. import commands, plot, data_obj as data
from PIL import Image
from io import BytesIO as BIO
import os


def initialize_instance():
    return new_instance()


class new_instance:
    def __init__(self):
        self.data = data.init()
        self.plot = plot.plotter(self.data)
        self.commands = commands

    def clear_all(self):
        self.data = data.init()

    def new_datamatrix(self):
        return self.data.new_matrix()

    def new_buffer(self):
        return self.data.new_buffer()

    def get_datamatrix(self):
        return self.data.matrix

    def append_datamatrix(self, datamatrix_to_append):
        for i in range(1, datamatrix_to_append.length() + 1):
            self.data.matrix.add_buffer(datamatrix_to_append.buffer(i))

    def write_buffer_at_buffer_number(self, buffer, buffer_number):
        if not 1 <= buffer_number <= self.data.matrix.length():
            raise ValueError('Supplied matrix index is invalid!')
        if isinstance(buffer, type(self.new_buffer())):
            self.data.matrix.set_buffer_by_number(buffer, buffer_number)
            return self.data.matrix
        raise TypeError('Supplied buffer object is not a valid instance of a PyVuka DataMatrix Data Buffer!')

    def set_datamatrix(self, input_datamatrix):
        if isinstance(input_datamatrix, type(self.data.matrix)) and \
                input_datamatrix.length() > 0 and isinstance(input_datamatrix.buffer(1), type(self.new_buffer())):
            self.data.matrix.set(input_datamatrix.get())
            return self.data.matrix
        raise TypeError('Invalid PyVuka datamatrix Object!')

    def add_buffer_to_datamatrix(self, buffer):
        if isinstance(buffer, type(self.new_buffer())):
            self.data.matrix.add_buffer(buffer)
            return self.data.matrix
        raise TypeError('Supplied buffer object is not a valid instance of a PyVuka DataMatrix Data Buffer!')

    def remove_buffer_from_datamatrix(self, buffer_number):
        try:
            self.data.matrix.remove_buffer_by_number(buffer_number)
            return self.data.matrix
        except Exception as e:
            raise IndexError(f'Invalid buffer index:\n\t{str(e)}')

    def get_plot_limit_params(self):
        self.buffer_range = self.data.plot_limits._BufferRange()
        self.x_range = self.data.plot_limits._XYZRange()
        self.y_range = self.data.plot_limits._XYZRange()
        self.z_range = self.data.plot_limits._XYZRange()
        self.__matrix_save = None
        self.is_active = False
        return {'buffer_range': self.data.plot_limits.buffer_range.get(),
                'x_range': self.data.plot_limits.x_range.get(),
                'y_range': self.data.plot_limits.y_range.get(),
                'z_range': self.data.plot_limits.z_range.get(),
                'limits_are_active': self.data.plot_limits.is_active}

    def set_plot_limit_params(self, plot_limit_dict):
        if isinstance(plot_limit_dict, type({})):
            self.data.plot_limits.buffer_range.set(plot_limit_dict['buffer_range'])
            self.data.plot_limits.x_range.set(plot_limit_dict['x_range'])
            self.data.plot_limits.y_range.set(plot_limit_dict['y_range'])
            self.data.plot_limits.z_range.set(plot_limit_dict['z_range'])
            self.data.plot_limits.is_active = bool(plot_limit_dict['limits_are_active'])
            return self.get_plot_limit_params()
        raise TypeError('Invalid PyVuka Plot Limits Dict!  Use "get_plot_limit_params()" for an example')

    def get_system_variables(self):
        return {'working': self.data.directories.working.get(), 'output': self.data.directories.output.get()}

    def set_system_variables(self, system_variables_dict):
        if isinstance(system_variables_dict, type({})):
            self.data.directories.working.set(system_variables_dict['working'])
            self.data.directories.output.set(system_variables_dict['output'])
            return self.get_system_variables()
        raise TypeError('Invalid PyVuka System Variables Object!')

    def get_current_working_directory(self):
        return self.data.directories.working.get()

    def set_current_working_directory(self, working_directory_full_path):
        if os.path.exists(working_directory_full_path):
            self.data.directories.working.set(working_directory_full_path)
            return self.data.directories.working.get()
        raise TypeError('Invalid PyVuka System Variables Object!')

    def get_output_directory(self):
        return self.data.directories.output.get()

    def set_output_directory(self, output_directory_full_path):
        if os.path.exists(output_directory_full_path) or os.access(os.path.dirname(output_directory_full_path), os.W_OK):
            self.data.directories.output.set(output_directory_full_path)
            return self.data.directories.output.get()
        raise TypeError('Invalid PyVuka System Variables Object!')

    def show_plot(self, list_of_datamatrix_idicies, *args, **kwargs):
        list_of_datamatrix_idicies = self.__single_int_to_list(list_of_datamatrix_idicies)
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

        #try:
        return self.plot(list_of_datamatrix_idicies, get_bytes=False, dpi=dpi, tight=tight, black_models=black_models)
        #except Exception as e:
        #    raise Exception(f'Could not generate plot:\n\t{str(e)}')

    def get_plot_as_bytestring(self, list_of_datamatrix_idicies, *args, **kwargs):
        list_of_datamatrix_idicies = self.__single_int_to_list(list_of_datamatrix_idicies)
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

        img = plot.plotter(self.data)
        try:
            return BIO(img(list_of_datamatrix_idicies, get_bytes=True, dpi=dpi, tight=tight, black_models=black_models))
        except Exception as e:
            raise Exception(f'Could not generate plot:\n\t{str(e)}')

    @staticmethod
    def __single_int_to_list(list_of_datamatrix_idicies):
        if isinstance(list_of_datamatrix_idicies, int):
            return [list_of_datamatrix_idicies]
        elif isinstance(list_of_datamatrix_idicies, list):
            return list_of_datamatrix_idicies
        else:
            raise TypeError(f'Invalid list of buffer indicies: {str(list_of_datamatrix_idicies)}\nExpecting list of int')

    def save_plot(self, list_of_datamatrix_idicies, output_image_file_path, *args, **kwargs):
        dpi = 50
        if 'dpi' in kwargs:
            try:
                dpi = int(kwargs['dpi'])
            except:
                pass
        # get image as bytes through call to existing function.  Will raise appropriate error on failure
        output_png = self.get_plot_as_bytestring(list_of_datamatrix_idicies, dpi=dpi)
        try:
            img = Image.open(output_png)
            img.save(output_image_file_path, format='PNG')
            return output_image_file_path
        except Exception as e:
            raise OSError(f"Can not write image to path as supplied: {output_image_file_path}")

    def run_pyvuka_command(self, native_pyvuka_command):
        if not isinstance(native_pyvuka_command, str):
            raise ValueError(f'PyVuka command is not a valid string object!')
        try:
            commander = commands.Command(self)
            return commander(native_pyvuka_command)
        except Exception as e:
            raise ValueError(f'Invalid PyVuka command!\n\t{str(e)}')