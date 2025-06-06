from ttboard.demoboard import DemoBoard, Pins

import ttboard.util.time as time
import ttboard.log as logging
log = logging.getLogger(__name__)

def wait_clocks(num:int=1):
    for _i in range(num):
        time.sleep_us(1)


from machine import Pin
import rp2
from rp2 import PIO


# https://github.com/TinyTapeout/tt-micropython-firmware/blob/main/src/ttboard/pins/gpio_map.py
# class GPIOMapTT06(GPIOMapBase):
#     RP_PROJCLK = 0
#     PROJECT_nRST = 1
#     CTRL_SEL_nRST = 2
#     CTRL_SEL_INC = 3
#     CTRL_SEL_ENA = 4
#     UO_OUT0 = 5
#     UO_OUT1 = 6
#     UO_OUT2 = 7
#     UO_OUT3 = 8
#     UI_IN0 = 9
#     UI_IN1 = 10
#     UI_IN2 = 11
#     UI_IN3 = 12
#     UO_OUT4 = 13
#     UO_OUT5 = 14
#     UO_OUT6 = 15 
#     UO_OUT7 = 16
#     UI_IN4  = 17
#     UI_IN5  = 18
#     UI_IN6  = 19
#     UI_IN7  = 20
#     UIO0 = 21
#     UIO1 = 22
#     UIO2 = 23
#     UIO3 = 24
#     UIO4 = 25
#     UIO5 = 26
#     UIO6 = 27
#     UIO7 = 28
#     RPIO29 = 29


# Pin layout and mapping between TT Z80 and Pico
#

#                                        / / / /
#                                       |b n i w|
#                                       |u m n a|
#                                       |s i t i|
#                                       |r     t|
#                                               
# ->Z80 |    data-in    |  mux  |       |b n I W|       |            W:/WAIT I:/INT n:/NMI b:/BUSRQ
# TinyT |     8 uio     | 4 ui  | 4 uo  | 4 ui  | 4 uo  |
#       |7 6 5 4 3 2 1 0|7 6 . .|7 6 5 4|3 2 1 0|3 2 1 0|
# Z80-> |    data-out   |       |addr_lo|       |addr_lo| (mux=00..)
#       |    ---//---   |       |addr_hi|       |addr_hi| (mux=01..)
#       |    ---//---   |       |b H f W|       |R I M 1| (mux=1x..) 1:/M1 M:/MREQ I:/IORQ R:/RD _ W:/WR f:/RFSH: H:/HALT b:/BUSAK
# ------+---------------+-------+-------+-------+-------+
# Pico  |8 7 6 5 4 3 2 1|0 9 . .|6 5 4 3|2 1 0 9|8 7 6 5|
# PIO   |      out      | side  |       |  set  |       |
#       |<-----------------in 24-bit------------------->|

#           pin ui: 3210
CPU_EXEC        = 0b1111
CPU_WAIT        = 0b1110
#           pin ui: 76
MUX_CTRL        = 0b10
MUX_ADDR_LO     = 0b00
MUX_ADDR_HI     = 0b01

PIN_CTRL_M1     = 0+0   # in_base + 0   UO_OUT0
PIN_CTRL_MREQ   = 1+0   # in_base + 1   UO_OUT1
PIN_CTRL_IORQ   = 2+0   # in_base + 2   UO_OUT2
PIN_CTRL_RD     = 3+0   # in_base + 3   UO_OUT3
PIN_CTRL_WR     = 4+4   # in_base + 8   UO_OUT4

# @rp2.asm_pio(autopull=False, autopush=False, 
#              out_shiftdir=PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_NONE,
#              in_shiftdir=PIO.SHIFT_LEFT,
#              sideset_init=(PIO.OUT_LOW,)*2,
#              set_init=(PIO.OUT_HIGH,)*4,
#              out_init=(PIO.IN_LOW,)*8)
# def z80_read_handler():
#     set(pins, 0b1111)    # CAN BE OPTIMIZED ???     # gpio[set_base]                <= [/wait=1, /int=1, /nmi=1, /busreq=1]
#     nop()                       .side(0b10)         # CAN BE OPTIMIZED ???
#     wait(0, pin, 3)                                 # gpio[in_base + PIN_CTRL_RD]
#     set(pins, 0b1110)                               # gpio[set_base]                <= [/WAIT=0, /int=1, /nmi=1, /busreq=1]
#     nop()                       .side(0b01)         # CAN BE OPTIMIZED ???
#     in_(pins, 12)               .side(0b01)         # gpio[in_base + 0..11]         => ISR, ISR << 12
#     nop()                       .side(0b00)
#     in_(pins, 12)               .side(0b00)         # gpio[in_base + 0..11]         => ISR, ISR << 12
#     push(block)
#     pull(block)
#     out(pins, 8)                .side(0b10)         # gpio[out_base + 0..7]         <= OSR, OSR >> 8
#     set(pins, 0b1111)                               # gpio[set_base]                <= [/wait=1, /int=1, /nmi=1, /busreq=1]
#     wait(1, pin, 3)                                 # gpio[in_base + PIN_CTRL_RD]

# @rp2.asm_pio(autopull=False, autopush=False, 
#              out_shiftdir=PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_NONE,
#              in_shiftdir=PIO.SHIFT_LEFT,
#              sideset_init=(PIO.OUT_LOW,)*2,
#              # set_init=(PIO.OUT_HIGH,)*4,
#              set_init=(PIO.OUT_HIGH,)*1,
#              out_init=(PIO.OUT_LOW,)*8)
# def z80_readwrite_handler():
#     # NOTE: that Z80 has all control signals inverted (active low)!
#     set(y, 0b01) # TODO: support for IORQ+WR
#                  # currently sensitive only to:     1) RD|*
#                  #                                  2) (notRD)|MREQ|(notM1)
#                  # missing:                         *) (notRD)|IORQ

#                                 # mux:CTRL
#     set(pins, 1)                .side(0b10)         # /WAIT <= 1, Z80 is free to run

#     label("busy_wait")
#     jmp(pin, "not_rd")          .side(0b10)         # detect READs: /RD pin is inverted
#     jmp("read")                 .side(0b10)

#     label("not_rd")
#     in_(pins, 2)                .side(0b10)         # detect WRITEs: ~M1 && MREQ; /M1, /MREQ pins are inverted
#     mov(x, isr)
#     mov(isr, null)                                  # clear ISR!
#     jmp(x_not_y, "busy_wait")


#     label("write")              # mux:CTRL          # will push 2 packets, see run()
#     nop()                       .side(0b10)         #                                   <-- could remove
#     # # wait(0, pin, 8)             .side(0b10)         # ************
#     in_(pins, 24)               .side(0b10)         #
#                                 # mux:ADDR_HI       #
#     push(block)                 .side(0b01)         # packet #1: DATA bus + flags
#     in_(pins, 12)               .side(0b01)         #
#                                 # mux:ADDR_LO       #
#     nop()                       .side(0b00)         #
#     in_(pins, 12)               .side(0b00)         #
#                                 # mux:CTRL          #
#     push(block)                 .side(0b10)         # packet #2: ADDRess bus
#     # # wait(1, pin, 8)             .side(0b10)         # wait until WR finishes
#     pull(block) # dummy pull
#     jmp("busy_wait")


#     label("read")               # mux:CTRL          # will push 2 and pop 1 packet, see run()
#     nop()                       .side(0b10)         #                                   <-- could remove
#     in_(pins, 24)               .side(0b10)         #
#                                 # mux:ADDR_HI       #
#     push(block)                 .side(0b01)         # packet #1: DATA bus + flags
#     in_(pins, 12)               .side(0b01)         #
#                                 # mux:ADDR_LO       #
#     nop()                       .side(0b00)         #
#     in_(pins, 12)               .side(0b00)         #
#     push(block)                                     # packet #2: ADDRess bus
#                                                     #
#     set(pins, 0)                                    # /WAIT <= 0, Z80 is PAUSED until 
#     pull(block)                                     #   wait for packet from RAM to arrive, see run()
#     out(pindirs, 8) # maybe put 1 instruction above #   switch PICO pins that are connected to Z80 DATA bus into WRITE mode 
#     out(pins, 8)                                    #   put RAM value Z80 DATA bus
#                                 # mux:CTRL          #
#     set(pins, 1)                .side(0b10)         # /WAIT <= 1, Z80 is free to run
#     wait(1, pin, 3)             .side(0b10)         # wait until RD finishes
#     out(pindirs, 8)             .side(0b10)         # restore PICO pins back to READ mode 

# @rp2.asm_pio(autopull=False, autopush=False, 
#              out_shiftdir=PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_NONE,
#              in_shiftdir=PIO.SHIFT_LEFT,
#              sideset_init=(PIO.OUT_LOW,)*2,
#              # set_init=(PIO.OUT_HIGH,)*4,
#              set_init=(PIO.OUT_HIGH,)*1,
#              out_init=(PIO.OUT_LOW,)*8)
# def z80_readwrite_handler2():
#     # NOTE: that Z80 has all control signals inverted (active low)!
#     set(y, 0b01) # TODO: support for IORQ+WR
#                  # currently sensitive only to:     1) RD|*
#                  #                                  2) (notRD)|MREQ|(notM1)
#                  # missing:                         *) (notRD)|IORQ
#     label("busy_signal_change_wait") # TODO
#                                 # mux:CTRL
#     set(pins, 1)                .side(0b10)         # /WAIT <= 1, Z80 is free to run

#     label("busy_wait")
#     nop()                       .side(0b10)
#     nop()                       .side(0b10)
#     jmp(pin, "not_rd")          .side(0b10)         # detect READs: /RD pin is inverted
#     jmp("readwrite")            .side(0b10)

#     label("not_rd")
#     in_(pins, 2)                .side(0b10)         # detect WRITEs: ~M1 && MREQ; /M1, /MREQ pins are inverted
#     mov(x, isr)                 .side(0b10)
#     mov(isr, null)              .side(0b10)         # clear ISR!
#     jmp(x_not_y, "busy_wait")   .side(0b10)

#     label("readwrite")          # mux:CTRL          # will push 2 and pop 1 packet, see run()
#     set(pins, 0)                .side(0b10)         # /WAIT <= 0, Z80 is PAUSED until 
#     in_(pins, 24)               .side(0b10)         #
#                                 # mux:ADDR_HI       #
#     nop()                       .side(0b01)
#     nop()                       .side(0b01)                                
#     push(block)                 .side(0b01)         # packet #1: DATA bus + flags
#     in_(pins, 12)               .side(0b01)         #
#                                 # mux:ADDR_LO       #
#     nop()                       .side(0b00)
#     nop()                       .side(0b00)         #
#     nop()                       .side(0b00)
#     in_(pins, 12)               .side(0b00)         #
#     push(block)                                     # packet #2: ADDRess bus
#                                                     #
#                                 # mux:CTRL          #
#     pull(block)                 .side(0b10)         #   wait for packet from RAM to arrive, see run()

#     nop()                       .side(0b10)
#     nop()                       .side(0b10)         #
#     jmp(pin, "busy_signal_change_wait") .side(0b10)

#     out(pindirs, 8) # maybe put 1 instruction above #   switch PICO pins that are connected to Z80 DATA bus into WRITE mode 
#     out(pins, 8)                                    #   put RAM value Z80 DATA bus
#                                 # mux:CTRL          #
#     set(pins, 1)                .side(0b10)         # /WAIT <= 1, Z80 is free to run
#     wait(1, pin, 3)             .side(0b10)         # wait until RD finishes
#     out(pindirs, 8)             .side(0b10)         # restore PICO pins back to READ mode 


@rp2.asm_pio(autopull=False, autopush=False, 
             out_shiftdir=PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_NONE,
             in_shiftdir=PIO.SHIFT_LEFT,
             sideset_init=(PIO.OUT_LOW,)*2,
             set_init=(PIO.OUT_HIGH,)*1,
             out_init=(PIO.OUT_LOW,)*8)
def z80_clocking_handler():
    label("new_clock")
                                # mux:CTRL
    set(pins, 1)                .side(0b10)         # CLK poesedge __/^^
    nop()                       .side(0b10)
    nop()                       .side(0b10)
    jmp(pin, "not_rd")          .side(0b10)         # detect READs: /RD pin is inverted
    jmp("read")                 .side(0b10)

    label("not_rd")
    in_(pins, 2)                .side(0b10)         # detect WRITEs: ~M1 && MREQ; /M1, /MREQ pins are inverted
    mov(x, isr)                 .side(0b10)
    mov(isr, null)              .side(0b10)         # clear ISR!
    set(y, 0b01) # TODO: support for IORQ+WR and IORQ+M1
                 # currently sensitive only to:     1) RD|*
                 #                                  2) (notRD)|MREQ|(notM1)
                 # missing:                         *) (notRD)|IORQ    
    jmp(x_not_y, "clock_ph2")   .side(0b10)

    label("write")              # mux:CTRL          # will push 2 and pop 1 packet, see run()
    label("read")               # mux:CTRL          # will push 2 and pop 1 packet, see run()
    set(pins, 0)                .side(0b10)         # clk negedge  ^^\__

    in_(pins, 24)               .side(0b10)         #
                                # mux:ADDR_HI       #
    nop()                       .side(0b01)
    nop()                       .side(0b01)
    push(block)                 .side(0b01)         # packet #1: DATA bus + flags
    in_(pins, 12)               .side(0b01)         #
                                # mux:ADDR_LO       #
    nop()                       .side(0b00)
    nop()                       .side(0b00)         #
    nop()                       .side(0b00)
    in_(pins, 12)               .side(0b00)         #
    push(block)                                     # packet #2: ADDRess bus
                                                    #
                                # mux:CTRL          #
    pull(block)                 .side(0b10)         #   wait for packet from RAM to arrive, see run()
    jmp(pin, "new_clock")       .side(0b10)

    out(pindirs, 8)                                 #   switch PICO pins that are connected to Z80 DATA bus into WRITE mode 
    out(pins, 8)                                    #   put RAM value Z80 DATA bus

    set(pins, 1)                .delay(2)           # CLK poesedge __/^^
    nop()                       .delay(3)
    nop()                       .delay(3)

    label("clock_ph2")
    set(pins, 0)                .delay(1)           # clk negedge  ^^\__
    nop()                       .delay(3)
    nop()                       .delay(3)

    out(pindirs, 8)             .side(0b10)         # restore PICO pins back to READ mode 


    # Below is the code I was learning from by Mike Bell and Pat Deegan
    # # This does work with a statemachine 
    # # freq of 2MHz... from uPython, we can set registers with 
    # # this in about 40us (down from close to 8 milliseconds!)
    # # any issues, easiest fixes are to just reduce the freq=
    # # in the SM below, see if that resolves things
    # out(isr, 8)         .side(0)                                    OSR => ISR, OSR >> 8
    # in_(isr, 4)         .side(0b11)                                 ISR => ISR, ISR << 4
    # mov(pins, isr)      .side(0b11)                                 ISR => pins
    # out(isr, 8)         .side(0)                                    OSR => ISR, OSR >> 8
    # in_(isr, 4)         .side(0b10)                                 ISR => ISR, ISR << 4
    # mov(pins, isr)      .side(0b10).delay(3)                        ISR => pins

    #              7ui4 7uo4 3ui0 3uo0
    # 0     :ISR  [...._...._...._....]    OSR: [VVVV_vvvv_RRRR_rrrr]
    # 1(out):ISR  [0000_0000_RRRR_rrrr]    OSR: [...._...._VVVV_vvvv]
    # 2(in_):ISR  [0000_RRRR_rrrr_rrrr]
    # 3(mov):pins [0000_RRRR_rrrr_rrrr]
    # 4(out):ISR  [0000_0000_VVVV_vvvv]
    # 5(in_):ISR  [0000_VVVV_vvvv_vvvv]
    # 6(mov):pins [0000_VVVV_vvvv_vvvv]

class Z80PIO:
    '''
        PIO implementation of the Z80 interface.
    '''
    def __init__(self, tt:DemoBoard, chip_frequency=10_000): # 2000000):
        self.tt = tt
        
        # tt.uio_oe_pico.value = 255 # DATA bus on the Z80 side is set to read, PICO side is set to write
        tt.uio_oe_pico.value = 0
        tt.uio_in = 0 # NOP instruction by default
        tt.ui_in[3:0] = 0b1110 # /WAIT
        tt.ui_in[7:4] = 0
        
        self._wait = 0
        self._int = 0
        self._nmi = 0
        self._busrq = 0

        # self.sm = rp2.StateMachine(0, z80handler, 
        # self.sm = rp2.StateMachine(0, z80_readwrite_handler2, 
        #     freq=chip_frequency,
        #     jmp_pin=     tt.pins.uo_out3.raw_pin,   # jumps on /RD signal
        #     in_base=     tt.pins.uo_out0.raw_pin,   # reads     CTRL signals and ADDR bus
        #     set_base=    tt.pins.ui_in0.raw_pin,    # sets      CTRL signals (WAIT) ???, INT, NMI, BUSREQ) 
        #     sideset_base=tt.pins.ui_in6.raw_pin,    # sets      MUX
        #     out_base=    tt.pins.uio0.raw_pin)      # writes to DATA bus

        tt.ui_in[3:0] = 0b1111 # /WAIT
        self.sm = rp2.StateMachine(0, z80_clocking_handler,
            freq=chip_frequency,
            jmp_pin=     tt.pins.uo_out3.raw_pin,   # jumps on /RD signal
            in_base=     tt.pins.uo_out0.raw_pin,   # reads     CTRL signals and ADDR bus
            set_base=    tt.pins.rp_projclk.raw_pin,# toggles   CLK 
            sideset_base=tt.pins.ui_in6.raw_pin,    # sets      MUX
            out_base=    tt.pins.uio0.raw_pin)      # writes to DATA bus


        self.sm.active(True)

    def run(self, ram, addr_mask:int=0xFFFF, verbose:bool=False):
        return self._run(ram, addr_mask, verbose)

    @micropython.viper
    def _run(self, ram:ptr8, addr_mask:int=0xFFFF, verbose:bool=False):
        # reads:int = 0
        # writes:int = 0
        execution_reached_past_addr_0:bool = False
        while True:
            x:int       = int(self.sm.get()) # 1st packet contains flags & value from the DATA bus
            y:int       = int(self.sm.get()) # 2nd packet contains lo & hi bits of the ADDRess bus
            rd:bool     = (x &  0x08) == 0
            wr:bool     = (x & 0x100) == 0
            halt:bool   = (x & 0x400) == 0
            addr:int    = (((y>>8) & 0xF000) | ((y>>4) & 0x0FF0) | (y & 0x000F)) & addr_mask
            if verbose:
                m1      = (x &  0x01) == 0
                mreq    = (x &  0x02) == 0                
                value   = ((x>>16) & 0xFF)
                flags   = 0x100 - (((x>>4) & 0xF0) | (x & 0xF))
                print(
                    "m1" if m1 else "  ", "mr" if mreq else "  ", "rd" if rd else "  ", "wr" if wr else "  ", "halt" if halt else "    ",\
                    "addr", hex(addr), hex(value) if wr else hex(int(ram[addr & addr_mask])),\
                    hex(y), hex(x),\
                    "r/t:", self.sm.rx_fifo(), self.sm.tx_fifo())
            if rd:
                value_from_ram = ram[addr]
                self.sm.put((value_from_ram << 8) | 0x00_00_FF) # 1) 0xFF sets PICO pindirs to write
                                                                # 2) PICO puts byte from RAM on Z80's data bus
                                                                # 3) 0x00 sets PICO pindirs back to read
                # reads += 1
            elif wr:
                value = (x>>16) & 0xFF
                ram[addr] = value
                self.sm.put(0) # dummy packet
            else:
                self.sm.put(0) # dummy packet

            if halt:
                flags = 0x100 - (((x>>4) & 0xF0) | (x & 0xF))
                return addr, flags

            if (addr & addr_mask) == 0:
                flags = 0x100 - (((x>>4) & 0xF0) | (x & 0xF))
                if execution_reached_past_addr_0:
                    return addr, flags

            execution_reached_past_addr_0 = addr > 0

            # if reads % 16384 == 0:
            #     print(reads)

    # def _update_cpu_ctrl():
    #     sm.exec(f"set(pins, 0b{1-self._busrq}{1-self._nmi}{1-self._int}{1-self._wait})")

    # @property
    # def WAIT(self):
    #     return self._wait
    # @WAIT.setter 
    # def WAIT(self, flag:bool):
    #     self._wait = flag
    #     self._update_cpu_ctrl()

    # @property
    # def INT(self):
    #     return self._int
    # @INT.setter 
    # def INT(self, flag:bool):
    #     self._int = flag
    #     self._update_cpu_ctrl()

    # @property
    # def NMI(self):
    #     return self._nmi
    # @NMI.setter 
    # def NMI(self, flag:bool):
    #     self._nmi = flag
    #     self._update_cpu_ctrl()

    # @property
    # def BUSRQ(self):
    #     return self._busrq
    # @BUSRQ.setter 
    # def BUSRQ(self, flag:bool):
    #     self._busrq = flag
    #     self._update_cpu_ctrl()

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
