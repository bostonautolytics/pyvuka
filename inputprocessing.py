import os

class InputParser(object):

    def __init__(self, quit_command=['q', 'quit']):
        self._quit_cmd = quit_command
        self.prompt = []
        self.defaultinput = []
        self.previousvals = []
        self.inputbounds = []
        self.userinput = []
        self.cmdflags = []
        self.modifiers = []

    def __call__(self, inputarray):
        for val in inputarray:
            if val.lower() in self._quit_cmd:
                break
            isfloat = self.__is_float(val)
            ispath = self.__is_path(val)
            if ('-' not in val and not isfloat) or ispath:
                self.modifiers.append(val)
            elif '-' in val[0] and not isfloat:
                self.cmdflags.append(val.lower())
            else:
                try:
                    self.userinput.append(float(val))
                except ValueError:
                    print("Invalid Command Parameters!")
                    return False
        return True

    def clear(self):
        self.prompt = []
        self.defaultinput = []
        self.previousvals = []
        self.inputbounds = []
        self.userinput = []
        self.cmdflags = []
        self.modifiers = []
        return True

    def getparams(self):
        returnvals = [None] * len(self.prompt)
        if len(self.userinput) > len(returnvals):
            self.userinput[:len(returnvals)-1]
        for i in range(len(self.userinput)):
            if i >= len(returnvals) or i >= len(self.userinput):
                break
            returnvals[i] = self.userinput[i]
        for j in range(len(self.prompt)):
            inval = ''
            if returnvals[j] is not None:
                if float(returnvals[j]) < float(self.inputbounds[j][0]):
                    returnvals[j] = float(self.inputbounds[j][0])
                elif float(returnvals[j]) > float(self.inputbounds[j][1]):
                    returnvals[j] = float(self.inputbounds[j][1])
                if len(self.previousvals) == len(self.defaultinput) and len(self.defaultinput) > 0:
                    self.defaultinput = self.previousvals[:]
                    print(self.prompt[j] + " [" + str(self.defaultinput[j]) + "]: " + str(returnvals[j]))
            else:
                numeric = False
                while not numeric:
                    if len(self.previousvals) == len(self.defaultinput) and len(self.defaultinput) > 0:
                        self.defaultinput = self.previousvals[:]
                    inval = input(self.prompt[j] + " [" + str(self.defaultinput[j]) + "]: ")
                    if inval == '':
                        inval = self.defaultinput[j]
                    elif inval in self._quit_cmd:
                        print("Operation Aborted!")
                        return False
                    try:
                        temp = float(inval)
                        numeric = True
                    except ValueError:
                        numeric = False
                        continue
                    if float(inval) < float(self.inputbounds[j][0]):
                        returnvals[j] = self.inputbounds[j][0]
                    elif float(inval) > float(self.inputbounds[j][1]):
                        returnvals[j] = self.inputbounds[j][1]
                    else:
                        returnvals[j] = inval
        self.userinput = returnvals
        return returnvals

    def __is_float(self, input):
        try:
            num = float(input)
        except ValueError:
            return False
        return True

    def __is_int(self, input):
        try:
            num = int(input)
        except ValueError:
            return False
        return True

    def __is_path(self, input):
        path_check = [os.path.exists(input), os.access(os.path.dirname(input), os.W_OK)]
        return True if True in path_check else False
