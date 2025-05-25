'''
Created on May 23, 2025

@author: ReJ aka Renaldas Zioma
'''

from ttboard.demoboard import DemoBoard

import ttboard.log as logging
log = logging.getLogger(__name__)

from examples.tt_um_rejunity_z80.z80 import Z80
from examples.tt_um_rejunity_z80.setup import setup
import ttboard.util.time as time 

# 7 segment display
#   a
#  f b
#   g
#  e c
#   d   (h - dot)
ascii_to_7seg = {
#        __hgfe_dcba
    '0': 0b0011_1111,
    '1': 0b0000_0110,
    '2': 0b0101_1011,
    '3': 0b0100_1111,
    '4': 0b0110_0110,
    '5': 0b0110_1101,
    '6': 0b0111_1101,
    '7': 0b0000_0111,
    '8': 0b0111_1111,
    '9': 0b0110_1111,
    'A': 0b0111_0111,
    'b': 0b0111_1100,
    'B': 0b0111_1111,
    'C': 0b0011_1001,
    'c': 0b0101_1000,
    'd': 0b0101_1110,
    'E': 0b0111_1001,
    'F': 0b0111_0001,
    'G': 0b0011_1101,
    'g': 0b0110_1111,
    '^': 0b0000_0001,
    '-': 0b0100_0000,
    ' ': 0b0000_0000,
    '.': 0b1000_0000,
    '!': 0b1000_0010,
    '_': 0b0000_1000,
    '=': 0b0100_1000,
    'H': 0b0111_0110,
    'h': 0b0111_0100,
    'I': 0b0000_0110,
    'i': 0b0000_0100,
    'J': 0b0001_1111,
    'L': 0b0011_1000,
    'l': 0b0000_0110,
    'N': 0b0011_0111,
    'n': 0b0101_0100,
    'O': 0b0011_1111,
    'o': 0b0101_1100,
    'P': 0b0111_0011,
    'q': 0b0110_0111,
    'R': 0b0011_0011,
    'r': 0b0101_0000,
    'S': 0b0110_1101,
    'T': 0b0011_0001,
    't': 0b0111_1000,
    'U': 0b0011_1110,
    'u': 0b0001_1100,
    'Y': 0b0110_0110,
    'y': 0b0110_1110,
    'Z': 0b0101_1011,    
}

def print7(z80, text, art=ascii_to_7seg, delay=1000):
    tt = z80.tt
    delay = delay//10
    def display(symbol):
        z80.data = 0xC3 # JP nnnn, nn should appear on the address bus and on the TT board 7-segment LED display
        tt.clock_project_once(msDelay=delay)
        tt.clock_project_once(msDelay=delay)
        tt.clock_project_once(msDelay=delay)
        tt.clock_project_once(msDelay=delay)
        z80.data = art[symbol]
        tt.clock_project_once(msDelay=delay)
        tt.clock_project_once(msDelay=delay)
        tt.clock_project_once(msDelay=delay)
        z80.data = art[symbol]
        tt.clock_project_once(msDelay=delay)
        tt.clock_project_once(msDelay=delay)
        tt.clock_project_once(msDelay=delay)

    for c in text:
        display(c)
    tt.clock_project_once()

def nop(delay=100):
    tt = DemoBoard.get()
    if not setup(tt):
        return False 
    
    chip = Z80(tt)

    while True:
        tt.clock_project_once(msDelay=delay)

def hello(delay=500):
    tt = DemoBoard.get()
    if not setup(tt):
        return False 
    
    z80 = Z80(tt)
    z80.set_mux_addr_hi()

    print7(z80, "01234567890 _-^ Z80 HELLO Uorld. . . Z80 _-^ Z80 HEllo Uorld. . . Z80 _-^ Z8o hcllo uorld. . . _-^Z80^-_ .", art=ascii_to_7seg, delay=delay)


NOP         = 0x00
LD_BC_nnnn  = 0x01
LD_DE_nnnn  = 0x11
LD_HL_nnnn  = 0x21
LD_SP_nnnn  = 0x31
POP_BC      = 0xC1
POP_DE      = 0xD1
POP_HL      = 0xE1
POP_AF      = 0xF1
PUSH_BC     = 0xC5
PUSH_DE     = 0xD5
PUSH_HL     = 0xE5
PUSH_AF     = 0xF5
JP_nnnn     = 0xC3
RET         = 0xC9
def op(opcodes):
    if isinstance(opcodes, int):
        opcodes = [opcodes]
    return bytearray(opcodes)
def op_LD_nnnn(reg, hi, lo=-1):
    if lo < 0:
        lo = hi %  0x100
        hi = hi // 0x100
    # TODO: IX/IY
    opcode = {"BC":LD_BC_nnnn,"DE":LD_DE_nnnn,"HL":LD_HL_nnnn,"SP":LD_SP_nnnn}[reg.upper()]
    return op([opcode, lo, hi])
def op_JP_nnnn(hi, lo=-1):
    if lo < 0:
        lo = hi %  0x100
        hi = hi // 0x100
    return op([JP_nnnn, lo, hi])

def prog_rom(delay=1, direct=True, verbose=False):
    tt = DemoBoard.get()
    if not setup(tt):
        return False 
    
    z80 = Z80(tt)
    z80.set_mux_addr_hi()

    text = "Z8o HELLO uorld."
    code = bytearray()
    jp_len = len(op_JP_nnnn(0))
    for c in text:
        assert len(code) < 256
        code += op_JP_nnnn(hi=ascii_to_7seg[c], lo=len(code)+jp_len)
    print(code)
    assert len(code) == len(text)*jp_len

    if direct:
        while True:
            tt.ui_in = 0b0000_1111 # mux lo addr
            rom_addr = tt.uo_out.value.to_unsigned()
            tt.ui_in = 0b0100_1111 # mux hi addr
            if rom_addr >= len(code):
                break
            z80.data = code[rom_addr]
            tt.clock_project_once(msDelay=delay)
    else:
        while True:
            if verbose:
                z80.dump()

            rom_addr = z80.addr & 0xFF
            z80.set_mux_addr_hi()
            if rom_addr >= len(code):
                break
            z80.data = code[rom_addr]
            tt.clock_project_once(msDelay=delay)

    tt.clock_project_once()


    # while True:
    #     # if type == 0:
    #     #     tt.ui_in[6] = 0
    #     #     rom_addr = int(tt.uo_out)
    #     #     tt.ui_in[6] = 1
    #     # elif type == 1:
    #     #     rom_addr = z80.addr & 0xFF
    #     # else:
    #     #     rom_addr = z80.addr_wait & 0xFF
    #     # z80.set_mux_addr_hi()
    #     # if rom_addr >= len(code):
    #         # break
    #     tt.ui_in[6] = 0
    #     rom_addr = int(tt.uo_out)
    #     tt.ui_in[6] = 1
    #     z80.data = code[rom_addr]
    #     # tt.clock_project_once(msDelay=delay)
    #     tt.clock_project_once()
    #     # if verbose:
    #     #     # print(rom_addr, code[rom_addr])
    #     #     z80.dump()
    # tt.clock_project_once()

