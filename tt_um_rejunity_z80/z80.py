from ttboard.demoboard import DemoBoard, Pins

import ttboard.util.time as time
import ttboard.log as logging
log = logging.getLogger(__name__)

def wait_clocks(num:int=1):
    for _i in range(num):
        time.sleep_us(1)
# Many thanks to Mike Bell, Pat Deegan and Uri Shaked for code examples and optimisation tips!
# With their help effective Z80 speed went from 300 KHz to 4 MHz.

# With Z80PIO class Z80 core frequency 4_000_000 (ceiling is around 4_020_000) is possible
#   if RP2040 is overcloked to 266_000_000
#
# Z80 address/control multiplexor response delay seems to be somewhere around 32.1 .. 24.1 MHz
# This assesment is based on observation that PIO running 96.48 MHz
# 4 cyles of delay is necessary between onset of the MUX pin and reading the correct value back from Z80.
#
# Effective measured speed for reads (NOP): 3.931MHz            -- demo.exec("", freq=4_000_000)
# Effective measured speed for writes (PUSH HL): of 3.647MHz    -- demo.exec("push", freq=4_000_000) 
#
# NOTE: by removing "if verbose" branch in Z80PIO _run() are slightly faster speed is possible!

from machine import Pin
import rp2
from rp2 import PIO

# Pin layout and mapping between TT Z80 and Pico / PIO ##################################################
# Based on: https://github.com/TinyTapeout/tt-micropython-firmware/blob/main/src/ttboard/pins/gpio_map.py
# class GPIOMapTT06(GPIOMapBase):
#     RP_PROJCLK = 0
#     PROJECT_nRST = 1
#     ..
#     UO_OUT0 = 5
#     ..
#     UO_OUT3 = 8
#     UI_IN0 = 9
#     ..
#     UI_IN3 = 12
#     UO_OUT4 = 13
#     ..
#     UO_OUT7 = 16
#     UI_IN4  = 17
#     ..
#     UI_IN7  = 20
#     UIO0 = 21
#     ..
#     UIO7 = 28

#                                            / / / /
#                                           |b n i w|
#                                           |u m n a|
#                                           |s i t i|
#                                           |r     t|
#                                               
# -> Z80 in |    data-in    |  MUX  |       |b n I W|       |         |            W:/WAIT I:/INT n:/NMI b:/BUSRQ
# - - - - - | - - - - - - - | - - - | - - - - - - - | - - - | - - - - |
#TinyTapeout|     8 uio     | 4 ui  | 4 uo  | 4 ui  | 4 uo  |      clk|
#    pin    |7 6 5 4 3 2 1 0|7 6 . .|7 6 5 4|3 2 1 0|3 2 1 0|         |
# - - - - - | - - - - - - - | - - - | - - - - - - - | - - - | - - - - |
# Z80 -> out|    data-out   |       |addr_lo|       |addr_lo|         | (MUX=00..)
#           |    ---//---   |       |addr_hi|       |addr_hi|         | (MUX=01..)
#           |    ---//---   |       |b H f W|       |R I M 1|         | (MUX=1x..) 1:/M1 M:/MREQ I:/IORQ R:/RD _ W:/WR f:/RFSH: H:/HALT b:/BUSAK
# ----------+---------------+-------+-------+-------+-------+---------+
# Pico pin  |8 7 6 5 4 3 2 1|0 9 . .|6 5 4 3|2 1 0 9|8|7 6 5|. . . . 0|
# PIO ctrl  |      out      | side  |               |j|     |   set   |
#           |               |       |               |m|     |         |
#           |               |       |               |p|     |         |
#           |<-----------------in 24-bit------------------->| 


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

# Many thanks to Mike Bell, Pat Deegan and Uri Shaked for code examples and tips!
# With their help effective Z80 speed went from 300 KHz to 4 MHz.

@rp2.asm_pio(autopull=False, autopush=False, 
             out_shiftdir=PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_NONE,
             in_shiftdir=PIO.SHIFT_LEFT,
             sideset_init=(PIO.OUT_LOW,)*2,
             set_init=(PIO.OUT_HIGH,)*1,
             out_init=(PIO.OUT_LOW,)*8)
def z80_clocking_handler():
    label("new_clock") ############################## Detect if READ or WRITE is happening
                                # mux:CTRL          #
    set(pins, 1)                .side(0b10).delay(3)#   CLK poesedge __/^^
    jmp(pin, "not_rd")          .side(0b10)         #   detect READ=RD; note /RD pin is inverted
    jmp("read")                 .side(0b10)

    label("not_rd")
    in_(pins, 2)                .side(0b10)         #   detect WRITE=(~M1 && MREQ); note /M1 /MREQ pins are inverted
    mov(x, isr)                 .side(0b10)
    mov(isr, null)              .side(0b10)         #   clear ISR!
    jmp(x_not_y, "clock_ph2")   .side(0b10)         #   if neither READ or WRITE happened,
                                                    #   jump straigt to the 2nd phase of the clock cycle

    label("write") #############           ########## To process READ or WRITE we will push 32bit and pop 24bit block, see run()
    label("read")                                   #
    set(pins, 0)                .side(0b10)         #   clk negedge  ^^\__
                                                    #
    mov(osr, pins)              .side(0b10)         #   use OSR register to skip (shift out of the register) ui_io nibbles
    out(null, 16)               .side(0b10)         #   OSR <= pins >> 16; ISR <= OSR[7..0]
    in_(osr, 8)                 .side(0b10)         #   ISR <= {value}
    mov(osr, pins)              .side(0b10)         #
    out(null, 8)                .side(0b10)         #
    in_(osr, 4)                 .side(0b10)         #   ISR <= {data_8bit, flags_only_bHfW_4bit}
    in_(pins, 4)                .side(0b01).delay(3)#   ISR <= {data_8bit, flags_8bit}
                                # mux:ADDR_HI       #
    mov(osr, pins)              .side(0b01)         #
    out(null, 8)                .side(0b01)         #
    in_(osr, 4)                 .side(0b01)         #   ISR <= {data_8bit, flags_8bit, addr_upper__4bit}
    in_(pins, 4)                .side(0b00).delay(3)#   ISR <= {data_8bit, flags_8bit, addr_upper__8bit}
                                # mux:ADDR_LO       #
    mov(osr, pins)              .side(0b00)         #
    out(null, 8)                .side(0b00)         #
    in_(osr, 4)                 .side(0b00)         #   ISR <= {data_8bit, flags_8bit, addr_upper_12bit}
    in_(pins, 4)                .side(0b00)         #   ISR <= {data_8bit, flags_8bit, addr_all___16bit} {31..0}
    push(block)                 .side(0b10)         #   PUSH contents of ISR to CPU
                                                    #
                                # mux:CTRL          #
    pull(block)                 .side(0b10)         #   WAIT for packet with RAM contents to arrive, see run()
    # jmp(pin, "new_clock")       .side(0b10)       #   WRITE ends here

    out(pindirs, 8)                                 #   switch PICO pins that are connected to Z80 DATA bus into WRITE mode 
    out(pins, 8)                                    #   put RAM value on the Z80 DATA bus
                                                    #   and hold results for 1 more clock cycle

    #################################################
    set(pins, 1)                .delay(3)           # CLK poesedge __/^^
    
    label("clock_ph2") ##############################
    set(pins, 0)                .delay(2)           # clk negedge  ^^\__
    out(pindirs, 8)             .side(0b10)         # restore PICO pins back to READ mode
                                                    # READ ends here


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


        self.sm.exec("set(y, 0b01)")
        self.sm.active(True)

    def run(self, ram, addr_mask:int=0xFFFF, verbose:bool=False):
        return self._run(ram, addr_mask, verbose)


    @micropython.viper
    def _run(self, ram:ptr8, addr_mask:int=0xFFFF, verbose:bool=False):
        # reads:int = 0
        # writes:int = 0
        execution_reached_past_addr_0:bool = False
        FLEVEL  = ptr32(0x5020000C)
        TXF0    = ptr32(0x50200010)
        RXF0    = ptr32(0x50200020)
        while True:
            while ((FLEVEL[0] >> 4) & 0b_1111) == 0: # busy wait while RX FIFO is empty, RX0[7..4] bits
                pass
            x = RXF0[0] # packet contains DATA bus value [31..24], flags [23..16] and ADDRess [15..0]
            wr      = (x & 0x10_0000) == 0
            addr    =  x & addr_mask
            if verbose:
                m1      = (x & 0x01_0000) == 0
                mreq    = (x & 0x02_0000) == 0
                rd      = (x & 0x08_0000) == 0
                halt    = (x & 0x40_0000) == 0
                value   = (x>>24) & 0xFF
                print(
                    "m1" if m1 else "  ", "mr" if mreq else "  ", "rd" if rd else "  ", "wr" if wr else "  ", "halt" if halt else "    ",\
                    "addr", hex(addr), hex(value) if wr else hex(int(ram[addr])),\
                    hex(x),\
                    "r/t:", self.sm.rx_fifo(), self.sm.tx_fifo())
            if wr:
                value   = (x>>24) & 0xFF
                ram[addr] = value
                TXF0[0] = int(0) # dummy packet
            else:
                value_from_ram = ram[addr]
                write_packet = (value_from_ram << 8) | 0x00_00_FF
                TXF0[0] = write_packet
                # self.sm.put((value_from_ram << 8) | 0x00_00_FF) # 1) 0xFF sets PICO pindirs to write
                #                                                 # 2) PICO puts byte from RAM on Z80's data bus
                #                                                 # 3) 0x00 sets PICO pindirs back to read
                # reads += 1
                # self.sm.put(0) # dummy packet

                halt   = (x & 0x40_0000) == 0
                if halt:
                    flags       = (x>>16) & 0xFF
                    return addr, 0x100-flags

            if addr == 0:
                flags       = (x>>16) & 0xFF
                if execution_reached_past_addr_0:
                    return addr, 0x100-flags

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
