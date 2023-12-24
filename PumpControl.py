#!/usr/bin/python3.9.6
import RPi.GPIO as GPIO
import time
import board
import busio
from adafruit_ads1x15 import ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from datetime import datetime
import csv

class PumpControl:
    def __init__(self, 
                desired_number_of_trials: float,
                desired_pressure: float,
                desired_inflate_time: float,
                desired_hold_time: float,
                desired_deflate_time: float,
                desired_time_between_trials: float):
        
        ### Trial Settings ###
        self.desired_number_of_trials = desired_number_of_trials
        self.desired_pressure = desired_pressure
        self.desired_inflate_time = desired_inflate_time
        self.desired_hold_time = desired_hold_time
        self.desired_deflate_time = desired_deflate_time
        self.desired_time_between_trials = desired_time_between_trials
        
        # Set channel to pin number for BOARD
        #InflateChannel = 33
        #DeflateChannel = 32
        #ValveChannel = 13

        # Set channel to socket code (GPIO21) for BCM
        self.InflateChannel = 13
        self.DeflateChannel = 12
        self.ValveChannel = 27

        ### GPIO setup ###
        # BOARD chooses channels by printed numbers on RPi, i.e. 40
        #GPIO.setmode(GPIO.BOARD)

        # BCM chooses channels by Broadcom SOC channel, i.e. GPIO21
        # This project uses a module that sets mode for BCM. No other format is possible.
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.InflateChannel, GPIO.OUT)
        GPIO.setup(self.DeflateChannel, GPIO.OUT)
        GPIO.setup(self.ValveChannel, GPIO.OUT)



        ### ADC Control Functions ###
        # Guide - https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c)
        # ADS gain is not used, so it is set to the default of 1
        self.ads.gain = 1

        # ADS mode set to single stream
        self.ads.mode = ADS.Mode.SINGLE
        # TODO: Offset is calculated at initialization to determine OpAmp bias
        #self.ads_offset = AnalogIn(self.ads, ADS.P0).voltage



        ### Data Logging ###
        # 2 dimensional array that stores device activity for debugging
        self.activity_log = [['Time', 'Object', 'Activity', 'Details']]

        # Define the inflation, deflation, and valve as FlowObject state machines
        # Control pin number and object name are passed to create the state machines
        self.inflation_pump = self.FlowObject(self.InflateChannel, 'inflation_pump')
        self.deflation_pump = self.FlowObject(self.DeflateChannel, 'deflation_pump')
        self.valve = self.FlowObject(self.ValveChannel, 'valve')

    ### File Handling ###
    class FileHandler:
        # Data source indicates what generated the data being written to the file.
        # Default is set to pressure
        def __init__(self, data_source: str = "Log_") -> None:
            # File name is source + current time (YYYY-MM-DD_HH_mm_ss)
            # ex. "pressure_2023-2-19_11-32-55.csv"
            self.__file_name = data_source + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
        
        def write_session(self, output: list[list]) -> None:
            with open(self.__file_name, 'w') as file:
                writer = csv.writer(file)
                for row in output:
                    writer.writerow(row)

        def read_file(self):
            with open(self.__file_name, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    print('#' + str(reader.line_num) + ' ' + str(row))



    ### Flow Control State Machines ###
    # FlowObject holds the logic for enabling and disabling the pumps and valves
    class FlowObject:
        
        # When creating a FlowObject, the corresponding pin must be passed.
        def __init__(self, pin: int, name: str) -> None:
            # Input: int (Pin number), str (name of FlowObject)
            # Return: None
            self.__state = False # False = OFF/OPEN, True = ON/CLOSED
            self.__pin = pin
            self.__name = name

        # Set the desired state of the pump or valve
        def set_state(self, state: bool) -> list:
            # Input: boolean (flow state)
            # Return: None
            self.__state = state
            return self.set_action()

        # Get the current state of the pump or valve
        def get_state(self) -> bool:
            # Input: None
            # Return: boolean (current flow state)
            return self.__state

        # Apply the current state to the pump or valve
        def set_action(self) -> list:
            # Input: None
            # Return: None
            global activity_log
            if not self.__state:
                GPIO.output(self.__pin, GPIO.LOW)
                return [datetime.now().strftime("%H:%M:%S"), "Turn off " + self.__name]
            else:
                GPIO.output(self.__pin, GPIO.HIGH)
                return [datetime.now().strftime("%H:%M:%S"), "Turn on " + self.__name]

    # Trigger emergency shutoff of pumps, opens valves to vent system
    def emergency_shutoff(self) -> None:
        # Input: None
        # Return: None
        self.log_activity([datetime.now().strftime("%H:%M:%S"), "Emergency Shutoff"])
        self.log_activity(self.inflation_pump.set_state(False)) # False = OFF
        self.log_activity(self.deflation_pump.set_state(False))
        self.log_activity(self.valve.set_state(False))
        GPIO.cleanup()



    ### Pressure Aware Functions ###
    def raise_pressure(self, target_pressure: float) -> None:
        # Input: float 
        # Return: None
        # Turn on inflation pump while current pressure below threshold
        self.log_activity([datetime.now().strftime("%H:%M:%S"), "Raise Pressure Start"])
        while self.get_pressure() < target_pressure:
            current_pressure = self.get_pressure()
            print(current_pressure)
            self.log_activity(self.deflation_pump.set_state(False)) # Ensure deflation pump is off
            if not self.inflation_pump.get_state():
                self.log_activity(self.inflation_pump.set_state(True))
        self.log_activity(self.inflation_pump.set_state(False))
        print(self.get_pressure())
        self.log_activity([datetime.now().strftime("%H:%M:%S"), "Raise Pressure End"])

    def lower_pressure(self, target_pressure: float) -> None:
        # Input: float 
        # Return: None
        # Turn on inflation pump while current pressure below threshold
        self.log_activity([datetime.now().strftime("%H:%M:%S"), "Lower Pressure Start"])
        while self.get_pressure() > target_pressure:
            current_pressure = self.get_pressure() 
            print(current_pressure)
            self.log_activity(self.inflation_pump.set_state(False)) # Ensure inflation pump is off
            if not self.deflation_pump.get_state():
                self.log_activity(self.deflation_pump.set_state(True))
        print(self.get_pressure())
        self.log_activity(self.deflation_pump.set_state(False))
        self.log_activity([datetime.now().strftime("%H:%M:%S"), "Lower Pressure End"])
        
    def inflation_line_pressure(self, target_pressure: float, inflate_time_elapsed: float, desired_inflate_time: float) -> float:
        ## finds slope of inflation by dividing target pressure by total inflation time, then multiplies
        ## by current time so the function can return what the pressure should be along the line
        return ((target_pressure // desired_inflate_time) * inflate_time_elapsed)

    def deflation_line_pressure(self, target_pressure: float, deflate_start_time: float, desired_deflate_time: float) -> float:
        ## finds slope of deflation by dividing target pressure by total inflation time, then multiplies
        ## by current time. This value is how much the pressure should have dropped in the time elapsed, this is then
        ## subtracted from the target pressure to provide a slope downward rather than upward like inflation_line_pressure
        return (target_pressure - ((target_pressure // desired_deflate_time) * (time.perf_counter() - deflate_start_time)))



    ### Pressure Sensor Querying Function ###
    def get_pressure(self) -> float:
        # Input: None
        # Return: Float (in mmHg)
        chan = AnalogIn(self.ads, ADS.P0)

        # Adds current pressure, timestamp, and voltage to pressure log
        self.log_activity([datetime.now().strftime("%H:%M:%S"), chan.voltage, chan.voltage//0.1067])

        #TODO: Fine tune ads_offset to obtain correct value at start
        #return ((chan.voltage + ads_offset) * 9372)
        return ((chan.voltage + 0.0042) * 9372)
    # Example Output: 1.61679
    # Pressure sensor outputs 0.1067 mV per mmHg
    # Multiplier is set at 1/0.1067 * 1000, or 9372, to turn the ratio into mmHG per V because the ADC returns Volts, not mV.
    # ads_offset is an offset to counteract bias introduced by an op amp, around 4-6 mV
    #

    # 300 mmHg should output ~31.997 mV



    ### Input Sanitization ###
    # Ensures that user input is numeric, not alphabetic
    def input_sanitizer(self, response: str) -> float:
        # Input: String (raw user input)
        # Return: Float (numerical user input)
        if response.isnumeric():
            return float(response)
        else:
            # If response is numeric, function will continue asking recursively until an adequate number is provided
            return self.input_sanitizer(input("Please enter numbers only (Ex. 6, 400, 25.43) without any letters or special characters."))

    ### Logging Function ###
    def log_activity(self, entry: list):
        self.activity_log.append(entry)

    def start_trials(self):
        try:
            ### Enters user input to activity log ###
            self.log_activity([datetime.now().strftime("%H:%M:%S"), "Number of Trials", str(self.desired_number_of_trials)])
            self.log_activity([datetime.now().strftime("%H:%M:%S"), "Target Pressure", str(self.desired_pressure)])
            self.log_activity([datetime.now().strftime("%H:%M:%S"), "Desired inflate time", str(self.desired_inflate_time)])
            self.log_activity([datetime.now().strftime("%H:%M:%S"), "Desired hold time", str(self.desired_hold_time)])
            self.log_activity([datetime.now().strftime("%H:%M:%S"), "Desired deflate time", str(self.desired_deflate_time)])
            self.log_activity([datetime.now().strftime("%H:%M:%S"), "Time between Trials", str(self.desired_time_between_trials)])

            ## Total trial time equation. 
            total_trial_time = self.desired_number_of_trials * (self.desired_inflate_time + self.desired_hold_time + self.desired_deflate_time) + (self.desired_time_between_trials * (self.desired_number_of_trials - 1))
            
            start_time = time.perf_counter()
            while (time.perf_counter() - start_time) < total_trial_time:            
                ## Inflation cycle. Starting time for inflation is recorded, and a function is called to compare current pressure
                ## to desired pressure at the current time. While loop keeps this running for as long as desired inflate time
                ## has not been reached
                inflate_start_time = time.perf_counter()
                while ((time.perf_counter() - self.desired_inflate_time - inflate_start_time) < 0):
                    self.raise_pressure(self.inflation_line_pressure(self.desired_pressure, (time.perf_counter() - inflate_start_time), self.desired_inflate_time))
                
                self.log_activity([datetime.now().strftime("%H:%M:%S"), "Actual inflate time", str(time.perf_counter() - inflate_start_time)])

                ## While loop essentially waits the program for the hold time requested            
                hold_start_time = time.perf_counter()
                while ((time.perf_counter() - hold_start_time) < self.desired_hold_time):
                    print("Holding at ", self.get_pressure())

                self.log_activity([datetime.now().strftime("%H:%M:%S"), "Actual hold time", str(time.perf_counter() - hold_start_time)])

                ## Deflation cycle. Essentially the same as inflation cycle            
                deflate_start_time = time.perf_counter()
                while ((time.perf_counter() - self.desired_deflate_time - deflate_start_time) < 0):
                    self.lower_pressure(self.deflation_line_pressure(self.desired_pressure, deflate_start_time, self.desired_deflate_time))
                
                self.log_activity([datetime.now().strftime("%H:%M:%S"), "Actual deflate time", str(time.perf_counter() - deflate_start_time)])    
        except KeyboardInterrupt:
            self.emergency_shutoff()
            
        except:
            self.emergency_shutoff()

        self.emergency_shutoff()

        log_file = self.FileHandler()
        log_file.write_session(self.activity_log)
        log_file.read_file()