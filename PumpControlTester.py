#!/usr/bin/python3.9.6
import time
from datetime import datetime
import csv

class PumpControlTester:
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

        ### Test Variables ###
        # Only used for program debugging
        self.current_pressure = 0.0

        ### Data Logging ###
        # 2 dimensional array that stores device activity for debugging
        self.activity_log = [['Time', 'Object', 'Activity', 'Details']]

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

    # Trigger emergency shutoff of pumps, opens valves to vent system
    def emergency_shutoff(self) -> None:
        # Input: None
        # Return: None
        self.log_activity([datetime.now().strftime("%H:%M:%S"), "Emergency Shutoff"])

    def raise_pressure(self, target_pressure: float) -> None:
        # Input: float 
        # Return: None
        # Turn on inflation pump while current pressure below threshold
        while self.current_pressure < target_pressure:
            self.current_pressure += 1
            self.get_pressure

    def lower_pressure(self, target_pressure: float) -> None:
        # Input: float 
        # Return: None
        # Turn on inflation pump while current pressure below threshold
        while self.current_pressure > target_pressure:
            self.current_pressure -= 1
        self.get_pressure

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

        # Adds current pressure, timestamp, and voltage to pressure log
        self.log_activity([datetime.now().strftime("%H:%M:%S"), self.current_pressure, self.current_pressure*0.0001067])

        return self.current_pressure
    
    ### Logging Function ###
    def log_activity(self, entry: list):
        self.activity_log.append(entry)