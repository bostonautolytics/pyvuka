import numpy as np
from scipy import stats
import ast
import os
import json


global matrix
global plot_limits
global directories


def init():
    global matrix
    matrix = Data().matrix
    global plot_limits
    plot_limits = Data().plot_limits
    global directories
    directories = Directories()


class _SharedDCO(object):
    def __init__(self):
        self.generic_array_set_method = self.__generic_array_set_method
        self.generic_cat_list_set_method = self.__generic_cat_list_set_method

    @staticmethod
    def __generic_array_set_method(input_var):
        in_type = type(input_var)
        if isinstance(input_var, (np.ndarray, np.generic)) or in_type is list or in_type is tuple:
            return np.array(input_var).flatten()
        elif in_type is int or in_type is float:
            return np.array([input_var])
        elif in_type is str and len(input_var) > 3:
            try:
                conv_input = ast.literal_eval(input_var)
                conv_type = type(conv_input)
                if conv_type is list or conv_type is tuple:
                    return np.array(conv_input)
                elif conv_type is float or conv_type is int:
                    return np.array([input_var])
            except Exception as e:
                # not useable data pass to final error raise
                pass
        raise TypeError('Input variable is not int, float, np.array, list, tuple, or string representation thereof!')

    @staticmethod
    def __generic_cat_list_set_method(input_var):
        in_type = type(input_var)
        if isinstance(input_var, (np.ndarray, np.generic)) or in_type is list or in_type is tuple:
            return _SharedDCO.__flatten(input_var)
        elif in_type is int or in_type is float:
            return [str(input_var)]
        elif in_type is str and len(input_var) > 3:
            try:
                conv_input = ast.literal_eval(input_var)
                conv_type = type(conv_input)
                if conv_type is list or conv_type is tuple:
                    return _SharedDCO.__flatten(conv_input)
                else:
                    return [str(input_var)]
            except Exception as e:
                # not useable data pass to final error raise
                pass
        raise TypeError('Input variable is not int, float, np.array, list, tuple, or string representation thereof!')

    @staticmethod
    def __flatten(str_matrix):
        rt = []
        for i in str_matrix:
            if isinstance(i, list):
                rt.extend(_SharedDCO.__flatten(i))
            else:
                rt.append(str(i))
        return rt


class Data(object):
    def __init__(self):
        self.matrix = self.__Matrix()
        self.plot_limits = self._PlotLimits()

    class __Matrix(object):
        def __init__(self):
            self.__buffer_list = []

        def __len__(self):
            return len(self.__buffer_list)

        def get(self) -> list:
            return self.__buffer_list

        def set(self, data_matrix: list):
            if type(data_matrix) is not list or len(data_matrix) == 0:
                raise ValueError(f"Expecting 'List' type with length > 0, received: {type(data_matrix)}")
            self.__buffer_valid_check(data_matrix[0])
            self.__buffer_list = data_matrix

        def length(self) -> int:
            return len(self.__buffer_list)

        def buffer(self, buffer_number: int):
            return self.get_buffer_by_number(buffer_number)

        def get_buffer_by_number(self, buffer_number: int):
            return self.__buffer_list[self.__buffer_number_to_idx(buffer_number)]

        def set_buffer_by_number(self, buffer, buffer_number: int):
            self.__buffer_number_valid_check(buffer_number)
            self.__buffer_valid_check(buffer)
            self.__buffer_list[self.__buffer_number_to_idx(buffer_number)] = buffer

        def add_buffer(self, buffer):
            self.__buffer_valid_check(buffer)
            self.__buffer_list.append(buffer)

        def append_new_buffer(self):
            self.__buffer_list.append(Buffer())

        def remove_buffer_by_number(self, buffer_number: int):
            buffer_idx = buffer_number - 1
            self.__buffer_number_valid_check(buffer_number)
            del self.__buffer_list[buffer_idx]

        def clear(self):
            self.__buffer_list = []

        def shortest_x_length(self) -> int:
            shortest = np.inf
            for i in range(len(self.__buffer_list)):
                temp_len = self.__buffer_list[i].data.x.length()
                if temp_len < shortest:
                    shortest = temp_len
            return shortest

        def longest_x_length(self) -> int:
            longest = -np.inf
            for i in range(len(self.__buffer_list)):
                temp_len = len(self.__buffer_list[i].data.x)
                if temp_len > longest:
                    longest = temp_len
            return longest

        def __buffer_number_valid_check(self, buffer_number):
            buffer_idx = buffer_number - 1
            if buffer_idx not in range(len(self.__buffer_list)):
                buf_idx_lst = list(range(len(self.__buffer_list)))
                first = buf_idx_lst[0]+1
                last = buf_idx_lst[-1] + 1
                raise ValueError(f"Buffer number: {buffer_number} is not in range of data matrix: {first} - {last}")

        @staticmethod
        def __buffer_number_to_idx(buffer_number: int) -> int:
            return buffer_number - 1

        @staticmethod
        def __buffer_valid_check(input_object):
            if not isinstance(input_object, Buffer):
                raise ValueError(f"Expecting PyVuka buffer objects, recieved: {type(input_object)}")

    class _PlotLimits(object):
        def __init__(self):
            self.buffer_range = self._BufferRange()
            self.x_range = self._XYZRange()
            self.y_range = self._XYZRange()
            self.z_range = self._XYZRange()
            self.__matrix_save = None
            self.is_active = False

        def on(self):
            if self.is_active:
                return
            self.__matrix_save = self.__copy_matrix_data()  # faster than using copy.deepcopy

            if len(self.buffer_range.get()) > 0:
                firstbuffer, lastbuffer = [min(self.buffer_range.get()), max(self.buffer_range.get())]
            else:
                firstbuffer, lastbuffer = [1, matrix.length()]
            for i in range(firstbuffer, lastbuffer + 1):
                matrix.set_buffer_by_number(self.apply_to_buffer(matrix.buffer(i)), i)
            self.is_active = True

        def __copy_matrix_data(self):
            save_list = []
            for i in range(1, len(matrix) + 1):
                save_dict = {}
                save_dict['x'] = list(matrix.buffer(i).data.x.get())
                save_dict['xe'] = list(matrix.buffer(i).data.xe.get())
                save_dict['y'] = list(matrix.buffer(i).data.y.get())
                save_dict['ye'] = list(matrix.buffer(i).data.ye.get())
                save_dict['z'] = list(matrix.buffer(i).data.z.get())
                save_dict['ze'] = list(matrix.buffer(i).data.ze.get())
                save_list.append(save_dict)
            return json.loads(json.dumps(save_list))

        def off(self):
            if not self.is_active:
                return
            for i in range(1, len(self.__matrix_save) + 1):
                if i in range(min(self.buffer_range.get()), max(self.buffer_range.get()) + 1):
                    matrix.buffer(i).data.x.set(self.__matrix_save[i-1]['x'])
                    matrix.buffer(i).data.xe.set(self.__matrix_save[i-1]['xe'])
                    matrix.buffer(i).data.y.set(self.__matrix_save[i-1]['y'])
                    matrix.buffer(i).data.ye.set(self.__matrix_save[i-1]['ye'])
                    matrix.buffer(i).data.z.set(self.__matrix_save[i-1]['z'])
                    matrix.buffer(i).data.ze.set(self.__matrix_save[i-1]['ze'])
            self.is_active = False
            self.__matrix_save = None

        @staticmethod
        def apply_to_buffer(buffer_object):
            global plot_limits
            new_buffer = buffer_object # removed copy.deepcopy
            x = new_buffer.data.x.get()
            xe = new_buffer.data.xe.get()
            y = new_buffer.data.y.get()
            ye = new_buffer.data.ye.get()
            z = new_buffer.data.z.get()
            ze = new_buffer.data.ze.get()

            x_range = plot_limits.x_range.get()
            y_range = plot_limits.y_range.get()
            z_range = plot_limits.z_range.get()
            idx_out = [i for i, j in enumerate(x) if not min(x_range)-1 <= i <= max(x_range)-1] if len(x_range) > 0 else [] + \
                [i for i, j in enumerate(y) if not min(y_range)-1 <= j <= max(y_range)-1] if len(y_range) > 0 else [] + \
                [i for i, j in enumerate(z) if not min(z_range)-1 <= j <= max(z_range)-1] if len(z_range) > 0 else []

            if len(idx_out) == 0:
                return buffer_object

            idx_out = list(set(sorted(idx_out)))
            all_data = [x, y, z, xe, ye, ze]
            for i, data_vector in enumerate(all_data):
                if len(data_vector) > 0:
                    if max(idx_out) <= len(data_vector):
                        all_data[i] = np.delete(data_vector, idx_out)

            x, y, z, xe, ye, ze = all_data

            new_buffer.data.x.set(x)
            new_buffer.data.xe.set(xe)
            new_buffer.data.y.set(y)
            new_buffer.data.ye.set(ye)
            new_buffer.data.z.set(z)
            new_buffer.data.ze.set(ze)
            return new_buffer

        class _base_range(object):
            def __init__(self):
                self.__base = tuple([])

            def get(self) -> tuple:
                return self.__base

            def set(self, user_input: iter):
                if type(user_input) is str:
                    user_input = ast.literal_eval(user_input)
                if not is_iterable(user_input):
                    raise ValueError(f"Parameter: {user_input} is not iterable. Expecting tuple containing 2 numbers")
                self.__base = tuple(user_input[:2])

            def max(self):
                return max(self.__base) if len(self.__base) > 0 else None

            def min(self):
                return min(self.__base) if len(self.__base) > 0 else None

        class _BufferRange(_base_range):
            def __init__(self):
                super(Data._PlotLimits._BufferRange, self).__init__()
                #self.__base = tuple([int(x) for x in self.__base].sort()[:2]) if len(self.__base) >= 2 else None

        class _XYZRange(_base_range):
            def __init__(self):
                super(Data._PlotLimits._XYZRange, self).__init__()
                #self.__base = tuple([float(x) for x in self.__base].sort()[:2]) if len(self.__base) >= 2 else None


class Directories(object):
    def __init__(self):
        self.working = self.__Working()
        self.output = self.__Output()

    def __str__(self):
        return f"Working Directory: {self.working}\nOutput Directory: {self.output}"

    class _base_class(object):
        def __init__(self):
            self.__base = ''

        def get(self) -> str:
            return self.__base

        def set(self, dir_name):
            try:
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
            except Exception as e:
                raise ValueError(f'Supplied directory path: {dir_name} does not exist and cannot be created!')
            self.__base = str(dir_name)

    class __Working(_base_class):
        pass

    class __Output(_base_class):
        pass


class Buffer(object):
    def __init__(self):
        self.data = self.__BaseData()
        self.category = self.__BaseCategory()
        self.model = self.__BaseData()
        self.residuals = self.__BaseData()
        self.instrument_response = self.__BaseData()
        self.fit = self.__Fit()
        self.plot = self.__Plot()
        self.comments = self.__Comments()
        self.meta_dict = {}

    class __BaseData(object):
        def __init__(self):
            self.x = self._base_array()
            self.xe = self._base_array()
            self.y = self._base_array()
            self.ye = self._base_array()
            self.z = self._base_array()
            self.ze = self._base_array()

        class _base_array(object):
            def __init__(self):
                self.__base = np.array([])

            def __len__(self):
                self.length()

            def get(self) -> np.array:
                return self.__base

            def get_sorted_ascending(self) -> np.array:
                return np.sort(self.__base)

            def get_sorted_decending(self) -> np.array:
                return np.sort(self.__base)[::-1]

            def set(self, user_input: iter):
                self.__base = _SharedDCO().generic_array_set_method(user_input)

            def append(self, value):
                self.__base = np.append(self.__base, value)

            def clear(self):
                self.__base = np.array([])

            def set_sorted_ascending(self, user_input: iter = None):
                if user_input is None or len(self.__base) == 0:
                    raise ValueError("No data to sort!")
                elif user_input is not None:
                    self.set(user_input)
                self.__base = self.get_sorted_ascending()

            def set_sorted_decending(self, user_input: iter = None):
                if user_input is None or len(self.__base) == 0:
                    raise ValueError("No data to sort!")
                elif user_input is not None:
                    self.set(user_input)
                self.__base = self.get_sorted_decending()

            def set_random(self, minimum: float = 0, maximum: float = 100, num_pts: int = -1):
                if num_pts > 0:
                    self.__base = np.random.uniform(low=minimum, high=maximum, size=(num_pts))
                elif len(self.__base) > 0:
                    self.__base = np.random.uniform(low=minimum, high=maximum, size=(len(self.__base)))
                else:
                    raise ValueError("No number of random values is defined!")

            def set_zeros(self, num_pts: int = -1) -> np.array:
                if num_pts < 0:
                    self.__base = np.zeros(num_pts)
                elif len(self.__base) > 0:
                    self.__base = np.zeros(len(self.__base))
                else:
                    raise ValueError("No number of zeros defined!")

            def average(self) -> float:
                return float(np.nanmean(self.__base)) if len(self.__base) > 0 else None

            def stdev(self) -> float:
                return float(np.nanstd(self.__base)) if len(self.__base) > 0 else None

            def range(self) -> tuple:
                data = [x for x in self.__base if np.isfinite(x) and not np.isnan(x)]
                return tuple([np.nanmin(data), np.nanmax(data)]) if len(data) > 1 else None

            def median(self) -> float:
                return float(np.nanmedian(self.__base)) if len(self.__base) > 0 else None

            def mode(self) -> tuple:
                '''Returns tuple of array_of_modal_values, array_of_mode_counts'''
                return stats.mode(self.__base) if len(self.__base) > 0 else None

            def min(self) -> float:
                return float(np.nanmin(self.__base)) if len(self.__base) > 0 else None

            def max(self):
                return np.nanmax(self.__base) if len(self.__base) > 0 else None

            def length(self) -> int:
                return len(self.__base)

            def sum(self) -> float:
                return float(np.nansum(self.__base)) if len(self.__base) > 0 else None

            def cumsum(self) -> np.array:
                return np.nancumsum(self.__base) if len(self.__base) > 0 else None

            def product(self) -> np.array:
                return np.nanprod(self.__base) if len(self.__base) > 0 else None

            def cumproduct(self) -> np.array:
                return np.nancumprod(self.__base) if len(self.__base) > 0 else None

            def clean_nan_inf(self):
                self.__base = np.nan_to_num(self.__base)

            def nearest_index_to_value(self, value: float) -> int:
                subarray = np.abs(np.array(self.__base) - float(value))
                return int(subarray.argmin())

            def value_at_index(self, index: int) -> float:
                return float(self.__base[index]) if index <= len(self.__base) else None

    class __BaseCategory(object):
        def __init__(self):
            self.x = self._base_cat_array()
            self.y = self._base_cat_array()
            self.z = self._base_cat_array()

        class _base_cat_array(object):
            def __init__(self):
                self.__base = []

            def get(self) -> list:
                return self.__base

            def set(self, user_input: iter):
                self.__base = _SharedDCO().generic_cat_list_set_method(user_input)

            def append(self, value):
                if type(value) in [str, float, int]:
                    self.__base.append(str(value))
                elif is_iterable(value):
                    self.__base.extend([str(v) for v in value])
                else:
                    raise ValueError('Unexpected parameter type! Expecting: str, float, int, list, or tuple')

            def clear(self):
                self.__base = []

            def get_sorted_ascending(self) -> list:
                return list(sorted(self.__base))

            def get_sorted_decending(self) -> list:
                return list(sorted(self.__base, reverse=True))

            def set_sorted_ascending(self, user_input: iter = None):
                if user_input is None or len(self.__base) == 0:
                    raise ValueError("No data to sort!")
                elif user_input is not None:
                    self.set(user_input)
                self.__base = self.get_sorted_ascending()

            def set_sorted_decending(self, user_input: iter = None):
                if user_input is None or len(self.__base) == 0:
                    raise ValueError("No data to sort!")
                elif user_input is not None:
                    self.set(user_input)
                self.__base = self.get_sorted_decending()

            def range(self) -> tuple:
                data = [x for x in self.__base if np.isfinite(x) and not np.isnan(x)]
                return tuple([data[0], data[-1]]) if len(data) > 1 else None

            def mode(self) -> tuple:
                '''Returns tuple of array_of_modal_values, array_of_mode_counts'''
                return stats.mode(self.__base) if len(self.__base) > 0 else None

            def length(self) -> int:
                return len(self.__base)

            def indcies_of_value(self, value: str) -> list :
                return [i for i, entry in enumerate(self.__base) if entry.strip().lower() == value.strip().lower()]

            def value_at_index(self, index: int) -> str:
                return self.__base[index] if index <= len(self.__base) else None

    class __Fit(object):
        def __init__(self):
            self.function = self._base_str()
            self.function_index = self._base_list()
            self.parameter = self._base_list()
            self.parameter_error = self._base_list()
            self.chisq = self._base_float()
            self.rsq = self._base_float()
            self.link = self._base_list()
            self.free = self._base_list()
            self.use_error_weighting = True
            self.fit_failed = False
            self.fit_failed_reason = self._base_str()

        class _base_str(object):
                def __init__(self):
                    self.__str_val = ''

                def set(self, value: str):
                    self.__str_val = str(value)

                def get(self) -> str:
                    return self.__str_val

        class _base_list(object):
            def __init__(self):
                self.__base = []

            def __len__(self):
                self.length()

            def length(self):
                return len(self.__base)

            def get(self):
                return self.__base

            def set(self, input_list: iter):
                if is_iterable(input_list):
                    self.__base = list(input_list)
                else:
                    raise ValueError(f"Input is {type(input_list)}, not List or Tuple!")

        class _base_float(object):
            def __init__(self):
                self.__base = 0.00

            def get(self):
                return self.__base

            def set(self, value: float):
                try:
                    self.__base = float(value)
                except Exception as e:
                    raise ValueError(f"Input is {type(value)}, not the expected Float type!")

    class __Plot(object):
        def __init__(self):
            self.type = self._BaseStr()
            self.title = self._BaseStr()
            self.series = self.__Series()
            self.axis = self.__Axis()
            self.polygons = self.__Polygons()
            self.use_weighted_residuals = False

        class _BaseStr(object):
            def __init__(self):
                self.__str_val = ''

            def set(self, value: str):
                self.__str_val = str(value)

            def get(self) -> str:
                return self.__str_val

        class __Series(object):
            def __init__(self):
                self.name = self._base_str()
                self.color = self._base_color()
                self.type = self._base_str()
                self.weight = self._base_float()

            class _base_float(object):
                def __init__(self):
                    self.__float_val = 5

                def set(self, value: float):
                    self.__float_val = float(value)

                def get(self) -> float:
                    return self.__float_val

            class _base_str(object):
                def __init__(self):
                    self.__str_val = ''

                def set(self, value: str):
                    self.__str_val = str(value)

                def get(self) -> str:
                    return self.__str_val

            class _base_color(object):
                def __init__(self):
                    self.__color_val = 'r'

                def set(self, color: str):
                    self.__color_val = str(color)

                def get(self) -> str:
                    return self.__color_val

            class _base_type(object):
                def __init__(self):
                    self.__type_val = '.'
                    self.__valid_types = self.return_valid_types()

                def set(self, point_type: str):
                    is_valid = False
                    point_type = point_type.lower()
                    if 'string' in point_type and '(' in point_type and point_type[-1] == ')':
                        point_type = f'${point_type.split("(")[-1][:-1]}$'
                        is_valid = True
                    else:
                        for k,v in self.__valid_types.items():
                            if point_type == k or point_type == v:
                                point_type = v
                                is_valid = True
                                break
                    self.__type_val = str(point_type) if is_valid else '.'

                def get(self) -> str:
                    return self.__type_val

                @staticmethod
                def return_valid_types():
                    valid_types = {'point': '.',
                                    'pixel': ',',
                                    'circle': 'o',
                                    'triangle_down': 'v',
                                    'triangle_up': '^',
                                    'triangle_left': '<',
                                    'triangle_right': '>',
                                    'tri_down': '1',
                                    'tri_up': '2',
                                    'tri_left': '3',
                                    'tri_right': '4',
                                    'octagon': '8',
                                    'square': 's',
                                    'pentagon': 'p',
                                    'plus (filled)': 'P',
                                    'star': '*',
                                    'hexagon1': 'h',
                                    'hexagon2': 'H',
                                    'plus': '+',
                                    'x': 'x',
                                    'x (filled)': 'X',
                                    'diamond': 'D',
                                    'thin_diamond': 'd',
                                    'vline': '|',
                                    'hline': '_',
                                    'tickleft': 0,
                                    'tickright': 1,
                                    'tickup': 2,
                                    'tickdown': 3,
                                    'caretleft': 4,
                                    'caretright': 5,
                                    'caretup': 6,
                                    'caretdown': 7,
                                    'string ex: @': 'string(@)'}
                    return valid_types

        class __Axis(object):
            def __init__(self):
                self.x = self._base_axis()
                self.y = self._base_axis()
                self.z = self._base_axis()

            class _base_axis(object):
                def __init__(self):
                    self.title = self.__base_title()
                    self.axis_scale = self.__base_scale()
                    self.range = self.__base_range()
                    self.lines = self.__base_nparray()
                    self.peaks = self.__base_nparray()
                    self.peak_bounds = self.__base_list()
                    self.integrals = self.__base_list()

                class __base_nparray(object):
                    def __init__(self):
                        self.__base_array = np.array([])
                        self.is_visible = self.hide()

                    def append(self, constant):
                        if not is_iterable(constant):
                            constant = [float(constant)]
                        self.__base_array = np.append(self.__base_array, constant, axis=0)

                    def get(self) -> np.array:
                        return self.__base_array

                    def set(self, value_list: list):
                        if type(value_list) is str:
                            lines = ast.literal_eval(value_list)
                        if type(value_list) in [int, float]:
                            lines = [value_list]
                        if is_iterable(value_list):
                            self.__base_array = np.array(value_list)
                        else:
                            raise ValueError(f"Invalid parameter type: {type(value_list)}; Expecting List type!")

                    def show(self, yes=True) -> bool:
                        self.is_visible = yes
                        return self.is_visible

                    def hide(self, yes=True) -> bool:
                        self.is_visible = False if yes is True else True
                        return self.is_visible

                class __base_list(object):
                    def __init__(self):
                        self.__base = []
                        self.is_visible = self.hide()

                    def add(self, bounds: tuple):
                        if is_iterable(bounds):
                            if is_iterable(bounds[0]):
                                for b in bounds:
                                    self.__base.append(tuple(list(b)[:2]))
                            else:
                                self.__base.append(tuple(list(bounds)[:2]))
                        else:
                            raise ValueError(f"Invalid parameter type:{type(bounds)}; " +
                                             f"Expecting tuple or list of tuples")

                    def get(self) -> list:
                        return self.__base

                    def set(self, bounds: list):
                        to_set = []
                        if is_iterable(bounds):
                            if is_iterable(bounds[0]):
                                for b in bounds:
                                    to_set.append(tuple(list(b)[:2]))
                            else:
                                to_set = [tuple(list(bounds)[:2])]
                            self.__base = to_set
                        else:
                            raise ValueError(f"Unexpected data type: {type(bounds)}. " +
                                             f"Expecting list of tuples: [(lower_bound, upper_bound),...]!")

                    def show(self, yes=True) -> bool:
                        self.is_visible = yes
                        return self.is_visible

                    def hide(self, yes=True) -> bool:
                        self.is_visible = False if yes is True else True
                        return self.is_visible

                class __base_range(object):
                    def __init__(self):
                        self.__range = tuple([])

                    def set(self, range: tuple):
                        if is_iterable(range):
                            self.__range = tuple(list(range)[:2])
                        else:
                            raise ValueError(f"Type: {type(range)} is not valid. Expecting: tuple or list")

                    def get(self) -> str:
                        data = [x for x in self.__range if np.isfinite(x) and not np.isnan(x)]
                        return tuple([np.nanmin(data), np.nanmax(data)]) if len(data) > 1 else tuple([])

                class __base_scale(object):
                    def __init__(self):
                        self.__scale_base = 'linear'
                        self.__valid_types = self.return_valid_types()

                    def set(self, scale_type: str):
                        if scale_type.lower() in self.__valid_types:
                            self.__scale_base = scale_type.lower()
                        else:
                            raise ValueError(f"Type: {scale_type} is not valid. Expecting: {str(self.__valid_types)}")

                    def get(self) -> str:
                        return self.__scale_base

                    @staticmethod
                    def return_valid_types():
                        return ["linear", "log", "symlog", "logit"]

                class __base_title(object):
                    def __init__(self):
                        self.__base = ''

                    def set(self, title: str):
                        self.__base = str(title)

                    def get(self) -> str:
                        return self.__base

        class __Polygons(object):
            def __init__(self):
                self.__base_val = []
                self.is_visible = self.hide()

            def get(self, index=-1) -> np.array:
                if index == -1:
                    return self.__base_val
                else:
                    return self.__base_val[index]

            def add_verticies(self, vertex, polygon_index=0):
                self.__base_val[polygon_index] = np.append(self.__base_val[polygon_index], vertex, axis=0)

            def set(self, verticies_list, index=-1):
                if index == -1:
                    if type(verticies_list[0]) is list:
                        self.__base_val = verticies_list
                    else:
                        self.__base_val = [verticies_list]
                else:
                    self.__base_val[index] = verticies_list

            def add_polygon(self, verticie_list: list):
                self.__base_val.append(np.array(verticie_list))

            def remove_polygon(self, index: int):
                del self.__base_val[index]

            def clear(self):
                self.__base_val = []

            def show(self, yes=True) -> bool:
                self.is_visible = yes
                return self.is_visible

            def hide(self, yes=True) -> bool:
                self.is_visible = False if yes is True else True
                return self.is_visible

    class __Comments(object):
        def __init__(self):
            self.comments = []

        def length(self) -> int:
            return len(self.comments)

        def get(self) -> list:
            return self.comments

        def set(self, user_comment: iter):
            if not is_iterable(user_comment):
                user_comment = [str(user_comment)]
            self.comments = [str(x) for x in user_comment]

        def add(self, user_comment: str):
            if is_iterable(user_comment):
                user_comment = str(user_comment)[1:-1]
            self.comments.append(user_comment)

        def remove_comment_by_index(self, index: int):
            if index not in range(self.length()):
                raise ValueError(f"Index: {index} is out of range: 0 - {self.length()}")
            del self.comments[index]

        def all_as_string(self) -> str:
            str_out = ''
            is_append = False
            for c in self.comments:
                is_append = True
                str_out += c + ' | '
            if is_append:
                str_out = str_out[:-3]
            return str_out

    def to_dict(self):
        output = {'data_x': self.data.x.get(),
                  'data_xe': self.data.xe.get(),
                  'data_y': self.data.y.get(),
                  'data_ye': self.data.ye.get(),
                  'data_z': self.data.z.get(),
                  'data_ze': self.data.ze.get(),
                  'category_x': self.category.x.get(),
                  'category_y': self.category.y.get(),
                  'category_z': self.category.z.get(),
                  'model_x': self.model.x.get(),
                  'model_y': self.model.y.get(),
                  'model_z': self.model.z.get(),
                  'residuals_x': self.residuals.x.get(),
                  'residuals_y': self.residuals.y.get(),
                  'residuals_z': self.residuals.z.get(),
                  'instrument_response_x': self.instrument_response.x.get(),
                  'instrument_response_y': self.instrument_response.y.get(),
                  'instrument_response_z': self.instrument_response.z.get(),
                  'plot_title': self.plot.title.get(),
                  'plot_type': self.plot.type.get(),
                  'plot_polygons': self.plot.polygons.get(),
                  'plot_use_weighted_residuals': self.plot.use_weighted_residuals,
                  'plot_series_name': self.plot.series.name.get(),
                  'plot_series_color': self.plot.series.color.get(),
                  'plot_series_type': self.plot.series.type.get(),
                  'plot_series_weight': self.plot.series.weight.get(),
                  'plot_x_title': self.plot.axis.x.title.get(),
                  'plot_x_type': self.plot.axis.x.axis_scale.get(),
                  'plot_x_integrals': self.plot.axis.x.integrals.get(),
                  'plot_x_lines': self.plot.axis.x.lines.get(),
                  'plot_x_peak_bounds': self.plot.axis.x.peak_bounds.get(),
                  'plot_x_peaks': self.plot.axis.x.peaks.get(),
                  'plot_x_range': self.plot.axis.x.range.get(),
                  'plot_y_title': self.plot.axis.y.title.get(),
                  'plot_y_type': self.plot.axis.y.axis_scale.get(),
                  'plot_y_integrals': self.plot.axis.y.integrals.get(),
                  'plot_y_lines': self.plot.axis.y.lines.get(),
                  'plot_y_peak_bounds': self.plot.axis.y.peak_bounds.get(),
                  'plot_y_peaks': self.plot.axis.y.peaks.get(),
                  'plot_y_range': self.plot.axis.y.range.get(),
                  'plot_z_title': self.plot.axis.z.title.get(),
                  'plot_z_type': self.plot.axis.z.axis_scale.get(),
                  'plot_z_integrals': self.plot.axis.z.integrals.get(),
                  'plot_z_lines': self.plot.axis.z.lines.get(),
                  'plot_z_peak_bounds': self.plot.axis.z.peak_bounds.get(),
                  'plot_z_peaks': self.plot.axis.z.peaks.get(),
                  'plot_z_range': self.plot.axis.z.range.get(),
                  'comments': self.comments.all_as_string(),
                  }
        output = {k: str(v) for k, v in output.items() if str(v) not in ['[]', '()', 'None', '']}
        return output


def is_iterable(element):
    if type(element) is str:
        return False
    try:
        iterator = iter(element)
    except TypeError:
        return False
    else:
        return True