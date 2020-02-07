import ModuleLink.toPyVuka as pyvuka
import os
import Modules.ipi_common as IPI
import xml.etree.ElementTree as xmlio
import base64
import pack64
import array
import numpy as np
import json


def auto_analysis():
    pyvuka.new_datamatrix()
    exp_dir = get_exp_dir()
    if not exp_dir:
        return
    readfb(exp_dir)
    sortfb()
    for i in range(1, pyvuka.get_datamatrix().length()+1):
        pyvuka.get_datamatrix().buffer(i).plot.axis.x.lines.show()
    scale_by_delta_load()
    scale_by_mw()
    clip_loading_phase()
    set_association_at_zero()
    buffer_subtract()
    get_amplitudes()
    pyvuka.run_pyvuka_command('fun 40 0')
    guess_initial_parameters()
    set_links()
    fit_all(iter=100)
    apply_amp_cutoff()
    set_y_range()
    calc_score_fxn()
    write_xlsx(os.path.join(os.path.basename(exp_dir + '_processed.xlsx')))
    clean_up(exp_dir)
    pass


def set_association_at_zero():
    origin = pyvuka.get_datamatrix().buffer(1).plot.axis.x.lines.get()[-2]
    origin_pt_num = pyvuka.get_datamatrix().buffer(1).data.x.nearest_index_to_value(origin) + 1
    pyvuka.run_pyvuka_command(f"ori -x -y {1} {pyvuka.get_datamatrix().length()} {origin_pt_num}")


def clip_loading_phase():
    dm = pyvuka.get_datamatrix()
    loading_end_idx = dm.buffer(1).data.x.nearest_index_to_value(dm.buffer(1).plot.axis.x.lines.get()[-3])
    for i in range(1, dm.length() + 1):
        dm.buffer(i).data.x.set(dm.buffer(i).data.x.get()[loading_end_idx:])
        dm.buffer(i).data.y.set(dm.buffer(i).data.y.get()[loading_end_idx:])
        dm.buffer(i).plot.axis.x.lines.set(dm.buffer(i).plot.axis.x.lines.get()[1:])
    pyvuka.set_datamatrix(dm)


def scale_by_mw():
    dm = pyvuka.get_datamatrix()
    mw = 150000
    avg_aa_mw = 120
    Dia_mAb = 12e-9 #12nm length due to biased orientation on sensor
    Dia_ag = 12e-9 #Default value (if no mw supplied) results in no scaling
    assoc_start_idx = dm.buffer(1).data.x.nearest_index_to_value(dm.buffer(1).plot.axis.x.lines.get()[-2])
    for i in range(1, dm.length() +1):
        if 'ag_mw' in dm.buffer(i).meta_dict and float(dm.buffer(i).meta_dict['ag_mw']) > 1:
            mw = float(dm.buffer(i).meta_dict['ag_mw'])
            mw = mw if mw > 1000 else mw*1000
            Dia_ag = np.power((mw/avg_aa_mw), 1/3)*(0.00000000069)
        baseline = dm.buffer(i).data.y.get()[:assoc_start_idx]
        binding = dm.buffer(i).data.y.get()[assoc_start_idx:] * Dia_mAb/Dia_ag
        delta = binding[0] - baseline[-1]
        dm.buffer(i).data.y.set(np.concatenate((baseline, (binding-delta)), axis=None))
        dm.buffer(i).plot.axis.y.title.set("Response Scaled by Loading Amp. & Est. Antigen Diameter\n(Avg Number of Molecules Bound)")
    pyvuka.set_datamatrix(dm)


def scale_by_delta_load():
    dm = pyvuka.get_datamatrix()
    last_idx = dm.buffer(1).data.x.nearest_index_to_value(dm.buffer(1).plot.axis.x.lines.get()[-3])
    new_origin_idx = dm.buffer(1).data.x.nearest_index_to_value(dm.buffer(1).plot.axis.x.lines.get()[-2])
    delta = []
    loading_amp_co = 0.1

    for i in range(1, dm.length() + 1):
        delta.append(dm.buffer(i).data.y.value_at_index(last_idx)-dm.buffer(i).data.y.value_at_index(0))

    mind, maxd = [min(delta), max(delta)]

    t = dm.length()
    s = len(delta)

    for i in range(1, dm.length() + 1):
        dm.buffer(i).data.y.set((dm.buffer(i).data.y.get() - mind) / (maxd-mind))
        if delta[i-1] >= loading_amp_co:
            scalar = 1/abs(dm.buffer(i).data.y.value_at_index(0))
        else:
            scalar = 0
        dm.buffer(i).data.y.set(dm.buffer(i).data.y.get() * scalar)

        # set origin at association and remove loading phase
        cor_x_val = dm.buffer(i).data.x.value_at_index(new_origin_idx)
        cor_y_val = dm.buffer(i).data.y.value_at_index(new_origin_idx)
        dm.buffer(i).data.x.set(dm.buffer(i).data.x.get() - cor_x_val)
        dm.buffer(i).data.y.set(dm.buffer(i).data.y.get() - cor_y_val)
        dm.buffer(i).plot.axis.x.lines.set([x-cor_x_val for x in dm.buffer(i).plot.axis.x.lines.get()])
        dm.buffer(i).plot.axis.y.title.set("Response Scaled by Loading Amp. (nm)")

    pyvuka.set_datamatrix(dm)


def get_exp_dir():
    dir_names = os.listdir(pyvuka.get_current_working_directory())
    dir_names = [os.path.join(pyvuka.get_current_working_directory(), folder) for folder in dir_names if 'processed' != folder.lower() and 'raw' != folder.lower()]
    for name in dir_names:
        exp_dir_list = os.listdir(name)
        lock_list = IPI.get_file_list_nested(name, '.lock')
        file_list = sort_for_exp(IPI.get_file_list_nested(name, '.frd'))
        if not file_list or lock_list or len(exp_dir_list) != 6:
            pass
        else:
            return name
    return False


def readfb(exp_dir):
    file_list = sort_for_exp(IPI.get_file_list_nested(exp_dir, '.frd'))
    for files in file_list:
        ignoreregenerationaandneutralization = True
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
        infile = xmlio.parse(os.path.join(exp_dir, files), parser=xmlio.XMLParser(encoding='iso-8859-5')).getroot()
        for expinfo in infile.findall('ExperimentInfo'):
            SensorName = expinfo.find('SensorName').text
            SensorType = expinfo.find('SensorType').text
            SensorRole = expinfo.find('SensorRole').text
            SensorInfo = expinfo.find('SensorInfo').text
        for kindata in infile.findall('KineticsData'):
            for stepdata in kindata.findall('Step'):
                for commondata in stepdata.findall('CommonData'):
                    if ignoreregenerationaandneutralization:
                        WellType.append(commondata.find('WellType').text)
                        if WellType[-1].upper() == 'REGENERATION' or WellType[-1] == 'NEUTRALIZATION':
                            WellType.pop()
                            continue # skip step
                        else:
                            WellType.pop()
                    Concentration.append(commondata.find('Concentration').text)
                    MolarConcentration.append(commondata.find('MolarConcentration').text)
                    SampleID.append(commondata.find('SampleID').text)
                    if commondata.find('SampleGroup') is not None:
                        SampleGroup.append(commondata.find('SampleGroup').text)
                    else:
                        SampleGroup.append(None)
                    WellType.append(commondata.find('WellType').text)
                    MW.append(commondata.find('MolecularWeight').text)
                    Xdata.append(np.array(array.array('f', base64.b64decode(stepdata.find('AssayXData').text))))
                    Ydata.append(np.array(array.array('f', base64.b64decode(stepdata.find('AssayYData').text))))
                    StepName.append(stepdata.find('StepName').text)
                    ActualTime.append(stepdata.find('ActualTime').text)
                    StepStatus.append(stepdata.find('StepStatus').text)
                    StepLoc.append(commondata.find('SampleRow').text + commondata.find('SampleLocation').text)
                    StepType.append(stepdata.find('StepType').text)
        for status in StepStatus:
            if not status == 'OK':
                Flags.append('Sensor:' + status)
                break


        step_initial = 1 # include loading
        step_split = 5
        cycles = 2
        for x in range(0, cycles, 1):
            buffer = pyvuka.new_buffer()
            trimX = Xdata[step_initial:step_split]
            x_to_zero = trimX[0][-1]
            for z, data in enumerate(trimX):
                data = np.array(data)
                if z == 1:
                    data = data - float(x_to_zero + (data[0] - trimX[z-1][-1]))
                elif z > 1:
                    data = data - float(data[0] - buffer.data.x.value_at_index(-1))
                else:
                    data = data-float(x_to_zero)
                buffer.data.x.append(data)
                buffer.plot.axis.x.lines.append(data[0])
            trimY = Ydata[step_initial:step_split]

            for z, data in enumerate(trimY):
                if z == 0:
                    data = data - trimY[0][-1]
                else:
                    data = data-float(data[0]-buffer.data.y.value_at_index(-1))
                buffer.data.y.append(data)

            buffer.data.z.set([float(MolarConcentration[-2])] * buffer.data.y.length())

            buffer.comments.set([SampleID[step_initial] + " on " + SensorType[:3] + " vs " +
                                       SampleID[step_initial+2] + " @ " +
                                       str("{:.2E}".format(float(MolarConcentration[step_initial+2]))) + "nM"])
            buffer.plot.series.name.set(buffer.comments.all_as_string())
            buffer.plot.title.set(buffer.plot.series.name.get())
            buffer.plot.axis.x.title.set("Time (s)")
            buffer.plot.axis.y.title.set("Response (nm)")
            buffer.plot.axis.x.lines.show()
            buffer.meta_dict['ag_mw'] = float(MW[step_initial+2]) if float(MW[step_initial+2]) < 1000 else float(MW[step_initial+2])/1000
            pyvuka.add_buffer_to_datamatrix(buffer)
            step_initial += step_split
            step_split += step_initial
    return "ForteBio data read into memory."


def get_amplitudes():
    dm = pyvuka.get_datamatrix()
    end_base_idx = dm.buffer(1).data.x.nearest_index_to_value(dm.buffer(1).plot.axis.x.lines.get()[-2])
    end_assoc_idx = dm.buffer(1).data.x.nearest_index_to_value(dm.buffer(1).plot.axis.x.lines.get()[-1])
    for i in range(1, dm.length() + 1):
        dm.buffer(i).meta_dict['baseline_amp'] = np.max(dm.buffer(i).data.y.get()[:end_base_idx])
        dm.buffer(i).meta_dict['association_amp'] = np.max(dm.buffer(i).data.y.get()[end_base_idx:end_assoc_idx])
    pyvuka.set_datamatrix(dm)


def sortfb():
    datamatrix_1 = pyvuka.new_datamatrix()
    datamatrix_2 = pyvuka.new_datamatrix()
    dm = pyvuka.get_datamatrix()
    for i in range(1, dm.length() + 1):
        if i%2 != 0:
            datamatrix_1.add_buffer(dm.buffer(i))
        else:
            datamatrix_2.add_buffer(dm.buffer(i))
    pyvuka.set_datamatrix(datamatrix_1)
    pyvuka.append_datamatrix(datamatrix_2)


def sort_for_exp(filelist):
    tuple_list = [(file, int(file.split('_')[-1][:-4])) for file in filelist]
    sorted_tuple_list = sorted(tuple_list, key=lambda x: x[1])
    return_list, key_list = zip(*sorted_tuple_list)
    return return_list


def guess_initial_parameters():
    # reference: Rmax, kd, ka, Cp, m, c, x0, kds = parameters
    dm = pyvuka.get_datamatrix()
    for i in range(1, dm.length() + 1):
        max_y = dm.buffer(i).data.y.max()
        final_y = dm.buffer(i).data.y.value_at_index(-1)
        rmax = max_y
        kd = 0.001
        ka = 60000
        Cp = dm.buffer(i).data.z.value_at_index(0) * 1E-9
        m = 0
        if (final_y <= max_y * 0.2 or final_y >= max_y * 0.8) and final_y >= 0:
            # if really slow off or relatively fast off, assume c = 0.  If final_y < 0, set c
            c = 0
        else:
            # otherwise kinetics are potentially multiphasic or do not otherwise approach 0
            c = final_y

        x0 = dm.buffer(i).plot.axis.x.lines.get()[-1]
        kds = 1
        pyvuka.run_pyvuka_command(f'ap {i} {rmax} {kd} {ka} {Cp} {m} {c} {x0} {kds}')
    return


def buffer_subtract():
    dm = pyvuka.get_datamatrix()
    for i in reversed(range(0, dm.length(), 3)):
        lastbuffer = i+3
        pyvuka.run_pyvuka_command(f'sbf {lastbuffer - 2} {lastbuffer-1} {lastbuffer}')
        pyvuka.run_pyvuka_command(f'sbf {lastbuffer - 2} {lastbuffer - 2} {lastbuffer - 2}')


def set_links():
    # reference: Rmax, kd, ka, Cp, m, c, x0, kds = parameters
    dm = pyvuka.get_datamatrix()
    pyvuka.run_pyvuka_command('fre all')
    pyvuka.run_pyvuka_command('unl all')
    pyvuka.run_pyvuka_command('fix 4')
    pyvuka.run_pyvuka_command('fix 5')
    pyvuka.run_pyvuka_command('fix 6')
    pyvuka.run_pyvuka_command('fix 7')
    pyvuka.run_pyvuka_command('fix 8')
    for i in range(1, dm.length() + 1, 3):
        buffer_set = [i, i+1, i+2]

        # if c!=0, float c
        for j in buffer_set:
            if dm.buffer(j).fit.parameter.get()[5] < 0:
                pyvuka.run_pyvuka_command(f'fix {j} 6')

        # add conditional to not link if both assoc:base amps < 2 (signal cutoff) 12/10/2019
        # ignore buffer_set[0] due to 0nm conc
        assoc_amp_1 = dm.buffer(buffer_set[1]).meta_dict['association_amp']
        base_amp_1 = dm.buffer(buffer_set[1]).meta_dict['baseline_amp']
        assoc_amp_2 = dm.buffer(buffer_set[2]).meta_dict['association_amp']
        base_amp_2 = dm.buffer(buffer_set[2]).meta_dict['baseline_amp']
        if (assoc_amp_2 > base_amp_2 and assoc_amp_1 > base_amp_1) and \
                (assoc_amp_2/base_amp_2 >= 2 and assoc_amp_1/base_amp_1 >= 2):
            pyvuka.run_pyvuka_command(f'lnk {buffer_set[2]} {2} {buffer_set[1]} {2}')
            pyvuka.run_pyvuka_command(f'lnk {buffer_set[2]} {3} {buffer_set[1]} {3}')
    return


def fit_all(iter=np.inf):
    dm = pyvuka.get_datamatrix()
    for i in range(1, len(dm) + 1, 3):
        buffer = dm.buffer(i)
        pyvuka.run_pyvuka_command('pl off')
        pyvuka.run_pyvuka_command(f'pl -v {i} {i+2} {buffer.plot.axis.x.lines.get()[1]} 1E6')
        if np.isinf(iter):
            pyvuka.run_pyvuka_command('fit -debug')
        else:
            pyvuka.run_pyvuka_command(f'fit {int(iter)} -debug')
    pyvuka.run_pyvuka_command('pl off')


def apply_amp_cutoff():
    assoc_amp_co = 0.01
    dm = pyvuka.get_datamatrix()
    for i in range(1, dm.length() + 1, 1):
        if dm.buffer(i).meta_dict['association_amp'] < dm.buffer(i).meta_dict['baseline_amp'] or \
                dm.buffer(i).meta_dict['association_amp'] / dm.buffer(i).meta_dict['baseline_amp'] < 2 or \
                dm.buffer(i).meta_dict['association_amp'] < assoc_amp_co:
            dm.buffer(i).model.x.clear()
            dm.buffer(i).model.y.clear()
            p = dm.buffer(i).fit.parameter.get()
            p[0] = -1
            p[1] = 0
            dm.buffer(i).fit.parameter.set(p)
            dm.buffer(i).fit.parameter_error.set([1E6]*len(dm.buffer(i).fit.parameter_error.get()))
            dm.buffer(i).fit.rsq.set(-1)
        elif dm.buffer(i).model.y.max() > (2 * dm.buffer(i).data.y.max()):
            max_co = 2 * dm.buffer(i).data.y.max()
            y_model = dm.buffer(i).model.y.get()
            # pack64 algo only works with data ranges in certain orders of magnitude.  here we alter unresonable values max co
            dm.buffer(i).model.y.set([y if y <= max_co else max_co for y in y_model])
    pyvuka.set_datamatrix(dm)


def calc_score_fxn():
    dm = pyvuka.get_datamatrix()
    dis_start_idx = dm.buffer(1).data.x.nearest_index_to_value(dm.buffer(1).data.x.get()[-1])
    ideal_stoichiometry = 2
    for i in range(len(dm)):
        first_y = dm.buffer(i).data.y.value_at_index(dis_start_idx)
        perfect_integral = np.abs(first_y * len(dm.buffer(i).data.x.get()[dis_start_idx:]))
        exp_integral = np.sum(dm.buffer(i).data.y.get()[dis_start_idx:])
        score = (exp_integral / perfect_integral) * (first_y / ideal_stoichiometry)
        dm.buffer(i).meta_dict['ipi_score'] = score
    pyvuka.set_datamatrix(dm)


def write_xlsx(xlsx_name):
    output_dir = IPI.create_IPI_output_dir(pyvuka.get_output_directory())

    filename = os.path.join(output_dir, xlsx_name)
    out_file = IPI.xlsx_out(filename)
    out_file.experiment = 'FORTEBIO'
    header = ['Plate', 'Sensor', 'Sensor_Protein', 'Solution_Protein', 'asymtope', 'kd',
              'kd_error', 'ka', 'ka_error', 'Conc', 'Keq', 'Keq_error',
              'Avg_Rsq', 'ipi-score (higher=better)', 'Comments', 'Plot_png', 'JSON']
    out_file.add_header(header)
    out_file.col_widths = [19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 58, 58]
    out_file.row_heights = 228

    dm = pyvuka.get_datamatrix()
    for i in range(1, dm.length() + 1, 3):
        buffer_set = [i, i + 1, i + 2]
        comments = ''
        parameters = ['None' if val is None or np.isnan(val) or not np.isfinite(val) else float(val) for val in
                      dm.buffer(buffer_set[-1]).fit.parameter.get()]
        parameters_err = ['None' if val is None or np.isnan(val) or not np.isfinite(val) else float(val) for val in
                          dm.buffer(buffer_set[-1]).fit.parameter_error.get()]

        Rmax, kd, ka, Cp, m, c, x0, kds = parameters
        if len(parameters_err) != len(parameters):
            parameters_err = [1e6] * len(parameters)
        Rmax_err, kd_err, ka_err, Cp_err, m_err, c_err, x0_err, kds_err = parameters_err

        # catch div by zero
        try:
            KD = kd/ka
        except:
            KD = -1
            comments = 'Fail : KD can not be calculated'

        try:
            KD_err = np.power(np.power(kd_err/kd, 2) + np.power(ka_err/ka, 2), 0.5) * KD
        except:
            KD_err = -1

        # Check rsq values to ensure fit has been made, if fit fails, rsq is nan
        rsq_1 = [-1 if np.isnan(val) or not np.isfinite(val) else float(val) for val in
                 [dm.buffer(buffer_set[0]).fit.rsq.get()]][0]
        rsq_2 = [-1 if np.isnan(val) or not np.isfinite(val) else float(val) for val in
                 [dm.buffer(buffer_set[1]).fit.rsq.get()]][0]
        rsq_3 = [-1 if np.isnan(val) or not np.isfinite(val) else float(val) for val in
                 [dm.buffer(buffer_set[2]).fit.rsq.get()]][0]
        avg_rsq = np.average([x for x in [rsq_1, rsq_2, rsq_3] if x >= 0])
        if np.isnan(avg_rsq):
            avg_rsq = -1
            comments = 'Fail : Insufficient s/n'

        # Check ipi-score values to ensure fit has been made, if fit fails, rsq is nan
        # score_1 = datamatrix[i].item['ipi_score'] 0nm conc
        score_2 = dm.buffer(buffer_set[1]).meta_dict['ipi_score']
        score_3 = dm.buffer(buffer_set[2]).meta_dict['ipi_score']
        avg_score = float(np.average([score_2, score_3]))
        if np.isnan(avg_score) or comments == 'Fail : Insufficient s/n':
            avg_score = -1
            comments = 'Fail : Insufficient s/n'

        # Check ampplitude cutoff of 0.01, fail low amplitudes
        amplitudes = [dm.buffer(buffer_set[0]).meta_dict['association_amp'],
                      dm.buffer(buffer_set[1]).meta_dict['association_amp'],
                      dm.buffer(buffer_set[2]).meta_dict['association_amp']]
        if max(amplitudes) < 0.01:
            comments = 'Fail : Insufficient association amplitude'

        # Check comments for fit failure. Remove model if fit failed
        if 'fail' in comments.lower():
            for j in buffer_set:
                dm.buffer(j).model.x.clear()
                dm.buffer(j).model.y.clear()


        Cp = "{}, {}, {}".format(*[dm.buffer(buffer_set[0]).fit.parameter.get()[3],
                                   dm.buffer(buffer_set[1]).fit.parameter.get()[3],
                                   dm.buffer(buffer_set[2]).fit.parameter.get()[3]])
        sensor_pro = dm.buffer(i).plot.series.name.get().split('on')[0].strip()
        sensor = dm.buffer(i).plot.series.name.get().split('on ')[1].split(' ')[0].strip()
        sol_pro = dm.buffer(i).plot.series.name.get().split('vs')[1].split('@')[0].strip()

        # construct xlsx line entry
        out_line = ['Plate', sensor, sensor_pro, sol_pro, c, kd, kd_err, ka, ka_err, Cp, KD, KD_err,
                    avg_rsq, avg_score, comments, None, None]
        LIMS_dict = {}


        plot_png = pyvuka.get_plot_as_bytestring([i, i+1, i+2], get_bytes=True, black_models=True)

        JSON = {
                'data_x_1': pack64.pack64(dm.buffer(buffer_set[0]).data.x.get()),
                'data_y_1': pack64.pack64(dm.buffer(buffer_set[0]).data.y.get()),
                'model_x_1': pack64.pack64(dm.buffer(buffer_set[0]).model.x.get()),
                'model_y_1': pack64.pack64(dm.buffer(buffer_set[0]).model.y.get()),
                'data_x_2': pack64.pack64(dm.buffer(buffer_set[1]).data.x.get()),
                'data_y_2': pack64.pack64(dm.buffer(buffer_set[1]).data.y.get()),
                'model_x_2': pack64.pack64(dm.buffer(buffer_set[1]).model.x.get()),
                'model_y_2': pack64.pack64(dm.buffer(buffer_set[1]).model.y.get()),
                'data_x_3': pack64.pack64(dm.buffer(buffer_set[2]).data.x.get()),
                'data_y_3': pack64.pack64(dm.buffer(buffer_set[2]).data.y.get()),
                'model_x_3': pack64.pack64(dm.buffer(buffer_set[2]).model.x.get()),
                'model_y_3': pack64.pack64(dm.buffer(buffer_set[2]).model.y.get()),
                'plot_x_lines': str(dm.buffer(buffer_set[0]).plot.axis.x.lines.get())
            }

        out_line[-2] = plot_png
        out_line[-1] = JSON

        for j in range(len(header)):
            key = header[j].lower()
            val = out_line[j]
            if '_png' not in key:
                if key == 'json':
                    key = 'data_xy'
                LIMS_dict.update({key: val})
        out_line[-1] = json.dumps(LIMS_dict)
        out_file.add_line(out_line)

    out_file.write_xlsx()
    return


def set_y_range():
    dm = pyvuka.get_datamatrix()
    y_vals = []
    for i in range(len(dm)):
        buffer = dm.buffer(i)
        y_vals += [buffer.data.y.min(), buffer.data.y.max()]
        if buffer.model.y.length() >= 1:
            y_vals += [buffer.model.y.min(), buffer.model.y.max()]

    ymin, ymax = [min(y_vals)*.95, max(y_vals)*1.05]

    for i in range(1, dm.length() + 1):
        dm.buffer(i).plot.axis.y.range.set([ymin, ymax])
    pyvuka.set_datamatrix(dm)
    return


def clean_up(exp_dir):
    raw_dir = IPI.create_IPI_output_dir(os.path.join(os.path.dirname(exp_dir), 'Raw'))
    IPI.native_copy_nested(exp_dir, os.path.join(raw_dir, os.path.basename(exp_dir)))
    IPI.remove_all_folder(exp_dir)
