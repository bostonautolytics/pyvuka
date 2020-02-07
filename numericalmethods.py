import numpy as np
import scipy
import data_obj


def lambertw(val):
    i = 0
    p = e = t = w = 0.00000
    eps = 4.0e-16 #eps = desiredprecision
    if val < -0.36787944117144232159552377016146086:
        return -np.inf #should return failure
    if val == 0:
        return 0.0
    #get initial approximation for iteration
    if val < 1.0: #series near 0
        p = np.sqrt(2.0 * (2.7182818284590452353602874713526625 * val+1.0))
        w = -1.0+p-p * p / 3.0+11.0 / 72.0 * p * p * p
    else: #asymptotic
        w = np.log(val)
    if val > 3.0:
        w -= np.log(w)
    while i < 20:  # Halley loop
        e = np.exp(w)
        t = w * e - val
        t /= e * (w + 1.0) - 0.5 * (w + 2.0) * t / (w + 1.0)
        w -= t
        if np.abs(t) < eps * (1.0 + np.abs(w)):
            return w  # rel - abs error
        i += 1
    # never gets here
    return np.inf


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


def calc_integral(x_list, y_list):
	# require x for future implementations that may use dX
    x_out = []
    y_out = []
    for i in range(len(x_list)):
        if i == 0:
            x_out.append(x_list[i])
            y_out.append(y_list[i])
        else:
            x_out.append(x_list[i])
            y_out.append(y_list[i] + y_out[i-1])
    return x_out, y_out


def sav_golay_filter(data_vector, window_length=15, polyorder=3, deriv=0, delta=1.0, axis=-1, mode='interp', cval=0.0):
    return scipy.signal.savgol_filter(data_vector, window_length, polyorder, deriv, delta, axis, mode, cval)
