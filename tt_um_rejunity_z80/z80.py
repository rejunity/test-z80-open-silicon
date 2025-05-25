from ttboard.demoboard import DemoBoard, Pins

import ttboard.util.time as time
import ttboard.log as logging
log = logging.getLogger(__name__)

def wait_clocks(num:int=1):
    for _i in range(num):
        time.sleep_us(1)
        
class Z80:
    '''
        Pure Python implementation, sans PIO or anything fancy.
        It's clean.  It's slow.
        But it does work and can act as an easy-to-debug reference.
    '''
    def __init__(self, tt:DemoBoard):
        self.tt = tt 

        tt.uio_oe_pico.value = 255 # DATA bus on the Z80 side is set to read, PICO side is set to write
        tt.uio_in = 0 # NOP instruction by default

        self.tt.ui_in = 0b0000_1111 # set /WAIT, /INT, /NMI, /BUSRQ (inverted)
        self._wait = 0
        self._int = 0
        self._nmi = 0
        self._busrq = 0

    def dump(self):
        save_mux = self.tt.ui_in[7:6]
        print(f"(out) ADDR:{self.addr:04x}" +
            f" M1:{int(self.M1)} MREQ:{int(self.MREQ)} RD:{int(self.RD)} WR:{int(self.WR)} IORQ:{int(self.IORQ)} HALT:{int(self.HALT)}" +
            f" (in) WAIT:{int(self.WAIT)} INT:{int(self.INT)} NMI:{int(self.NMI)}" +
            f" | BUSRQ:{int(self.BUSRQ)}/BUSAK:{int(self.BUSAK)} RFSH:{int(self.RFSH)}")
        self.tt.ui_in[7:6] = save_mux

    def set_mux_to_ctrl(self):
        self.tt.ui_in[7] = 1

    def set_mux_addr_hi(self):
        self.tt.ui_in[7:6] = 0b01

    def set_mux_addr_lo(self):
        self.tt.ui_in[7:6] = 0b00

    def update_data_bus_direction_on_pico(self):
        if self.WR:
            assert self.RD == False, "both RD and WR signals are activated simultaneously!"
            tt.uio_oe_pico.value = 0
        else:
            tt.uio_oe_pico.value = 255

    @property
    def addr(self):
        self.set_mux_addr_hi()
        hi = int(self.tt.uo_out) # NOTE: it is important to convert to int() immediately here in order
                                 #       to derefernce uo_out and force-read the value of the pins
        self.set_mux_addr_lo()
        lo = int(self.tt.uo_out)
        return hi*256 + lo

    @property
    def addr_wait(self):
        self.set_mux_addr_hi()
        wait_clocks(1)
        hi = int(self.tt.uo_out) # NOTE: it is important to convert to int() immediately here in order
                                 #       to derefernce uo_out and force-read the value of the pins
        self.set_mux_addr_lo()
        wait_clocks(1)
        lo = int(self.tt.uo_out)
        return hi*256 + lo

    @property
    def data(self):
        return self.tt.uio_out
    @data.setter 
    def data(self, value:int):
        self.tt.uio_in = value

    @property
    def WAIT(self):
        return self._wait
    @WAIT.setter 
    def WAIT(self, flag:bool):
        self.tt.ui_in[0] = not flag
        self._wait = flag

    @property
    def INT(self):
        return self._int
    @INT.setter 
    def INT(self, flag:bool):
        self.tt.ui_in[1] = not flag
        self._int = flag

    @property
    def NMI(self):
        return self._nmi
    @NMI.setter 
    def NMI(self, flag:bool):
        self.tt.ui_in[2] = not flag
        self._nmi = flag

    @property
    def BUSRQ(self):
        return self._busrq
    @BUSRQ.setter 
    def BUSRQ(self, flag:bool):
        self.tt.ui_in[3] = not flag
        self._busrq = flag

    @property
    def M1(self):
        self.set_mux_to_ctrl()
        return not self.tt.uo_out[0]

    @property
    def MREQ(self):
        self.set_mux_to_ctrl()
        return not self.tt.uo_out[1]

    @property
    def IORQ(self):
        self.set_mux_to_ctrl()
        return not self.tt.uo_out[2]

    @property
    def RD(self):
        self.set_mux_to_ctrl()
        return not self.tt.uo_out[3]

    @property
    def WR(self):
        self.set_mux_to_ctrl()
        return not self.tt.uo_out[4]

    @property
    def RFSH(self):
        self.set_mux_to_ctrl()
        return not self.tt.uo_out[5]

    @property
    def HALT(self):
        self.set_mux_to_ctrl()
        return not self.tt.uo_out[6]

    @property
    def BUSAK(self):
        self.set_mux_to_ctrl()
        return not self.tt.uo_out[7]
