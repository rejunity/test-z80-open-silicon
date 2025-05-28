# Test FOSS Z80 replica on Tiny Tapeout 07

This is a testing code for [FOSS Z80 silicon](https://github.com/rejunity/z80-open-silicon) on [Tiny Tapeout 07](https://tinytapeout.com/runs/tt07). Tests are written in MicroPython and will run from the RP2040 microcontroller situated on the Tiny Tapeout base board.

## Requirements

NOTE: this all assumes you're running a Tiny Tapeout 7 demoboard, with [the SDK](https://github.com/TinyTapeout/tt-micropython-firmware/) and [MicroPython](https://www.micropython.org) installed.

On a host machine you will need [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) tool that usually comes with MicroPython installation. Older `mpremote` versions have a bit funky behavior, so you might need to upgrade it to _1.24.1_ or later version!

If `mpremote` is missing on your host machine, install it with:
```
pip install mpremote
```

## Install tests on Tiny Tapeout board
Connect your Tiny Tapeout 7 demoboard to you host machine via USB cable. Installation basically involves copying over the `tt_um_rejunity_z80` directory onto the micropython file system under `examples/` situated on a Tiny Tapeout 7 demoboard and accessbile to RP2040 microcontroller.

```
mpremote cp -r tt_um_rejunity_z80 :/examples/
```

## Run

Connect to your board from the host machine:
```
mpremote reset
mpremote
```

Once connection initiated, type:
```
import examples.tt_um_rejunity_z80.demo as demo

demo.hello()

```

Couple of other small programs included:
```
demo.prog_rom() # RP2040 emulates ROM, flashes LED with text

demo.prog_ram() # RP2040 emulates RAM, pushes vales on stack and prints them in the mpremote console

```


## Z80 Mircopython API

Example use:
```
from examples.tt_um_rejunity_z80.setup import setup
setup(tt) # Activate Z80 project on your TinyTapeout board

from examples.tt_um_rejunity_z80.z80 import Z80
z80 = Z80(tt) # Initialize Z80 wrapper

z80.data = 0 # NOP
print(z80.addr) # prints 0
tt.clock_project_once() # takes 4 cycles to execute NOP
tt.clock_project_once() # and advance PC by 1
tt.clock_project_once()
tt.clock_project_once()
tt.clock_project_once() # new PC will be set on adress bus
print(z80.addr) # prints 1

z80.dump() # prints control signals and address bus
```
