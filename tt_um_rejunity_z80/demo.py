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

# ascii_to_7seg = {
#     '0': 0b1111110,
#     '1': 0b0110000,
#     '2': 0b1101101,
#     '3': 0b1111001,
#     '4': 0b0110011,
#     '5': 0b1011011,
#     '6': 0b1011111,
#     '7': 0b1110000,
#     '8': 0b1111111,
#     '9': 0b1111011,
#     'A': 0b1110111,
#     'b': 0b0011111,
#     'C': 0b1001110,
#     'c': 0b0001101,
#     'd': 0b0111101,
#     'E': 0b1001111,
#     'F': 0b1000111,
#     '-': 0b0000001,
#     ' ': 0b0000000,
#     '_': 0b0001000,
#     '=': 0b0001001,
#     'H': 0b0110111,
#     'L': 0b0001110,
#     'l': 0b0000110, # *
#     'o': 0b0001111, # *
#     'P': 0b1100111,
#     'r': 0b0000101, # *
#     'U': 0b0111110
# }

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
    'n': 0b0101_0100,
    'O': 0b0011_1111,
    'o': 0b0101_1100,
    'P': 0b0111_0011,
    'q': 0b0110_0111,
    'r': 0b0101_0000,
    'S': 0b0110_1101,
    't': 0b0111_1000,
    'U': 0b0011_1110,
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

    print7(z80, "01234567890 . . . Z80 HELLO Uorld. . . Z80! ! ! Z80 HELLO Uorld. . .", art=ascii_to_7seg, delay=delay)
    # tt = DemoBoard.get()
    # if not setup(tt):
    #     return False 
    
    # z80 = Z80(tt)
    # z80.set_mux_addr_hi()

    # def display(symbol):
    #     z80.data = 0xC3 # JP nnnn, nn should appear on the address bus and on the TT board 7-segment LED display
    #     tt.clock_project_once(msDelay=100)
    #     tt.clock_project_once(msDelay=100)
    #     tt.clock_project_once(msDelay=100)
    #     tt.clock_project_once(msDelay=100)
    #     z80.data = ascii_to_7seg[symbol]
    #     tt.clock_project_once(msDelay=100)
    #     tt.clock_project_once(msDelay=100)
    #     tt.clock_project_once(msDelay=100)
    #     z80.data = ascii_to_7seg[symbol]
    #     tt.clock_project_once(msDelay=100)
    #     tt.clock_project_once(msDelay=100)
    #     tt.clock_project_once(msDelay=100)

    # while True:
    #     for s in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
    #         display(s)
    #     time.sleep_ms(1000) 

