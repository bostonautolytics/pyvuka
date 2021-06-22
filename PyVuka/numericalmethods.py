import numpy as np
import scipy


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


def peak_pick(xdata, ydata, threshold, *args, **kwargs):
        notpeak1 = 0
        notpeak2 = 0
        allpeaks = []
        allint = []
        savek = 0
        res = 1
        positivepeaks = True

        if 'positive_peaks' in kwargs.keys():
            positivepeaks = bool(kwargs['positive_peaks'])
        if 'resolution' in kwargs.keys():
            res = int(kwargs['resolution'])

        if positivepeaks == False:
            for k in range(res, int(np.size(ydata)) - res, 1):
                for m in range(k - res, k, 1):
                    if ydata[m] >= ydata[k] and ydata[m] >= ydata[m + 1]:
                        notpeak1 += 1
                for n in range(k + res, k, -1):
                    if ydata[n] >= ydata[k] and ydata[n - 1] <= ydata[n]:
                        notpeak2 += 1
                if notpeak1 == res and notpeak2 == res and \
                        abs(ydata[k] - ydata[0]) >= abs(threshold) and ydata[k] < ydata[0]:
                    if k == savek + 1:
                        allpeaks[len(allpeaks) - 1] = ((xdata[savek] + xdata[k]) / 2)
                        allint[len(allint) - 1] = ((ydata[savek] + ydata[k]) / 2)
                    else:
                        allpeaks.append(xdata[k])
                        allint.append(ydata[k])
                    savek = k
                notpeak1 = 0
                notpeak2 = 0
        else:
            for k in range(res, int(np.size(ydata)) - res):
                for m in range(k - res, k, 1):
                    if ydata[m] <= ydata[k] and ydata[m] <= ydata[m + 1]:
                        notpeak1 += 1
                for n in range(k + res, k, -1):
                    if ydata[n] <= ydata[k] and ydata[n - 1] >= ydata[n]:
                        notpeak2 += 1
                if notpeak1 == res and notpeak2 == res and abs(ydata[k] - ydata[0]) >= threshold and ydata[k] > \
                        ydata[0]:
                    if k == savek + 1:
                        allpeaks[len(allpeaks) - 1] = ((xdata[savek] + xdata[k]) / 2)
                        allint[len(allint) - 1] = ((ydata[savek] + ydata[k]) / 2)
                    else:
                        allpeaks.append(xdata[k])
                        allint.append(ydata[k])
                    savek = k
                notpeak1 = 0
                notpeak2 = 0
        sortYLowtoHigh = [ap for ai, ap in sorted(zip(allint, allpeaks))]
        if positivepeaks:
            return sortYLowtoHigh[::-1]
        else:
            return sortYLowtoHigh