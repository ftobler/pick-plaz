try:
    from serial import Serial
except:
    print("Could not import Serial. However, usage with mock is still possible.")


def print(*args):
    pass

class Robot:
    con = None
    __full = False
    __empty = False
    __sync = False

    def __init__(self, comport=None):
        if comport != None:
            #regular constructor
            self.con = Serial(comport, baudrate=115200, timeout=0.1)
        else:
            #mock constructor
            def dummy_fcn(*args):
                pass
            self.__send_commands = dummy_fcn
            self.__receive_answer = dummy_fcn
            self.done = dummy_fcn
            self.flush = dummy_fcn


    def home(self, axis=None):
        """
        Sends a HOME command

        axis : str, axes to home e.g. axis="xy" homes the x and y axis

        Function blocks execution until the command is sent.
        Returns itself
        """
        if axis is None:
            self.__send_commands(["G28"])
        else:
            axes = " ".join(f"{a}=0" for a in ["x", "y", "z"] if a in axis)
            self.__send_commands([f"G28 {axes}"])

        return self

    def done(self):
        """
        Sends a SYNC and blocks until controller has executed it.

        Function blocks execution until the command is sent.
        Returns itself
        """
        self.__sync = False
        self.__send_commands(["M1000"])
        while not self.__sync:
            self.__receive_answer()
        return self

    def flush(self):
        """
        Blocks until the command queue on controller side is empty.

        Function blocks execution until the command is sent.
        Returns itself
        """
        while not self.__empty:
            self.__receive_answer()
        return self

    def drive(self, x=None, y=None, z=None, e=None, a=None, b=None, c=None, f=None, o=None):
        """
        drives to a new Location. All Axies can be driven at the same time. Command finishes when the slowest Motor has reached its target.

        setting F overrides the max Feedrate

          * X = X Axies
          * Y = Y Axies (2 Motors)
          * Z = Head Height (Paste head and Pick head are on same axies but mechanically linked and inverted)
          * E = Pick rotation (degrees)
          * A = Paste Motor
          * B = reserved
          * C = reserved
          * O = target completeness (default 1.0)

        Function blocks execution until the command is sent.
        Returns itself
        """
        cmd = [
            "G0"
        ]
        if x != None:
            cmd.append(" X%f" % x)
        if y != None:
            cmd.append(" Y%f" % y)
        if z != None:
            cmd.append(" Z%f" % z)
        if e != None:
            cmd.append(" E%f" % e)
        if a != None:
            cmd.append(" A%f" % a)
        if b != None:
            cmd.append(" B%f" % b)
        if c != None:
            cmd.append(" C%f" % c)
        if f != None:
            cmd.append(" F%f" % f)
        if o != None:
            cmd.append(" O%f" % o)
        self.__send_commands(["".join(cmd)])
        return self

    def position(self, x=None, y=None, z=None, e=None, a=None, b=None, c=None):
        """
        Assumes this as the actual position without driving there.

        Axies descripton see drive()

        Function blocks execution until the command is sent.
        Returns itself
        """
        cmd = [
            "G0"
        ]
        if x != None:
            cmd.append(" X%f" % x)
        if y != None:
            cmd.append(" Y%f" % y)
        if z != None:
            cmd.append(" Z%f" % z)
        if e != None:
            cmd.append(" E%f" % e)
        if a != None:
            cmd.append(" A%f" % a)
        if b != None:
            cmd.append(" B%f" % b)
        if c != None:
            cmd.append(" C%f" % c)
        self.__send_commands(["".join(cmd)])
        return self

    def acceleration(self, x=None, y=None, z=None, e=None, a=None, b=None, c=None):
        """
        set the axies acceleration

        Axies descripton see drive()

        Function blocks execution until the command is sent.
        Returns itself
        """
        cmd = [
            "GM201"
        ]
        if x != None:
            cmd.append(" X%f" % x)
        if y != None:
            cmd.append(" Y%f" % y)
        if z != None:
            cmd.append(" Z%f" % z)
        if e != None:
            cmd.append(" E%f" % e)
        if a != None:
            cmd.append(" A%f" % a)
        if b != None:
            cmd.append(" B%f" % b)
        if c != None:
            cmd.append(" C%f" % c)
        self.__send_commands(["".join(cmd)])
        return self

    def max_feedrate(self, x=None, y=None, z=None, e=None, a=None, b=None, c=None):
        """
        set the maximum allowed feedrate

        Axies descripton see drive()

        Function blocks execution until the command is sent.
        Returns itself
        """
        cmd = [
            "GM203"
        ]
        if x != None:
            cmd.append(" X%f" % x)
        if y != None:
            cmd.append(" Y%f" % y)
        if z != None:
            cmd.append(" Z%f" % z)
        if e != None:
            cmd.append(" E%f" % e)
        if a != None:
            cmd.append(" A%f" % a)
        if b != None:
            cmd.append(" B%f" % b)
        if c != None:
            cmd.append(" C%f" % c)
        self.__send_commands(["".join(cmd)])
        return self

    def feedrate_multiplier(self, x=None, y=None, z=None, e=None, a=None, b=None, c=None):
        """
        set max feedrate multiplier

        this factor is normally 1.0000

        it will be applied on G0/G1 commands when the F-Parameter is given
        the given speed is multiplied with this factor before setting it.
        this allows slow rotating axies to kind of ignore the F-Parameter

        Axies descripton see drive()

        Function blocks execution until the command is sent.
        Returns itself
        """
        cmd = [
            "M204"
        ]
        if x != None:
            cmd.append(" X%f" % x)
        if y != None:
            cmd.append(" Y%f" % y)
        if z != None:
            cmd.append(" Z%f" % z)
        if e != None:
            cmd.append(" E%f" % e)
        if a != None:
            cmd.append(" A%f" % a)
        if b != None:
            cmd.append(" B%f" % b)
        if c != None:
            cmd.append(" C%f" % c)
        self.__send_commands(["".join(cmd)])
        return self

    def dwell(self, timeout_milliseconds):
        """
        controller sleeps for this amount of time

        Function blocks execution until the command is sent.
        Returns itself
        """
        self.__send_commands(["G4T%d" % (timeout_milliseconds//1000)]) #FIXME G4T uses seconds instead of milliseconds
        return self

    def vacuum(self, enable):
        """
        turn the vacuum pump (motor) on/off

        Function blocks execution until the command is sent.
        Returns itself
        """
        if enable:
            self.__send_commands(["M10"])
        else:
            self.__send_commands(["M11"])
        return self

    def valve(self, enable):
        """
        turn the vacuum valve to the nozzle on/off

        Function blocks execution until the command is sent.
        Returns itself
        """
        if enable:
            self.__send_commands(["M126"])
        else:
            self.__send_commands(["M127"])
        return self

    def steppers(self, enable):
        """
        turn stepper power on/off

        Function blocks execution until the command is sent.
        Returns itself
        """
        if enable:
            self.__send_commands(["M17"])
        else:
            self.__send_commands(["M18"])
        return self


    def light_botup(self, enable=True):
        """
        Switch Light ON/OFF (True/False)

        Function blocks execution until the command is sent.
        Returns itself
        """
        self.__set_io(2, enable)
        return self


    def light_topdn(self, enable=True):
        """
        Switch Light ON/OFF (True/False)

        Function blocks execution until the command is sent.
        Returns itself
        """
        self.__set_io(3, enable)
        return self


    def light_tray(self, enable=True):
        """
        Switch Light ON/OFF (True/False)

        Function blocks execution until the command is sent.
        Returns itself
        """
        self.__set_io(5, enable)
        return self


    def default_settings(self):
        """
        Set Stepper Acceleration and Speeds to default (like after reset)
        """
        self.__send_commands(["M512"])
        return self


    def raw_command(self, gcode):
        """
        Send a raw GCODE command

        Function blocks execution until the command is sent.
        Returns itself
        """
        self.__send_commands([gcode])
        return self


    def __set_io(self, io, enable):

        """
        control IO
        """
        self.__send_commands(["M42 P%d S%d" % (io, 1 if enable else 0)])


    def __send_commands(self, list):
        """
        Send one or multiple Gcode commands.
        Handles handshaking.
        """
        for s in list:
            self.con.write(bytes(s, encoding="utf8"))
            print(s)
            self.con.write(b";\n")
            self.con.flush()
            self.__full = True #assume it
            self.__receive_answer()
            while self.__full: #if it is full we need to wait until queue gets consumed
                self.__receive_answer()


    def __receive_answer(self):
        """
        Receives at least one line but multiple if needed.
        Depending on the result, Exceptions are thrown or Flags set.
        """

        do = True
        while do:
            msg = self.con.readline().decode().strip()

            print(msg)
            if msg == "":
                #timeout happened
                print("timeout happened")
            elif msg == "OK":
                #means queue is not full (and also not empty because a command was just sent)
                self.__full = False
                self.__empty = False
            elif msg == "READY":
                #means queue was previously full but has now been cleared and can hold another command.
                self.__full = False
                self.__empty = False
            elif msg == "FULL":
                #means queue is full
                self.__full = True
                self.__empty = False
            elif msg == "EMPTY":
                #means queue is empty
                self.__full = False
                self.__empty = True
            elif msg == "SYNC":
                #means sync comamnd has been reached
                self.__sync = True
            #elif msg == b"ERR_COMMAND_NOT_FOUND":
            #    raise Exception(msg
            #    raise Exception(msg)
            else:
                raise Exception(msg)
            do = self.con.in_waiting > 0
