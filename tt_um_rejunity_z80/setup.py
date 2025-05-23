
from ttboard.demoboard import DemoBoard

import ttboard.log as logging
log = logging.getLogger(__name__)

import ttboard.util.platform as platform

def setup(tt:DemoBoard):
    
    if tt.shuttle.run != 'tt07' and tt.shuttle.run != 'tt09' and tt.shuttle.run != 'ttihp0p2' and tt.shuttle.run != 'ttihp25a':
        log.error(f"Z80 isn't actually on shuttle {tt.shuttle.run}, sorry!")
        return False
    
    log.info("Selecting Z80 project")
    tt.shuttle.tt_um_rejunity_z80.enable()
    
    tt.reset_project(True)
    platform.set_RP_system_clock(126e6)
    # tt.clock_project_PWM(4e6)
    tt.clock_project_stop()
    for _ in range(20):
        tt.clock_project_once(msDelay=50)
    tt.reset_project(False)
    
    return True
