# Constant current, variable voltage

from eez import scpi
from utime import ticks_ms, ticks_diff

# change the voltage
def adjust_voltage():
    global voltage, is_on
    value = scpi('DISP:INP? "Enter Voltage",NUMB,VOLT,0,40,0')
    if not value is None:
        voltage = value
        if is_on:
            scpi("VOLT " + str(voltage))

# change the current
def adjust_current():
    global current, is_on
    value = scpi('DISP:INP? "Enter Current",NUMB,AMPE,0,5,0')
    if not value is None:
        current = value
        if is_on:
            scpi("CURR " + str(current))

# change timer start value
def adjust_timer():
    global timer
    if not is_on:
        value = scpi('DISP:INP? "Enter Seconds",NUMB,SECO,0.0,60.0,0.0')
        if not value is None:
            timer = value

# reset timer
def reset_timer():
    global countdown, timer
    countdown = timer
    
def start():
    global voltage, current, is_on, status_text, countdown, timer, use_timer, prev_tick
    scpi("INST CH1")
    if not is_on:
        try:
            scpi("OUTP ON")
        except:
            scpi('DISP:ERROR "External voltage detected!"')
        else:
            scpi("VOLT " + str(voltage))
            scpi("CURR " + str(current))
            is_on = True
            status_text = "Stop"
            if timer > 0.0:
                countdown = timer
                use_timer = True
            else:
                use_timer = False
    else:
        scpi("OUTP OFF")
        is_on = False
        status_text = "Start"
        countdown = 0.0
        use_timer = False

def main():
    # defaults
    global voltage, current, is_on, status_text, timer, current_draw, countdown, use_timer, voltage_actual, timer_on
    voltage = 0.0
    voltage_actual = 0.0
    current = 0.0
    current_draw = 0.0
    timer = 0.0
    countdown = 0.0
    prev_tick = -5.1
    use_timer = False
    is_on = False
    timer_on = False
    status_text = "Start"
    
    # Save state and set in known (default) state.  
    scpi("*SAV 10")
    scpi("MEM:STATE:FREEZE ON")
    scpi("*RST")
    
    # From now on we always restore the state in case of an error.  
    try:
        scpi("DISP:DIAL:OPEN \"Scripts/CCVV.res\"" )
        scpi('INST CH1')
        while True:
            # main loop
            # update measurements
            if is_on:
                current_draw = float(scpi('MEAS:CURR? CH1'))
                voltage_actual = float(scpi('MEAS? CH1'))
                
                if current_draw > 0.001:
                    timer_on = True
                else:
                    timer_on = False
                    reset_timer()
                
                if prev_tick > -5.0 and use_timer and timer_on:
                    countdown -= ticks_diff(ticks_ms(), prev_tick) * 0.001
                prev_tick = ticks_ms()
            else:
                current_draw = 0.0
                voltage_actual = voltage
                prev_tick = -5.1
                timer_on = False
                
            # shut off if timer ends    
            if is_on and countdown < 0.0:
                start()
                
            # update displays
            scpi('DISP:DIAL:DATA "voltage",FLOAT,VOLT,' + str(voltage))
            scpi('DISP:DIAL:DATA "voltage_actual",FLOAT,VOLT,' + str(voltage_actual))
            scpi('DISP:DIAL:DATA "current",FLOAT,AMPE,' + str(current))
            scpi('DISP:DIAL:DATA "current_draw",FLOAT,AMPE,' + str(current_draw))
            scpi('DISP:DIAL:DATA "timer",FLOAT,SECO,' + str(timer))
            scpi('DISP:DIAL:DATA "countdown",FLOAT,SECO,' + str(countdown))
            scpi('DISP:DIAL:DATA "status_text",STR,' + status_text)
            
            # parse actions
            action = scpi("DISP:DIALOG:ACTION? 0.1")
            if action == "adjust_voltage":
                adjust_voltage()
            elif action == "adjust_current":
                adjust_current()
            elif action == "adjust_timer":
                adjust_timer()
            elif action == "start":
                start()
            elif action == "reset_timer":
                reset_timer()
            elif action == "close_script" or action == 0:
                break
      
    finally:
        # Turn off channels, etc.
        scpi("OUTP 0")
        scpi("DISP:DIAL:CLOSE")
        scpi("*RCL 10")
        scpi("MEM:STATE:FREEZE OFF")

main()
