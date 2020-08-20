import numpy as np
from lmfit import minimize, Parameters, report_fit
from functools import partial
import multiprocessing as mp
import copy
import itertools

#constants
gas_const_kcal = .0019872036

class datafit(object):
    """extend with fxn_index  methods. index must be an integer.

    Docstring text (first line) is parsed for building function table so docstring format must be conserved

        Ex1: Generic Function: Constant (Additive)
            \n
        Ex2: Generic Function: Constant (Additive)\n

        where "Generic Function" is the category of the function and "Constant (additive)" is the function name"

    Remaining doctstring format should be conserved as it is the description used by the 'fun info' command.
        """

    def __init__(self, data_instance, info_commands=('info', '?')):
        self._info_cmd = info_commands
        self.paramid = []
        self.paramval = []
        self.parambounds = []
        self.paramdefaults = []
        self.funcindex = []
        self.functions = []
        self.pyscript = False
        self.tzerooffset = False
        self.pyscriptonly = False
        self.inst = data_instance

    def __call__(self, args):
        if len(args) == 0:
            return 'error'
        elif len(args) == 1 and args[0] == "info":
            return self.info(None)
        elif len(args) > 1 and args[0] == "info":
            return self.info(args[1])

    def update(self, funcnum):
        for num in funcnum:
            fn = getattr(self, 'fxn_' + str(num))
            fn()
        return True

    def clear(self):
        self.paramid = []
        self.paramval = []
        self.parambounds = []
        self.paramdefaults = []
        self.funcindex = []
        self.functions = []
        self.pyscript = []
        return True

    def fxn_1(self, *args):
        """Generic Function: Constant (Additive)
        \nDescription: Function in the form of: Y = C + 0X
        \nParameters:
        \tC\t(constant value)
        """
        self.paramid.extend(["Add_Constant"])
        self.parambounds.extend([[-np.inf, np.inf]])
        self.paramdefaults.extend([0])
        self.functions.extend(["Y=(X*0)+P[0]"])
        return

    def fxn_2(self, *args):
        """Generic Function: Exponential
        \nDescription: Function in the form of: Y = A*e^(-X/t)
        \nParameters:
        \tA\t(exponential amplitude)
        \tt\t(exponential time constant)
        """
        self.paramid.extend(["Amplitude", "Time_Constant"])
        self.parambounds.extend([[-np.inf, np.inf], [0, np.inf]])
        self.paramdefaults.extend([1, 1])
        self.functions.extend(["Y=P[0]*np.exp(-1*X/P[1])"])
        return

    def fxn_3(self, *args):
        """Generic Function: Gaussian 1-D
        \nDescription: Function in the form of: Y = A/(sqrt(2*pi)*WHM))*exp(-(X-CENTER)^2/(2*WHM^2)
        \nParameters:
        \tA   \t(Amplitude)
        \tWHM \t(Full Width at Half Max)
        \tXcen\t(Centered at X-val)
        """
        self.paramid.extend(["Amplitude", "WHM", "Xcen"])
        self.parambounds.extend([[-np.inf, np.inf], [0, np.inf], [-np.inf, np.inf]])
        self.paramdefaults.extend([10, 5, 5])
        self.functions.extend(["Y=(P[0]/(np.sqrt(2*np.pi)*P[1]))*np.exp(-(X-P[2])**2/(2*P[1]**2))"])
        return

    def fxn_27(self, *args):
        """Generic Function: Linear
        \nDescription: Function in the form of: Y = M*X+C
        \nParameters:
        \tM\t(Mul. constant value [slope])
        \tC\t(Add. constant value [y-intercept])
        """
        self.paramid.extend(["Slope", "Y_intercept"])
        self.parambounds.extend([[-np.inf, np.inf], [-np.inf, np.inf]])
        self.paramdefaults.extend([1, 0])
        self.functions.extend(["Y=(P[0]*X)+P[1]"])
        return

    def fxn_30(self, *args):
        """Generic Function: Constant (Multiplicative)
        \nDescription: Function in the form of: Y = M*X
        \nParameters:
        \tM\t(constant value)
        """
        self.paramid.extend(["Mul_Constant"])
        self.parambounds.extend([[-np.inf, np.inf]])
        self.paramdefaults.extend([0])
        self.functions.extend(["Y=X*P[0]"])
        return

    def fxn_14(self, *args):
        """Protein Folding Equilibrium: 2-state Equilibrium, Chemical Denaturant
        \nDescription: Model for equilibrium titration data describing 2 thermodynamic states (U->N)
        \nPubMed ID: 15689503
        \nParameters:
        \tdG \t(Delta G in kcal/Mol)
        \tm  \t(m-value, denaturant dependence of transition in kcal/mol/M)
        \tCn \t(Y-intercept of Native Baseline)
        \tCu \t(Y-intercept of Unfolded Baseline)
        \tMn \t(Slope of Native Baseline)
        \tMu \t(Slope of Unfolded Baseline)
        \tT  \t(Temperature in Kelvin)

        Note: This function requires the X-values to be denaturant concentrations and the Y-values are the experimental signal at that denaturant concentration
        """
        self.paramid.extend(["dG", "m", "Cn", "Cu", "Mn", "Mu", "T"])
        self.parambounds.extend([[-np.inf, np.inf], [-np.inf, np.inf], [-np.inf, np.inf], [-np.inf, np.inf],
                                 [-np.inf, np.inf], [-np.inf, np.inf], [-np.inf, np.inf]])
        self.paramdefaults.extend([5, 1.8, 0, 25000, 1000, 2, 298.15])
        self.functions.extend(["Y=(P[2]+(P[4]*X))+((P[3]+(P[5]*X))*np.exp((P[0]-(P[1]*X))/(gas_const_kcal*P[6])))/(1+np.exp((P[0]-(P[1]*X))/(gas_const_kcal*P[6])))"])
        self.pyscriptonly = False
        return

    def fxn_39(self, *args):
        """Molecular Kinetics Function: CFCA (SPR, Biacore 8K)
        \nDescription: Calibration-Free Concentration Analysis for SPR data. Requires 2 datasets of concentration series
         data collected at different flow rates. One data set should have kinetics that are at least
         partially limited by mass transport. Calculation assumes Biacore 8K flow cell.
        \nPubMed ID: 12081475
        \nParameters:
        \tFd  \t(Fold Dilution from max concentration in series)
        \tF\t \t(Flow Rate in uL/min)
        \tMW  \t(Molecular Weight of Analyte in Da)
        \tT   \t(Temperature of experiment in Celcius)
        \tRmax\t(Maximum SPR Response)
        \tka  \t(Association Rate Constant in 1/Ms)
        \tkd  \t(Dissociation Rate Constant in 1/s)
        \tCa  \t(Concentration of Analyte in M)
        \tt0  \t(Time Zero of Dissociation Data in s)
        \tkc  \t(Mass Transport Coefficient in cm/s.  If user enters 0, estimation with Einstein-Sutherland equation overrides.)
        \tG   \t(Concentration G-Factor in Rcm^2/g. If user enters 0, Defaults to 100000 Rmm^2/ng)
        """
        self.paramid.extend(["Fd", "F", "MW", "T", "Rmax", "ka", "kd", "Ca", "t0", "kc", "G"])
        self.parambounds.extend([[0, np.inf], [0, np.inf], [0, np.inf], [0, np.inf], [0, np.inf], [0, np.inf],
                                 [0, np.inf], [0, np.inf], [-np.inf, np.inf], [0, np.inf], [0, np.inf]])
        self.paramdefaults.extend([1, 30, 14300, 25, 25, 2.3E6, 9.85E-11, 5E-9, 300, 0, 1.0E10])
        self.pyscriptonly = True
        self.pyscript = compile("""
# L1 is the distance from the inlet to the start of the detection area
# L2 is the distance from the inlet to the end of the detection spot
# SpotL and SpotW are the detection spot dimensions
#dimensions are in cm
SpotL = .16
SpotW = 0.02
L1 = .03
L2 = .03 + SpotL
# Flow Cell Dimensions in mm from Christensen paper
CW = 0.05
CH = 0.005
CL = 0.24
# CKC describes the concentration gradient
CKC = 1.47 * ((1 - np.power((L1 / L2), 0.6666666667)) / (1 - (L1 / L2)))
# D is the Diffusion coefficient of analyte estimated using the Einstein-Sutherland equation (christensen paper)
D = (1.381E-23 * (298.15 + P[3])) / (6 * np.pi * np.power((3 * np.pi * P[2] * (7.3E-4 / (4 * np.pi * 6.022E23))), 0.3333333333) * 0.001 * 1.2)
# if user enters 0 for kc, estimate it here:
P[7] = (P[7]/P[0]) #corrects concentration for fold dilution
P[2] = P[2] #MW is in Da
P[1] = (P[1]*60) #converts flowrate from uL/min to uL/sec
P[3] = P[3] + 273.15 #converts C to Kelvin
if P[9] == 0:
    P[9] = CKC * np.power((((D * D) * P[1]) / (np.power(CH,2) * CW * L2)), 0.3333333333)
K1 = (P[7] * P[5]) / ((P[7] * P[5]) + P[6])
K2 = (P[7] * np.power(P[5],2) * P[4]) / ((((P[7] * P[5]) + P[6]) * P[9] * P[2] * P[10]) + (P[5] * P[6] * P[4]))
K3 = (np.power(((P[7] * P[5]) + P[6]), 2) * P[9] * P[2] * P[10]) / (
P[6] * ((((P[7] * P[5]) + P[6]) * (P[9] * P[2] * P[10])) + (P[5] * P[6] * P[4])))
K4 = ((P[2] * P[10] * P[9]) + (P[5] * P[4])) / (P[5] * P[4])
K5 = (P[2] * P[10] * P[9]) / ((P[2] * P[10] * P[9]) + (P[5] * P[4]))
K6 = ((P[2] * P[10] * P[9]) + (P[5] * P[4])) / P[5]
Rz = None
for j in range(len(X)):
    if X[j] <= P[8]:
        # calc association
        Wval = numericalmethods.lambertw(K2 * np.exp(K2 - (K3 * P[6] * X[j])))
        R[j] = P[4] * K1 * (1 - (Wval / K2))
        Rz = float(R[j])
    else:
        # calc dissociation
        Wval = numericalmethods.lambertw(((-1 * Rz) / K6) * np.exp(-1 * ((Rz / K6) + (K5 * P[6] * (X[j] - P[8])))))
        R[j] = (-1 * K6) * Wval
""", '<string>', 'exec')
        self.functions.extend(["Y=X+P[0]"])
        self.pyscriptonly = True
        return

    def fxn_40(self, *args):
            """Molecular Kinetics Function: 1-to-1 Stoiciometery binding model (on & off, same buffer)
            \nDescription: 1:1 Stoiciometery binding model for molecular interactions. Full trace.
            \nPubMed ID: 28430560
            \nParameters:
            \tRmax\t(Response maximum value)
            \tkd  \t(Dissociation rate)
            \tka  \t(Association rate)
            \tCp  \t(Concentration of analyte in solution in Molar)
            \tm   \t(Linear approximation of slow phase)
            \tc   \t(Dissociation asymtote)
            \tX0  \t(Dissociation phase time offset)
            \tkds \t(Dissociation phase scalar)
            """
            self.paramid.extend(["Rmax", "kd", "ka", "Cp", "m", "c", "X0", "kds"])
            self.parambounds.extend([[0, np.inf], [0, np.inf], [0, np.inf], [0, np.inf], [-np.inf, np.inf],
                                     [-np.inf, np.inf], [-np.inf, np.inf], [-6, 6]])
            self.paramdefaults.extend([25, 0.001, 60000, 100E-9, 0, 0, 180, 1])
            self.pyscriptonly = True
            self.pyscript = compile("""
rm, kd, ka, cp, m, c, xo, kds = P
if cp==0:
    cp=1E-15
for j in range(len(X)):
    if X[j] <= xo:
        # calc association
        R[j] = (rm / (1 + (kd / (ka * cp)))) * (1-(np.exp((-1 * X[j] * ((ka * cp) + kd)))))
    else:
        # calc dissociation
        R[j] = kds*(((rm/(1+(kd/(ka*cp))))*(1-np.exp(-1*xo*(ka*cp+kd)))-c))*(np.exp(-1*kd*(X[j]-xo))) + m*(X[j]-xo) + c
""", '<string>', 'exec')

            self.functions.extend(["Y=(P[0]/(1+(P[1]/(P[2]*P[3]))))*(1-(np.exp((-1*X*((P[2]*P[3])+P[1])))))+(P[7]*(((P[0]/(1+(P[1]/(P[2]*P[3]))))*(1-np.exp(-1*P[6]*(P[2]*P[3]+P[1])))-P[5]))*(np.exp(-1*P[1]*(X-P[6])))+P[4]*(X-P[6])+P[5])"])
            return

    def fxn_41(self, *args):
        """Molecular Equilibrium Binding Function: 1-to-1 Stoiciometery binding model using Hill Equation
        \nDescription: 1:1 Stoiciometery binding model for molecular interactions. Hill equation estimate of EC50.
        \nPubMed ID: 19049668
        \nParameters:
        \tEC50    \t(Effective concentrarion for 50% binding)
        \tHillCoef\t(Hill coefficient)
        \tminY    \t(Minimum Y-value)
        \tmaxY    \t(Maximum Y-value)
        """
        self.paramid.extend(["EC50", "HillCoef", "minY", "maxY"])
        self.parambounds.extend([[0, np.inf], [-1000, 1000], [-np.inf, np.inf], [-np.inf, np.inf]])
        self.paramdefaults.extend([5, 1, 0, 100])
        self.functions.extend(["Y=P[2]+((P[3]-P[2])/(1+((P[0]/X)**P[1])))"])
        # Y=minY+((maxY-minY)/(1+((EC50/X[0])^HillCoef)))
        return

    def fxn_42(self, *args):
        """Molecular Equilibrium Binding Function: 1-to-1 Stoiciometery binding model using Quadratic Equation
        \nDescription: 1:1 Stoiciometery binding model for molecular interactions. Quadratic equation estimate of Keq.
        \nPubMed ID: 21115850
        \nParameters:
        \tKeq    \t(Equilibrium dissociation constant)
        \tC      \t(Concentration of constant component)
        \tAmp    \t(Signal Amplitude [max_Y - min_Y])
        \tS0     \t(background signal of unbound [min_Y])
        """
        self.paramid.extend(["Keq", "C", "Amp", "S0"])
        self.parambounds.extend([[0, np.inf], [0, np.inf], [-np.inf, np.inf], [-np.inf, np.inf]])
        self.paramdefaults.extend([0.5, 100, 1000, 0])
        self.functions.extend(["Y=(P[3]+P[2])*((P[1]+X+P[0])-np.power(np.power(P[1]+X+P[0], 2)-(4*P[1]*X), 0.5)) /(2*P[1])"])
        # Y=S0+Amp*((c+X+Keq)-((c+X+Keq)^2 -(4*c*X))^0.5 )/2*c
        return

    def fxn_43(self, *args):
        """Molecular Equilibrium Binding Function: 1-to-1 Stoiciometery Single Site Specific Binding Potential
        \nDescription: 1:1 Stoiciometery binding potential model for molecular interactions. Binding Potential estimate of Keq.
        \nPubMed ID: 6609679
        \nParameters:
        \tKeq    \t(Equilibrium dissociation constant)
        \tBmax   \t(Signal of maximum binding [max_Y])
        \tS0     \t(background signal of unbound [min_Y])
        \nNote (binding potential (BP)):
        \tBP     \t(Bmax/Keq = receptor density * affinity)
        """
        self.paramid.extend(["Keq", "Bmax", "S0"])
        self.parambounds.extend([[0, np.inf], [0, np.inf], [-np.inf, np.inf]])
        self.paramdefaults.extend([0.5, 1000, 0])
        self.functions.extend(["Y=((P[1]*X)/(P[0]+X))+P[2]"])
        # Y=(Bmax*X/(Keq + X))+S0; BP=Bmax/Keq
        return

    def info(self, fxn=None):
        def std_info():
            hc = '|'.join(self._info_cmd)
            res = '\n\tType [%s] fxn_index to get more help about particular command\n' % hc
            fl = self.getfxnlist()
            res += '\n\tAvailable Functions: \n\t%s' % ('  '.join(sorted(fl))) + "\n"
            return res

        if not fxn:
            return std_info()
        else:
            try:
                fn = getattr(self, 'fxn_' + str(fxn))
                doc = fn.__doc__
                return doc or 'No documentation available for %s' % fxn
            except AttributeError:
                return std_info()

    def getfxnlist(self):
        return [name[4:] for name in dir(self) if name.startswith('fxn_') and len(name) > 4]

    def showfxntable(self):
        topline = 100*'_'
        spacer = 86*'.'
        toreturn = "\n\t     Function Name" + 60*' ' + "Function Number\n" + topline + '\n'
        cat = []
        fxnindex = [name[4:] for name in dir(self) if name.startswith('fxn_') and len(name) > 4]
        name = []
        for fxn in fxnindex:
            fn = getattr(self, 'fxn_' + str(fxn))
            doc = fn.__doc__
            doc = doc.split('\n')
            doc = doc[0].split(':')
            cat.append(doc[0].strip())
            name.append(doc[1].strip())
        titles = list(set(cat))
        for t in titles:
            toreturn += (t + ':\n')
            for i in range(len(cat)):
                if cat[i] == t:
                    toreturn += ('\t' + name[i] +
                                 spacer[:len(spacer)-(len(name[i])+len(fxnindex[i]))] + fxnindex[i] + '\n')
        return toreturn

    def applyfxns(self):
        firstindex = 1
        lastindex = 1
        fxnindicies = self.funcindex
        fxns = self.functions
        for f in self.funcindex:
            fn = getattr(self, 'fxn_' + str(f))
            fn()
        if self.inst.data.plot_limits.is_active:
            firstindex = min(self.inst.data.plot_limits.buffer_range.get())
            lastindex = max(self.inst.data.plot_limits.buffer_range.get())
        else:
            firstindex = 1
            lastindex = self.inst.data.matrix.length() + 1
        maxindex = 0
        for k in range(len(fxns)):
            fxnsplit = fxns[k].split("P[")
            for f in range(0, len(fxnsplit) - 1, 1):
                fxnsplit[f] += "P["
                tempstr = fxnsplit[f + 1].split(']')
                fxnsplit[f + 1] = str(int(tempstr[0]) + maxindex) + ']' + tempstr[1]
            maxindex = int(tempstr[0]) + maxindex + 1
            fxns[k] = ''.join(fxnsplit)
        tempfxn = ''
        for j in range(len(fxns)):
            yval, xval = fxns[j].split('=')
            tempfxn += xval + '+'
        try:
            for i in range(firstindex, lastindex):
                self.inst.data.matrix.buffer(i).fit.function_index.set(fxnindicies)
                self.inst.data.matrix.buffer(i).fit.function.set(tempfxn[:-1])
        except:
            return False
        return True

    def dofit(self, *args):
        fitparams = datafit(self.inst)
        args = [int(val) if val.isdigit() else val.lower() for val in args]
        method = "Leastsq"
        debug = True if "-debug" in args else False
        group = abs(args[args.index('-group') + 1]) if '-group' in args and args.index('-group') < len(args) and is_integer(args[args.index('-group') + 1]) else 1 if '-ind' in args else self.inst.data.matrix.length()
        cpu = abs(args[args.index('-cpu') + 1]) if '-cpu' in args and args.index('-cpu') < len(args) and is_integer(args[args.index('-cpu') + 1]) else 1
        ind_fit = True if '-ind' in args else False
        group = 1 if ind_fit else group
        silent = True if "-silent" in args else False
        iter_cb = debug_fitting if debug else None
        max_iter = int(args[0]) if isinstance(args[0], int) else 2000
        bmax = self.inst.data.matrix.length() #if not self.inst.data.plot_limits.is_active else max(self.inst.data.plot_limits.buffer_range.get())
        bmin = 1 if not self.inst.data.plot_limits.is_active else min(self.inst.data.plot_limits.buffer_range.get())

        #construct list of lists for X, Y, Params
        X_vec = []
        Y_vec = []
        Z_vec = []
        P_vec = []
        IR_X_vec = []
        IR_Y_vec = []
        IR_Z_vec = []
        FXN_vec = []
        WEIGHTS_vec = []
        FXN_NUM_vec = []
        PARAM_ID_vec = []
        Y_matrix = []
        for i in range(bmin, bmax+1, group):
            parameters = Parameters()
            x_group = []
            y_group = []
            z_group = []
            ir_x_group = []
            ir_y_group = []
            ir_z_group = []
            fxn_group = []
            weights_group = []
            fxn_num_group = []
            for j in range(group):
                k=i+j
                fitparams.clear()
                fitparams.update(self.inst.data.matrix.buffer(k).fit.function_index.get())
                p_init= self.inst.data.matrix.buffer(k).fit.parameter.get()
                if len(p_init) == 0:
                    return "Invalid Parameters!  Try Function: ap ."

                for m in range(len(p_init)):
                    try:
                        parameters.add(name=fitparams.paramid[m] + "_{}_{}".format(m+1, k),
                                       value=float(self.inst.data.matrix.buffer(k).fit.parameter.get()[m]),
                                       min=float(min(fitparams.parambounds[m])), max=float(max(fitparams.parambounds[m])),
                                       expr=self.inst.data.matrix.buffer(k).fit.link.get()[m],
                                       vary=self.inst.data.matrix.buffer(k).fit.free.get()[m])
                    except (NameError, ValueError) as e:
                        if isinstance(e, NameError):
                            return "Parameter Linking Scheme is Invalid!"
                        elif isinstance(e, ValueError):
                            return "Parameters Return Invalid Results!!"

                x_group.append(self.inst.data.matrix.buffer(k).data.x.get())
                y_group.append(self.inst.data.matrix.buffer(k).data.y.get())
                z_group.append(self.inst.data.matrix.buffer(k).data.z.get())
                ir_x_group.append(self.inst.data.matrix.buffer(k).instrument_response.x.get())
                ir_y_group.append(self.inst.data.matrix.buffer(k).instrument_response.y.get())
                ir_z_group.append(self.inst.data.matrix.buffer(k).instrument_response.z.get())
                weights_group.append(self.inst.data.matrix.buffer(k).data.ye.get())
                fxn_group.append(self.inst.data.matrix.buffer(k).fit.function.get())
                temp_df = datafit(self.inst)
                temp_df.update(self.inst.data.matrix.buffer(k).fit.function_index.get())
                fxn_num_group.append(self.inst.data.matrix.buffer(k).fit.function_index.get())
            X_vec.append(x_group)
            Y_vec.append(y_group)
            Z_vec.append(z_group)
            P_vec.append(parameters)
            IR_X_vec.append(ir_x_group)
            IR_Y_vec.append(ir_y_group)
            IR_Z_vec.append(ir_z_group)
            WEIGHTS_vec.append(weights_group)
            FXN_vec.append(fxn_group)
            FXN_NUM_vec.append(fxn_num_group)

        try:
            for vec in Y_vec:
                Y_matrix.append(np.array(vec))
                assert Y_matrix[-1].shape == (len(Y_matrix[-1]), max([len(y) for y in vec]))
        except AssertionError:
            return "All Buffers Must Be the Same Number of Points!  Try Commands: pl or res or tri"

        param_dict = {'x_vec': X_vec, 'y_vec': Y_vec, 'z_vec': Z_vec, 'p_vec':P_vec, 'y_matrix': Y_matrix,
                      'ir_x_vec': IR_X_vec, 'ir_y_vec': IR_Y_vec, 'ir_z_vec': IR_Z_vec, 'silent': silent,
                      'weights_vec': WEIGHTS_vec, 'fxn_vec': FXN_vec, 'fxn_num_vec': FXN_NUM_vec,
                      'param_id_vec': PARAM_ID_vec,'method': method, 'debug': debug, 'group': group, 'cpu': cpu,
                      'ind_fit': ind_fit, 'iter_cb': iter_cb, 'max_iter': max_iter, 'index': i}

        result = multi_fit(param_dict)
        result = self.split_result_by_group(result, group)

        print('Saving parameters to matrix...')
        self.saveparams(result, group, silent)

        print('Calculating fit stats and generating model traces...')
        for i in range(bmin, bmax+1):
            try:
                self.calcfitstat(i)
                self.generatemodel(i, numpts=300)
            except Exception as e:
                print(str(e))

            if debug:
                report_fit(result[i-bmin].params)

            if not silent:
                print(f'---Buffer {i} fit statistics---')
                # print number of function efvals
                print('\n#Function efvals:\t', result[i-bmin].nfev)
                #print number of data points
                print('#Data pts:\t', result[i-bmin].ndata)
                #print number of variables
                print('#Variables:\t', result[i-bmin].nvarys)
                # chi-sqr
                print('\nResult Chi Sq:\t', result[i-bmin].chisqr)
                # reduce chi-sqr
                print('Result Reduced Chi Sq:\t', result[i-bmin].redchi)
                # Akaike info crit
                print('Result Akaike:\t', result[i-bmin].aic)
                # Bayesian info crit
                print('Result Bayesian:\t', result[i-bmin].bic)
                # message
                print('Fit Details:\t', result[i-bmin].message)
                print('-----------------------------')
        return "\nData Fitting Complete!"

    def split_result_by_group(self, result, group):
        '''Make result vector equivilent size to buffer matrix by splitting results by group'''
        if group == 1:
            return result
        result_to_return = []
        for r in result:
            for i in range(group):
                if r == None:
                    result_to_return.append(None)
                    continue
                result_to_return.append(copy.copy(r))
        return result_to_return

    def generatemodel(self, i, numpts=300):
        X = self.inst.data.matrix.buffer(i).data.x.get()
        Y = self.inst.data.matrix.buffer(i).data.y.get()
        Z = self.inst.data.matrix.buffer(i).data.z.get()
        IRX = self.inst.data.matrix.buffer(i).instrument_response.x.get()
        IRY = self.inst.data.matrix.buffer(i).instrument_response.y.get()
        IRZ = self.inst.data.matrix.buffer(i).instrument_response.z.get()

        min_x = np.min(X)
        max_x = np.max(X)
        stepsize = (max_x - min_x) / (numpts)
        modelX = [((stepsize * k) + min_x) for k in range(0, numpts, 1)]

        # add some points in-case data is logarithmically sampled 11/08/2019
        inc_x = list(zip(['inc'] * len(modelX), modelX))
        data_x = list(zip(['data'] * len(X), X))
        inc_x.extend(data_x)
        all_x = sorted(inc_x, key=lambda tup: tup[1])
        for j in reversed(range(1, len(all_x) - 1, 1)):
            if all_x[j][0] == 'data' and all_x[j - 1][0] == 'inc' and all_x[j + 1][0] == 'inc':
                del all_x[j]
        _, X = map(list, zip(*all_x))
        # end add points

        fxn = self.inst.data.matrix.buffer(i).fit.function.get()
        P = self.inst.data.matrix.buffer(i).fit.parameter.get()
        X = np.array(X)
        R = [0] * len(X)

        if fxn is not False and fxn[:2].upper() == "Y=":
            fxn = fxn[2:]
        # execute custom script
        if self.pyscript:
            exec(self.pyscript)
        else:
            R = eval(str(fxn))

        self.inst.data.matrix.buffer(i).model.x.set(X)
        self.inst.data.matrix.buffer(i).model.y.set(R)
        return True

    def calcfitstat(self, i):
        rawy = self.inst.data.matrix.buffer(i).data.y.get()
        resid_y = self.inst.data.matrix.buffer(i).residuals.y.get()
        rsq = np.sum(np.power(resid_y, 2))
        avgerror = np.sum(np.power(rawy - np.average(rawy), 2))
        avgerror = 1E-6 if avgerror == 0 else avgerror
        self.inst.data.matrix.buffer(i).fit.rsq.set(1 - (rsq / avgerror))
        SD = np.average(np.abs(resid_y))
        if SD == 0:
            SD = 0.001
        self.inst.data.matrix.buffer(i).fit.chisq.set(np.sum(((resid_y) ** 2) / SD))
        return

    def saveparams(self, result, group, silent):
        bmin = 1
        if not self.inst.data.plot_limits.is_active:
            bmax = self.inst.data.matrix.length()
        else:
            bmin = self.inst.data.plot_limits.buffer_range.min()
            bmax = self.inst.data.plot_limits.buffer_range.max()

        if not silent:
            print('--------Fit Parameters---------')

        grp_cnt = -1
        for i in range(bmin, bmax+1, 1):
            grp_cnt = grp_cnt + 1 if grp_cnt < group-1 else 0
            i_idx = i-bmin
            self.clear()
            self.update(self.inst.data.matrix.buffer(i).fit.function_index.get())
            self.inst.data.matrix.buffer(i).fit.parameter_error.set([0] * len(self.inst.data.matrix.buffer(i).fit.parameter.get()))
            parameters = self.inst.data.matrix.buffer(i).fit.parameter.get()

            # if fit failed fill in data
            if result[i_idx].aborted:
                x = self.inst.data.matrix.buffer(i).data.x.get()
                y = self.inst.data.matrix.buffer(i).data.y.get()
                z = self.inst.data.matrix.buffer(i).data.z.get()
                self.inst.data.matrix.buffer(i).fit.fit_failed = True
                self.inst.data.matrix.buffer(i).fit.fit_failed_reason.set(str(e))
                self.inst.data.matrix.buffer(i).fit.parameter.set([-1] * len(parameters))
                self.inst.data.matrix.buffer(i).fit.parameter_error.set([-1] * len(parameters))
                self.inst.data.matrix.buffer(i).model.x.set([x[0], x[-1]] if len(x) > 1 else [])
                self.inst.data.matrix.buffer(i).model.y.set([y[0], y[-1]] if len(y) > 1 else [])
                self.inst.data.matrix.buffer(i).model.z.set([z[0], z[-1]] if len(z) > 1 else [])
                self.inst.data.matrix.buffer(i).residuals.y.set([y[0], y[-1]] if len(y) > 1 else [])
                self.inst.data.matrix.buffer(i).residuals.x.set(x)
                if not silent:
                    print(f'Buffer {i}: Fit Failed!\n-----------------------------')
                continue

            # Else, add fit  values to matrix
            resid= np.array_split(result[i_idx].residual, group)
            # weights used are typically Y error vector
            weights = self.inst.data.matrix.buffer(i).data.ye.get()
            # Residuals are squared in fit minimization and multiplied by the weight vector.  Here we reverse those calculations
            try:
                unweighted_resid = np.power(resid[grp_cnt], 0.5) if len(weights) <= 1 else np.power(resid[grp_cnt], 0.5) / weights
            except:
                weights = np.nan_to_num(weights, nan=1.0)
                unweighted_resid = np.power(resid[grp_cnt], 0.5) if len(weights) <= 1 else np.power(resid[grp_cnt], 0.5) / weights
            self.inst.data.matrix.buffer(i).residuals.y.set(unweighted_resid)
            self.inst.data.matrix.buffer(i).residuals.x.set(self.inst.data.matrix.buffer(i).data.x.get())
            for j_idx in range(len(self.paramid)):
                j = j_idx+1
                param = result[i_idx].params[self.paramid[j_idx] + f"_{j}_{i}"].value
                error = result[i_idx].params[self.paramid[j_idx] + f"_{j}_{i}"].stderr
                param_list = self.inst.data.matrix.buffer(i).fit.parameter.get()
                param_list[j_idx] = param
                self.inst.data.matrix.buffer(i).fit.parameter.set(param_list)
                error_list = self.inst.data.matrix.buffer(i).fit.parameter_error.get()
                error_list[j_idx] = error
                self.inst.data.matrix.buffer(i).fit.parameter_error.set(error_list)
                if not silent:
                    print(f'Buffer {i}: Parameter: {self.paramid[j_idx]} = {param} +/- {error}')

            if not silent:
                print('-----------------------------')
        return True


def debug_fitting(self, params, nfev, resid, *args, **kwargs):
    """Function to be called after each iteration of the minimization method
    used by lmfit. Should reveal information about how parameter values are
    changing after every iteration in the fitting routine. See
    lmfit.Minimizer.__residual for more information."""
    print("Iteration {0}".format(nfev) + "\tRsq: " + str(np.sum(np.power(resid, 2))))


def is_integer(input):
    try:
        num = int(input)
    except ValueError:
        return False
    return True

def eval_objective(params, y_matrix, idx, param_dict):  # calculate residuals to determine if the parameters are improving the fit
    '''param_dict = param_dict = {'x_vec': X_vec, 'y_vec': Y_vec, 'z_vec': Z_vec, 'p_vec':P_vec, 'y_matrix': Y_matrix,
                          'ir_x_vec': IR_X_vec, 'ir_y_vec': IR_Y_vec, 'ir_z_vec': IR_Z_vec,
                          'weights_vec': WEIGHTS_vec, 'fxn_vec': FXN_vec, 'fxn_num_vec': FXN_NUM_vec,
                          'param_id_vec': PARAM_ID_vec,'method': method, 'debug': debug, 'group': group, 'cpu': cpu,
                          'ind_fit': ind_fit, 'iter_cb': iter_cb, 'max_iter': max_iter}'''
    resid = 0.0 * y_matrix[:]
    group = param_dict['group']
    x_vec = param_dict['x_vec'][idx]
    y_vec = param_dict['y_vec'][idx]
    z_vec = param_dict['z_vec'][idx]
    p_vec = param_dict['p_vec'][idx]
    ir_x_vec = param_dict['ir_x_vec'][idx]
    ir_y_vec = param_dict['ir_y_vec'][idx]
    ir_z_vec = param_dict['ir_z_vec'][idx]
    fxn_vec = param_dict['fxn_vec'][idx]
    weights_vec = param_dict['weights_vec'][idx]
    fxn_num_vec = param_dict['fxn_num_vec'][idx]
    pyscript_vec = []
    param_id_vec = []
    for fxn_num in fxn_num_vec:
        temp_df = datafit(fxn_num)
        temp_df.update(fxn_num)
        pyscript_vec.append(temp_df.pyscript)
        param_id_vec.append(temp_df.paramid)
    for i in range(len(x_vec)):
        P = []
        X = x_vec[i]
        Y = y_vec[i]
        Z = z_vec[i]
        IRX = ir_x_vec[i]
        IRY = ir_y_vec[i]
        IRZ = ir_z_vec[i]
        weights = weights_vec[i]

        # Fit the data
        fxn = fxn_vec[i]
        R = [0] * len(X)
        for j in range(len(param_id_vec[i])):
            pname = param_id_vec[i][j].replace('-', '') + "_{}_{}".format(j + 1, i+(idx*group)+1)
            P.append(params[pname].value)
        if fxn is not False and fxn[:2].upper() == "Y=":
            fxn = fxn[2:]
        # execute custom script
        if pyscript_vec[i]:
            exec(pyscript_vec[i])
        else:
            R = eval(str(fxn))

        p_vec = P
        R = np.array(R)

        resid_line = (Y - R) if len(weights) <= 1 else (Y - R) * weights
        resid[i, :] = np.power(resid_line, 2)
    # now flatten this to a 1D array, as minimize() needs
    return resid.flatten()

def optimizer(param_dict, idx_list):
    result = []
    for idx in idx_list:
        print(f'Evaluating #{idx+1} from total pool of: {len(param_dict["y_vec"])}')
        parameters = param_dict['p_vec'][idx]
        iter_cb = param_dict['iter_cb']
        max_iter = iter_cb = param_dict['max_iter']
        method = iter_cb = param_dict['method']
        argsx = (param_dict['y_matrix'][idx], idx, param_dict)
        result.append(minimize(eval_objective, parameters, args=(param_dict['y_matrix'][idx], idx, param_dict),
                 iter_cb=iter_cb, method=method, maxfev=max_iter, nan_policy='omit'))
    return result

def multi_fit(param_dict):
    '''param_dict = {'x_vec': X_vec, 'y_vec': Y_vec, 'z_vec': Z_vec, 'p_vec':P_vec, 'y_matrix': Y_matrix,
                          'ir_x_vec': IR_X_vec, 'ir_y_vec': IR_Y_vec, 'ir_z_vec': IR_Z_vec,
                          'weights_vec': WEIGHTS_vec, 'fxn_vec': FXN_vec, 'fxn_num_vec': FXN_NUM_vec,
                          'param_id_vec': PARAM_ID_vec,'method': method, 'debug': debug, 'group': group, 'cpu': cpu,
                          'ind_fit': ind_fit, 'iter_cb': iter_cb, 'max_iter': max_iter}'''
    idx_list = [*range(len(param_dict['x_vec']))]
    func = partial(optimizer, param_dict)
    cpu_num = int(min(mp.cpu_count()-1, param_dict['cpu'], len(idx_list)))
    results = []
    if cpu_num > 1:
        group = param_dict['group']
        seg_size = int(np.floor(np.floor(len(idx_list) / group) / cpu_num) * group)
        seg_idx_list = [idx_list[i*seg_size:(i+1)*seg_size] if ((i+2)*seg_size) <= len(idx_list) else idx_list[i*seg_size:] for i in range(cpu_num)]
        print(f'Generating Workers (cores:{cpu_num})...')
        proc_pool = mp.Pool(cpu_num)
        print('Fitting data in multiprocessing mode...')
        results = proc_pool.map_async(func, seg_idx_list)
        proc_pool.close()
        proc_pool.join()
        results = list(itertools.chain.from_iterable(results.get()))
    else: # Avoid multiprocessing overhead
        print(f'Fitting data in single core mode...')
        results = [func([idx])[0] for idx in idx_list]
    return results
