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
        
        # self.tt.bidir_mode = [Pins.IN, Pins.IN, Pins.IN, Pins.IN, 
        #                       Pins.IN, Pins.IN, Pins.IN, Pins.IN] # initial DATA bus configution
        
        # self.tt.bidir_byte = 0 # NOP instruction by default
        
        tt.uio_oe_pico.value = 255 # DATA bus on the Z80 side is set to input
        tt.uio_in = 0 # NOP instruction by default

        self.tt.ui_in = 0b0000_1111 # set /WAIT, /INT, /NMI, /BUSRQ (inverted)
        self._wait = 0
        self._int = 0
        self._nmi = 0
        self._busrq = 0

    def set_mux_to_ctrl(self):
        self.tt.ui_in[7] = 1

    def set_mux_addr_hi(self):
        self.tt.ui_in[6] = 1
        self.tt.ui_in[7] = 0

    def set_mux_addr_lo(self):
        self.tt.ui_in[6] = 0
        self.tt.ui_in[7] = 0

    @property
    def addr(self):
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
        # return self.tt.bidir_byte
        return self.tt.uio_out
    @data.setter 
    def data(self, set_to:int):
        # self.tt.bidir_byte = set_to
        self.tt.uio_in = set_to

    @property
    def WAIT(self):
        return self._wait
    @WAIT.setter 
    def wait(self, set_to:bool):
        self.tt.pins.ui_in0 = ~set_to
        self._wait = ~set_to

    @property
    def INT(self):
        return self._int
    @INT.setter 
    def INT(self, set_to:bool):
        self.tt.pins.ui_in1 = ~set_to
        self._int = ~set_to

    @property
    def NMI(self):
        return self._nmi
    @NMI.setter 
    def NMI(self, set_to:bool):
        self.tt.pins.ui_in2 = ~set_to
        self._nmi = ~set_to

    @property
    def BUSRQ(self):
        return self._busrq
    @BUSRQ.setter 
    def BUSRQ(self, set_to:bool):
        self.tt.pins.ui_in3 = ~set_to
        self._busrq = ~set_to

    @property
    def M1(self):
        self.set_mux_to_ctrl()
        return ~tt.pins.pin_uo_out0.value()

    @property
    def MREQ(self):
        self.set_mux_to_ctrl()
        return ~tt.pins.pin_uo_out1.value()

    @property
    def IORQ(self):
        self.set_mux_to_ctrl()
        return ~tt.pins.pin_uo_out2.value()

    @property
    def RD(self):
        self.set_mux_to_ctrl()
        return ~tt.pins.pin_uo_out3.value()

    @property
    def WR(self):
        self.set_mux_to_ctrl()
        return ~tt.pins.pin_uo_out4.value()

    @property
    def RFSH(self):
        self.set_mux_to_ctrl()
        return ~tt.pins.pin_uo_out5.value()

    @property
    def HALT(self):
        self.set_mux_to_ctrl()
        return ~tt.pins.pin_uo_out6.value()

    @property
    def BUSAK(self):
        self.set_mux_to_ctrl()
        return ~tt.pins.pin_uo_out7.value()




    # @property
    # def we(self):
    #     return ~self.tt.pins.uio0()
    # @we.setter 
    # def we(self, set_to:int):
    #     self._pin_we_bar.value(~set_to)
        
        
    # @property 
    # def sel0(self):
    #     return self.tt.pins.uio1()
    # @sel0.setter 
    # def sel0(self, set_to:int):
    #     self.tt.pins.uio1(set_to)
        
        
    # @property 
    # def sel1(self):
    #     return self.tt.pins.uio2()
    # @sel1.setter 
    # def sel1(self, set_to:int):
    #     self.tt.pins.uio2(set_to)
        
            
    
    # def set_value(self, value):
    #     self.value = value
    # @property 
    # def value(self):
    #     return self._cur_val
    # @value.setter
    # def value(self, set_to:int):
    #     self.we = 1
    #     self.bus = set_to 
    #     self._cur_val = set_to
    #     if self.latch_delay_clocks:
    #         wait_clocks(self.latch_delay_clocks)
    #     self.we = 0
        
    #     #log.info(f'Set {self.register} to {set_to}')
        
        
        
        
    
        
