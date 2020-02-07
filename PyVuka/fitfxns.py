import numpy as np
from lmfit import minimize, Parameters, report_fit
from PyVuka import data_obj as data

#constants
gas_const_kcal = 1.9872036

class datafit(object):
    """extend with fxn_index  methods. index must be an integer.

    Docstring text (first line) is parsed for building function table so docstring format must be conserved

        Ex1: Generic Function: Constant (Additive)
            \n
        Ex2: Generic Function: Constant (Additive)\n

        where "Generic Function" is the category of the function and "Constant (additive)" is the function name"

    Remaining doctstring format should be conserved as it is the description used by the 'fun info' command.
        """

    def __init__(self, info_commands=['info', '?']):
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
        \nPubMed ID: [Not defined]
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
        #delta_g_at_concentration = (P[0]+P[1]*X)
        #equilibrium_constant = (np.exp(-1*(P[0] + P[1] * X)/(1.9872036*P[6])))
        #unfolded_fraction = ((np.exp(-1*(P[0] + P[1] * X)/(1.9872036*P[6]))) / (1 + (np.exp(-1*(P[0] + P[1] * X)/(1.9872036*P[6])))))
        #native_y_at_concentration = P[2] + P[4] * X
        #unfolded_y_at_concentration = P[3] + P[5] * X
        #return unfolded_fraction*unfolded_y_at_concentration + (1-unfolded_fraction)*native_y_at_concentration

        self.paramid.extend(["dG", "m", "Cn", "Cu", "Mn", "Mu", "T"])
        self.parambounds.extend([[-np.inf, np.inf], [-np.inf, np.inf], [-np.inf, np.inf], [-np.inf, np.inf],
                                 [-np.inf, np.inf], [-np.inf, np.inf], [-np.inf, np.inf]])
        self.paramdefaults.extend([5, 1.8, 0, 25000, 1000, 2, 298.15])
        self.functions.extend(["Y=((np.exp(-1*(P[0] + P[1] * X)/(1.9872036*P[6]))) / (1 + (np.exp(-1*(P[0] + P[1] * X)/(1.9872036*P[6])))))*(P[3] + P[5] * X) + (1-((np.exp(-1*(P[0] + P[1] * X)/(1.9872036*P[6]))) / (1 + (np.exp(-1*(P[0] + P[1] * X)/(1.9872036*P[6]))))))*(P[2] + P[4] * X)"])
        self.pyscriptonly = True
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
fitparams.pyscriptonly = True
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
fitparams.pyscriptonly = True
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
        if data.plot_limits.is_active:
            firstindex = min(data.plot_limits.buffer_range.get())
            lastindex = max(data.plot_limits.buffer_range.get())
        else:
            firstindex = 1
            lastindex = data.matrix.length() + 1
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
                data.matrix.buffer(i).fit.function_index.set(fxnindicies)
                data.matrix.buffer(i).fit.function.set(tempfxn[:-1])
        except:
            return False
        return True


def dofit(*args):
    ymatrix = []
    parameters = Parameters()
    fitparams = datafit()
    bmax = 1
    bmin = 1
    p_best = []
    longest = 0
    debug = True
    method = "Leastsq"
    args = [int(val) if val.isdigit() else val.lower() for val in args]

    if "-debug" in args:
        iter_cb = debug_fitting
    else:
        iter_cb = None
    if not data.plot_limits.is_active:
        bmax = data.matrix.length()
    else:
        bmin = min(data.plot_limits.buffer_range.get())
        bmax = max(data.plot_limits.buffer_range.get())
    for i in range(bmin, bmax+1):
        fitparams.update(data.matrix.buffer(i).fit.function_index.get())
        p_init = data.matrix.buffer(i).fit.parameter.get()

        max_iter = 2000 * (len(p_init) + 1)
        # if int passed as arg, use as maximum iteration number, else default to lib default
        new_max = [val for val in args if isinstance(val, int)]
        if new_max:
            max_iter = new_max[0]

        if len(p_init) == 0:
            return "Invalid Parameters!  Try Function: ap ."
        ymatrix.append(data.matrix.buffer(i).data.y.get())
        for j in range(len(data.matrix.buffer(i).fit.parameter.get())):
            try:
                parameters.add(name=fitparams.paramid[j] + "_{}_{}".format(j+1, i),
                               value=float(data.matrix.buffer(i).fit.parameter.get()[j]),
                               min=float(min(fitparams.parambounds[j])), max=float(max(fitparams.parambounds[j])),
                               expr=data.matrix.buffer(i).fit.link.get()[j],
                               vary=data.matrix.buffer(i).fit.free.get()[j])
            except (NameError, ValueError) as e:
                if isinstance(e, NameError):
                    return "Parameter Linking Scheme is Invalid!"
                elif isinstance(e, ValueError):
                    return "Parameters Return Invalid Results!!"
    ymatrix = np.array(ymatrix)
    longest = max([len(y) for y in ymatrix])
    try:
        assert ymatrix.shape == (bmax-bmin+1, longest)
    except AssertionError:
        return "All Buffers Must Be the Same Number of Points!  Try Commands: pl or res or tri"
    try:
        result = minimize(objective, parameters, args=(ymatrix, bmin, bmax),
                  iter_cb=iter_cb, method=method, maxfev=max_iter, nan_policy='omit')
    except Exception as e:
        for i in range(bmin, bmax + 1):
            x = data.matrix.buffer(i).data.x.get()
            y = data.matrix.buffer(i).data.y.get()
            z = data.matrix.buffer(i).data.z.get()
            data.matrix.buffer(i).fit.fit_failed = True
            data.matrix.buffer(i).fit.fit_failed_reason.set(str(e))
            data.matrix.buffer(i).fit.parameter.set([-1] * len(parameters))
            data.matrix.buffer(i).fit.parameter_error.set([-1] * len(parameters))
            data.matrix.buffer(i).model.x.set([x[0], x[-1]] if len(x) > 1 else [])
            data.matrix.buffer(i).model.y.set([y[0], y[-1]] if len(y) > 1 else [])
            data.matrix.buffer(i).model.z.set([z[0], z[-1]] if len(z) > 1 else [])
        return f"\nFit Failed!\n\t{str(e)}"

    saveparams(result)
    report_fit(result.params)

    # calculate model
    for i in range(bmin, bmax + 1):
        generatemodel(i, numpts=300)

    # print number of function efvals
    print('\n#Function efvals:\t', result.nfev)
    #print number of data points
    print('#Data pts:\t', result.ndata)
    #print number of variables
    print('#Variables:\t', result.nvarys)
    # chi-sqr
    print('\nResult Chi Sq:\t', result.chisqr)
    # reduce chi-sqr
    print('Result Reduced Chi Sq:\t', result.redchi)
    # Akaike info crit
    print('Result Akaike:\t', result.aic)
    # Bayesian info crit
    print('Result Bayesian:\t', result.bic)
    return "\nData Fitting Complete!"


def debug_fitting(params, nfev, resid, *args, **kwargs):
    """Function to be called after each iteration of the minimization method
    used by lmfit. Should reveal information about how parameter values are
    changing after every iteration in the fitting routine. See
    lmfit.Minimizer.__residual for more information."""
    print("Iteration {0}".format(nfev) + "\tRsq: " + str(np.sum(np.power(resid, 2))))


def objective(params, ymatrix, bmin, bmax):  # calculate residuals to determine if the parameters are improving the fit
    resid = 0.0 * ymatrix[:]
    for i in range(bmin, bmax + 1):
        P = []
        fitparams = datafit()
        fitparams.update(data.matrix.buffer(i).fit.function_index.get())
        X = data.matrix.buffer(i).data.x.get()
        Y = data.matrix.buffer(i).data.y.get()
        Z = data.matrix.buffer(i).data.z.get()
        IRX = data.matrix.buffer(i).instrument_response.x.get()
        IRY = data.matrix.buffer(i).instrument_response.y.get()
        IRZ = data.matrix.buffer(i).instrument_response.z.get()
        weights = data.matrix.buffer(i).data.ye.get()

        # Fit the data
        fxn = data.matrix.buffer(i).fit.function.get()
        R = [0] * len(X)
        for j in range(len(data.matrix.buffer(i).fit.parameter.get())):
            pname = fitparams.paramid[j].replace('-', '') + "_{}_{}".format(j+1, i)
            P.append(params[pname].value)
        if fxn is not False and fxn[:2].upper() == "Y=":
            fxn = fxn[2:]
        # execute custom script
        if fitparams.pyscript:
            exec(fitparams.pyscript)
        else:
            R = eval(str(fxn))

        data.matrix.buffer(i).fit.parameter.set(P)
        R = np.array(R)

        data.matrix.buffer(i).residuals.y.set(Y - R)
        data.matrix.buffer(i).residuals.x.set(X)
        resid_line = data.matrix.buffer(i).residuals.y.get()
        if len(weights) > 1:
            # apply weights
            resid_line = (Y - R) * weights
        resid[i - bmin, :] = np.power(resid_line, 2)
        calcfitstat(i)
    # now flatten this to a 1D array, as minimize() needs
    return resid.flatten()


def generatemodel(i, numpts=300):
    fitparams = datafit()
    fitparams.update(data.matrix.buffer(i).fit.function_index.get())
    X = data.matrix.buffer(i).data.x.get()
    Y = data.matrix.buffer(i).data.y.get()
    Z = data.matrix.buffer(i).data.z.get()
    IRX = data.matrix.buffer(i).instrument_response.x.get()
    IRY = data.matrix.buffer(i).instrument_response.y.get()
    IRZ = data.matrix.buffer(i).instrument_response.z.get()

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

    fxn = data.matrix.buffer(i).fit.function.get()
    P = data.matrix.buffer(i).fit.parameter.get()
    X = np.array(X)
    R = [0] * len(X)

    if fxn is not False and fxn[:2].upper() == "Y=":
        fxn = fxn[2:]
    # execute custom script
    if fitparams.pyscript:
        exec(fitparams.pyscript)
    else:
        R = eval(str(fxn))

    data.matrix.buffer(i).model.x.set(X)
    data.matrix.buffer(i).model.y.set(R)
    return True


def calcfitstat(i):
    rawy = data.matrix.buffer(i).data.y.get()
    resid_y = data.matrix.buffer(i).residuals.y.get()
    rsq = np.sum(np.power(resid_y, 2))
    avgerror = np.sum(np.power(rawy - np.average(rawy), 2))
    data.matrix.buffer(i).fit.rsq.set(1 - (rsq / avgerror))
    SD = np.average(np.abs(resid_y))
    if SD == 0:
        SD = 0.001
    data.matrix.buffer(i).fit.chisq.set(np.sum(((resid_y) ** 2) / SD))
    return


def saveparams(result):
    parameters = Parameters()
    fitparams = datafit()
    bmin = 1
    if not data.plot_limits.is_active:
        bmax = data.matrix.length()
    else:
        bmin = data.plot_limits.buffer_range.min()
        bmax = data.plot_limits.buffer_range.max()
    for i in range(bmin, bmax+1):
        fitparams.clear()
        fitparams.update(data.matrix.buffer(i).fit.function_index.get())
        data.matrix.buffer(i).fit.parameter_error.set([0] * len(data.matrix.buffer(i).fit.parameter.get()))

        for j in range(len(fitparams.paramid)):
            param = result.params[fitparams.paramid[j] + f"_{j+1}_{i}"].value
            error = result.params[fitparams.paramid[j] + f"_{j+1}_{i}"].stderr
            temp = data.matrix.buffer(i).fit.parameter.get()
            temp[j] = param
            data.matrix.buffer(i).fit.parameter.set(temp)
            temp = data.matrix.buffer(i).fit.parameter_error.get()
            temp[j] = error
            data.matrix.buffer(i).fit.parameter_error.set(temp)
            print("Buffer " + str(i) + " Parameter " + str(j+1) + " = " + str(param) + " +/- " + str(error))

    for i in range(bmin, bmax+1):
        for j in range(len(data.matrix.buffer(i).fit.parameter.get())):
            print(f"Buffer {i} Parameter {j+1} = {str(data.matrix.buffer(i).fit.parameter.get()[j])}" +
                  f" +/- {str(data.matrix.buffer(i).fit.parameter_error.get()[j])}")
    return True
