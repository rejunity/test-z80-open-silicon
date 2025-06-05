'''
Created on May 23, 2025

@author: ReJ aka Renaldas Zioma
'''

from ttboard.demoboard import DemoBoard
import ttboard.util.platform as platform

import ttboard.log as logging
log = logging.getLogger(__name__)

from examples.tt_um_rejunity_z80.z80 import Z80, Z80PIO
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
LD_mem_A    = 0x32
LD_A_B      = 0b01_111_000
LD_A_C      = 0b01_111_001
LD_A_D      = 0b01_111_010
LD_A_E      = 0b01_111_011
LD_A_H      = 0b01_111_100
LD_A_L      = 0b01_111_101
POP_BC      = 0xC1
POP_DE      = 0xD1
POP_HL      = 0xE1
POP_AF      = 0xF1
PUSH_BC     = 0xC5
PUSH_DE     = 0xD5
PUSH_HL     = 0xE5
PUSH_AF     = 0xF5
HALT        = 0x76
JP_nnnn     = 0xC3
RET         = 0xC9
DI          = 0xF3
EI          = 0xFB
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
# def op_LD(arg0, arg1, arg2=-1):
#     if isinstance(arg0, str) and if isinstance(arg1, str):

#     elif isinstance(arg0, str):
#         return op_LD_nnnn(arg0, arg1, arg2)
#     elif isinstance(arg1, str):
#         return op_LD_nnnn(arg0, arg1, arg2)

def op_JP_nnnn(hi, lo=-1):
    if lo < 0:
        lo = hi %  0x100
        hi = hi // 0x100
    return op([JP_nnnn, lo, hi])

def prog_rom(delay=100, direct=True, verbose=False):
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


# WIP: does not work yet!!!
# For some reason address bus seems does not seem to contain PC when HALTed
# TODO: Will try to use NMI instead of INT
# TODO: Maybe use Z80 loop to pause / busy wait between the "frames"
# import examples.tt_um_rejunity_z80.demo as demo; demo.prog_rom_pio(100000, 100, True)
def prog_rom_pio(sleep=1000, freq=100, verbose=False):
    tt = DemoBoard.get()
    if not setup(tt):
        return False 
    
    z80 = Z80PIO(tt, chip_frequency=freq*100)
    tt.clock_project_PWM(freq)

    text = "Z8o HELLO uorld."
    code = bytearray()
    code += op(EI)
    code += op([0xED, 0x56]) # IM1
    # code += op(0x46) # IM0
    # code += op(0x56) # IM1
    code += op_JP_nnnn(0x0040)
    while len(code) < 0x38:
        code += op(NOP)
    code += op([0xED, 0x4D]) # RETI
    while len(code) < 0x40:
        code += op(NOP)
    for c in text:
        code += op_JP_nnnn(hi=ascii_to_7seg[c], lo=len(code)+3)
        code += op(EI)
        code += op(HALT)
    # assert len(code) == len(text)*4 + 1
    code += op_JP_nnnn(0)
    code_end = len(code)

    rom = bytearray(0x100)
    assert len(code) <= len(rom)
    for n in range(len(code)):
        rom[n] = code[n]
    addr_mask = len(rom)-1

    # rom[]

    tt.ui_in[3:0] = 0b1111
    ff_int = 0
    while True:
        # if z80.update(rom=rom, addr_mask=addr_mask, verbose=verbose) & addr_mask >= code_end:
        #     break
        z80.run(ram=rom, addr_mask=addr_mask, verbose=verbose)
        tt.ui_in[7:6] = 0b01
        time.sleep_us(sleep)
        # tt.uio_oe_pico.value = 255
        # tt.uio_in = 0xFF # 0xC9
        tt.ui_in[7:6] = 0b01
        tt.ui_in[1] = ff_int
        tt.ui_in[7:6] = 0b01
        # ff_int = not ff_int

    # tt.clock_project_once()

# import examples.tt_um_rejunity_z80.demo as demo; demo.prog_ram_pio(100, True)
def prog_ram_pio(freq=100, verbose=False):
    tt = DemoBoard.get()
    if not setup(tt):
        return False 
    
    z80 = Z80PIO(tt, chip_frequency=freq*100)
    tt.clock_project_PWM(freq)

    code = bytearray()
    code += op_LD_nnnn("BC", 0xCAFE)
    code += op_LD_nnnn("DE", 0xDECF)
    code += op_LD_nnnn("HL", 0x1337)
    code += op_LD_nnnn("SP", 0x0000)
    # code += op(LD_A_B)                  
    # code += op([LD_mem_A, 0x00, 0x80])
    # code += op(LD_A_C)                  
    # code += op([LD_mem_A, 0x01, 0x80])
    # code += op(0x77) # LD (HL),A
    # code += op(0x70) # LD (HL),B
    # code += op(0x71) # LD (HL),C
    code += op(PUSH_HL)
    code += op(PUSH_HL)
    code += op(PUSH_HL)
    code += op(PUSH_HL)
    code += op(PUSH_BC)
    code += op(PUSH_DE)
    code += op(HALT)

    print(code)

    ram = bytearray(0x100)
    for n in range(len(code)):
        ram[n] = code[n]

    tt.ui_in[3:0] = 0b1111
    z80.run(ram=ram, addr_mask=0xFF, verbose=verbose) # run until HALT

    print("RAM 0xE0..0xFF: ", [hex(x) for x in ram[-16:]])
    assert ram[-16:] == bytearray([0,0,0,0, 0xCF,0xDE, 0xFE,0xCA,   0x37,0x13, 0x37,0x13, 0x37,0x13, 0x37,0x13])

    print("Success!")


def prog_ram(delay=1, verbose=False):
    tt = DemoBoard.get()
    if not setup(tt):
        return False 
    
    z80 = Z80(tt)

    code = bytearray()
    code += op_LD_nnnn("BC", 0xCAFE)
    code += op_LD_nnnn("DE", 0xDECF)
    code += op_LD_nnnn("HL", 0x1337)
    code += op_LD_nnnn("SP", 0x0000)
    code += op(PUSH_HL)
    code += op(PUSH_HL)
    code += op(PUSH_HL)
    code += op(PUSH_HL)
    code += op(PUSH_BC)
    code += op(PUSH_DE)
    code += op(RET)

    print(code)

    ram = bytearray(0x100)
    for n in range(len(code)):
        ram[n] = code[n]

    while True:
        if verbose:
            z80.dump()

        ram_addr = z80.addr % len(ram)

        if z80.WR and z80.MREQ:
            tt.uio_oe_pico = 0
            ram[ram_addr] = z80.data
            print(f"{int(z80.data):02x} -> [{z80.addr:04x}]")
        else:
            if z80.M1 and ram[ram_addr] == RET:
                break
            tt.uio_oe_pico = 255
            if z80.RD and z80.MREQ:
                z80.data = ram[ram_addr]
                print(f"      [{z80.addr:04x}] {'=' if z80.M1 else '-'}> {int(z80.data):02x}")
        tt.clock_project_once(msDelay=delay)
    assert ram[-16:] == bytearray([0,0,0,0, 0xCF,0xDE, 0xFE,0xCA,   0x37,0x13, 0x37,0x13, 0x37,0x13, 0x37,0x13])

    # print(ram[0x1_0000-16:0x1_0000-1])
    print("RAM 0xE0..0xFF: ", [hex(x) for x in ram[-16:]])

# import examples.tt_um_rejunity_z80.demo as demo; demo.cpm("/hello.com") #verbose=True)
def cpm(com_filename, ram_size=0x4000, verbose=False, reboot=True):
    tt = DemoBoard.get()
    if reboot:
        if not setup(tt):
            return False

    z80 = Z80(tt)

    code = bytearray()
    code += op_JP_nnnn(0x100)           # CALL $0000 jump here - CP/M entree point to warm boot
    code += op(NOP)
    code += op(NOP)
    assert(len(code) == 5)
    code += op(NOP)                     # CALL $0005 jumps here - CP/M entree point to BDOS
    code += op(NOP)                     # Keep bytes at address $0006 and $0007 as zero!
    code += op(NOP)                     # CP/M contains top of the user memory at address $0006
    code += op(LD_A_D)                  
    code += op([LD_mem_A, 0x02, 0x00])
    code += op(LD_A_E)
    code += op([LD_mem_A, 0x01, 0x00])
    code += op(LD_A_C)
    code += op([LD_mem_A, 0x00, 0x00])  # Writing to $0000 triggers handling of BDOS call by emulation environment
    code += op(RET)
    assert(len(code) < 0x100)

    # Emulate CP/M bdos CALL 5 functions:
    #  2 - output character on screenZ80 instruction exerciser
    #  9 - output $-terminated string to screen
    def emulate_bdos(ram):
        if ram[0] == 2: # print char
            print(chr(ram[1]), end='')
        elif ram[0] == 9: # print str terminated by $
            ptr = ram[2]*256 + ram[1]
            n = 0
            while chr(ram[ptr]) != '$' or n > 80: # protect against non-terminated strings
                print(chr(ram[ptr]), end='')
                ptr = (ptr + 1) % len(ram)
                n += 1

    f = open(com_filename, mode='rb')    
    loaded_code = f.read()
    f.close()

    ram = bytearray(ram_size)
    for n in range(len(code)):
        ram[n] = code[n]
    for n in range(len(loaded_code)):
        ram[0x0100+n] = loaded_code[n]

    if verbose:
        print(ram[0:16])
        print(ram[0x100:0x120])

    running = False
    while True:
        if verbose == "super":
            z80.dump()

        ram_addr = z80.addr % len(ram)

        if z80.M1:
            if ram_addr == 0:
                if running:
                    break # finished the execution of COM file
            else:
                running = True

        # assert z80.WR != z80.RD
        if z80.WR and z80.MREQ:
            tt.uio_oe_pico = 0
            ram[ram_addr] = z80.data
            if verbose or verbose == "super":
                print(f"{int(z80.data):02x} -> [{z80.addr:04x}]")

            if ram_addr == 0:
                emulate_bdos(ram) # emulate the CP/M BDOS

        if z80.RD and z80.MREQ:
            tt.uio_oe_pico = 255
            z80.data = ram[ram_addr]
            if verbose or verbose == "super":
                print(f"      [{z80.addr:04x}] {'=' if z80.M1 else '-'}> {int(z80.data):02x}")

        tt.clock_project_once()


# import examples.tt_um_rejunity_z80.demo as demo; demo.cpm_pio("/hello.com", rp2040_freq=133_000_000)
def cpm_pio(com_filename, ram_size=0x4000, freq=100_000, freq_mul=40, rp2040_freq=133_000_000, verbose=False):
    tt = DemoBoard.get()
    if not setup(tt):
        return False

    code = bytearray()
    code += op_JP_nnnn(0x100)           # CALL $0000 jump here - CP/M entree point to warm boot
    code += op(NOP)
    code += op(NOP)
    assert(len(code) == 5)
    code += op(NOP)                     # CALL $0005 jumps here - CP/M entree point to BDOS
    code += op(NOP)                     # Keep bytes at address $0006 and $0007 as zero!
    code += op(NOP)                     # CP/M contains top of the user memory at address $0006
    code += op(LD_A_D)                  
    code += op([LD_mem_A, 0x02, 0x00])
    code += op(LD_A_E)
    code += op([LD_mem_A, 0x01, 0x00])
    code += op(LD_A_C)
    code += op([LD_mem_A, 0x00, 0x00])  # Writing to $0000 triggers handling of BDOS call by emulation environment
    code += op(RET)
    assert(len(code) < 0x100)

    # Emulate CP/M bdos CALL 5 functions:
    #  2 - output character on screenZ80 instruction exerciser
    #  9 - output $-terminated string to screen
    def emulate_bdos(ram):
        if ram[0] == 2: # print char
            print(chr(ram[1]), end='')
        elif ram[0] == 9: # print str terminated by $
            ptr = ram[2]*256 + ram[1]
            n = 0
            while chr(ram[ptr]) != '$' or n > 80: # protect against non-terminated strings
                print(chr(ram[ptr]), end='')
                ptr = (ptr + 1) % len(ram)
                n += 1

    f = open(com_filename, mode='rb')    
    loaded_code = f.read()
    f.close()

    ram = bytearray(ram_size)
    for n in range(len(code)):
        ram[n] = code[n]
    for n in range(len(loaded_code)):
        ram[0x0100+n] = loaded_code[n]

    if verbose:
        print(ram[0:16])
        print(ram[0x100:0x120])

    z80 = Z80PIO(tt, chip_frequency=freq*100)
    tt.clock_project_PWM(freq)
    platform.set_RP_system_clock(rp2040_freq)

    tt.ui_in[3:0] = 0b1111
    addr_mask = len(ram)-1
    while True:
        addr, flags = z80.run(ram=ram, addr_mask=addr_mask, verbose=verbose)
        m1 = (flags & 1) > 0
        rd = (flags & 8) > 0
        if   addr == 0 and rd:
            break
        elif addr == 0:
            emulate_bdos(ram) # emulate the CP/M BDOS

    print("Program finished execution!")
