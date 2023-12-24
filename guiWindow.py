import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.messagebox import askyesno
import threading, time
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#from PumpControl import PumpControl
from PumpControlTester import PumpControlTester as PumpControl

class GuiWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        ### Main window ###
        self.title('Automated Blood Pressure Occlusion')
        self.geometry('800x480')
        self.resizable(False, False)
        self.config(cursor='arrow', bg='#eeebe2')

        # Frames that separate functions within the main window
        self.settings_frame = ttk.Frame(self)
        self.output_frame = ttk.Frame(self)
        self.output_frame.place(relx=0.48, rely=0.38, relheight=0.60, relwidth=0.5, bordermode='ignore')


    # Positional settings used for all widgets
        options = {'padx': 0, 'pady': 0, 'sticky':'W'}

        ### State variables ###
        # This is used to allow the GUI to continue refreshing while pumps are operating
        # Which in turn allows the GUI to interrupt pump operations
        self.running = False

        # Current trial variables that are updated during the cycle
        self.pressure: list[float] = [0.0]
        self.elapsed_time: list[float] = [0.0]

        # Shows status of trial program
        self.trial_status = tk.StringVar(value='Ready')
        self.current_pressure = tk.DoubleVar(value=0.0)
        self.current_time = tk.DoubleVar(value=0.0)

        # Current save directory
        self.directory = tk.StringVar(value='~/Desktop')

        # matplotlib objects
        # TODO: Fix graph constraints
        self.fig, self.axis = plt.subplots(figsize=(5,3.6), dpi=80)
        self.fig.set_facecolor('#eeebe2')
        self.axis.grid(color='darkgrey', alpha=0.65, linestyle='-')
        self.axis.set_facecolor('#eeebe2')
        self.axis.margins(0)
        self.axis.set_xlabel("Number of Samples")
        self.axis.set_ylabel("Pressure (mmHg)")
        #self.animation = FuncAnimation(self.fig, self.animate, interval=400, cache_frame_data=False)
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.99, top=0.99)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.output_frame)
        self.canvas.get_tk_widget().grid(column=0, row=5, **options)

        ### Settings Labels ###
        #label_settings = ttk.Label(self.settings_frame, text='Trial Parameters', bg='grey', font=('Arial', 16, 'bold'))
        self.Frame1 = ttk.Frame(self)
        self.Frame1.place(relx=0.01, rely=0.01, relheight=0.1, relwidth=0.44, bordermode='ignore')
        self.Frame1.configure(relief='solid')


        temps = ttk.Style(self.Frame1)
        temps.configure('TFrame', background='GREY')
        temps.configure('Custom.TLabel', background='grey', relief='flat', foreground='white', bordercolor='#ffffff')
        label_settings = ttk.Label(self.Frame1, text='Trial Parameters', style='Custom.TLabel', font=('Arial', 16, 'bold'))
        fram1options = {'padx': 50, 'pady': 10, 'sticky':'W'}
        label_settings.grid(column=0, row=0, columnspan=2, **fram1options)


        label_cycle = ttk.Label(self, text='Number of Cycles: ', font=('Arial', 10, 'bold'), foreground='dark blue')
        label_cycle.configure(background='#eeebe2')
        label_cycle.place(relx=0.01, rely=0.12, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_pressure = ttk.Label(self, text='Target pressure: (mmHg)', font=('Arial', 10, 'bold'), foreground='dark blue')
        label_pressure.configure(background='#eeebe2')
        label_pressure.place(relx=0.01, rely=0.2, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_inflate_time = ttk.Label(self, text='Target inflation time: (sec)', font=('Arial', 10, 'bold'),  foreground='dark blue')
        label_inflate_time.configure(background='#eeebe2')
        label_inflate_time.place(relx=0.01, rely=0.28, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_hold_time = ttk.Label(self, text='Hold time at max pressure: (sec)', font=('Arial', 10, 'bold'),  foreground='dark blue')
        label_hold_time.configure(background='#eeebe2')
        label_hold_time.place(relx=0.01, rely=0.36, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_deflate_time = ttk.Label(self, text='Target deflation time: (sec)', font=('Arial', 10, 'bold'),  foreground='dark blue')
        label_deflate_time.configure(background='#eeebe2')
        label_deflate_time.place(relx=0.01, rely=0.44, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_between_time = ttk.Label(self, text='Rest time between cycles: (sec)', font=('Arial', 10, 'bold'),  foreground='dark blue')
        label_between_time.configure(background='#eeebe2')
        label_between_time.place(relx=0.01, rely=0.52, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_start_instructions = ttk.Label(self, text="Press the START button to begin trials.\n", font=('Arial', 10, 'bold'),  foreground='dark blue')
        label_start_instructions.configure(background='#eeebe2')
        label_start_instructions.place(relx=0.01, rely=0.60, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_stop_instructions = ttk.Label(self, text="Press the STOP button to halt trials.\n", font=('Arial', 10, 'bold'), foreground='dark blue')
        label_stop_instructions.configure(background='#eeebe2')
        label_stop_instructions.place(relx=0.01, rely=0.68, relheight=0.05, relwidth=0.35, bordermode='ignore')

        # drawing a vertical line

        # TODO: Customize RPI to have UDEV rule to automent
        # /etc/fstab addition to not need sudo for the copy: /dev/sda1 /mnt auto defaults,noauto,user,x-systemd.automount 0 0
        #label_choose_directory = ttk.Label(self.settings_frame, text='Choose a directory to save pressure logs.\nIf using a USB, please insert before selecting directory.')
        #label_choose_directory.grid(column=0, row=9, **options)

        ### Output Labels ###
        label_current_pressure = ttk.Label(self, text='Current Pressure: ', font=('Arial', 10, 'bold'), foreground='dark blue')
        label_current_pressure.configure(background='#eeebe2')
        label_current_pressure.place(relx=0.55, rely=0.12, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_current_pressure = ttk.Label(self, textvariable = self.current_pressure)
        label_current_pressure.configure(background='#eeebe2')
        label_current_pressure.place(relx=0.70, rely=0.12, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_current_time = ttk.Label(self, text='Elapsed Time: ', font=('Arial', 10, 'bold'), foreground='dark blue')
        label_current_time.configure(background='#eeebe2')
        label_current_time.place(relx=0.55, rely=0.20, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_current_time = ttk.Label(self, textvariable = self.current_time)
        label_current_time.configure(background='#eeebe2')
        label_current_time.place(relx=0.70, rely=0.20, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_current_time = ttk.Label(self, text= str('Trial Status:'), font=('Arial', 10, 'bold'), foreground='dark blue')
        label_current_time.configure(background='#eeebe2')
        label_current_time.place(relx=0.55, rely=0.28, relheight=0.05, relwidth=0.35, bordermode='ignore')

        label_current_time_state = ttk.Label(self, text= str(self.trial_status.get()))
        label_current_time_state.configure(background='#eeebe2')
        label_current_time_state.place(relx=0.7, rely=0.28, relheight=0.05, relwidth=0.35, bordermode='ignore')
        ### Buttons ###
        # Spin buttons allow for user input in a predetermined range

        # Number of Trials
        self.desired_number_of_trials = tk.StringVar(value='3')
        trials_spin_button = ttk.Spinbox(self,
                                            from_ = 0, to = 30,
                                            textvariable = self.desired_number_of_trials,
                                            state='readonly',
                                            width=7,
                                            background='#ffffff',
                                           foreground='#000000',
                                            wrap=True)
        trials_spin_button.place(relx=0.35, rely=0.13, relheight=0.04, relwidth=0.1, bordermode='ignore')


        # Set focus to first spin button on program start
        trials_spin_button.focus()

        # Desired pressure
        self.desired_pressure = tk.StringVar(value='250')
        pressure_spin_button = ttk.Spinbox(self,
                                            from_ = 150, to = 360,
                                            values = ('150', '155', '160', '165','170', '175', '180', '185', '190','195',
                                            '200', '205', '210', '215', '220','225', '230', '235', '240', '245', '250'),
                                            textvariable = self.desired_pressure,
                                            state='readonly',
                                            width=7,
                                            wrap=True)
        pressure_spin_button.place(relx=0.35, rely=0.21, relheight=0.04, relwidth=0.1, bordermode='ignore')

        # Desired inflate time
        self.desired_inflate_time = tk.StringVar(value='2')
        inflate_spin_button = ttk.Spinbox(self,
                                            from_ = 1, to = 20,
                                            textvariable = self.desired_inflate_time,
                                            state='readonly',
                                            width=7,
                                            wrap=True)
        inflate_spin_button.place(relx=0.35, rely=0.29, relheight=0.04, relwidth=0.1, bordermode='ignore')

        # Desired hold time at target pressure
        self.desired_hold_time = tk.StringVar(value='5')
        hold_spin_button = ttk.Spinbox(self,
                                            from_ = 0, to = 360,
                                            values = ('0', '5', '10', '15', '20', '25', '30', '35', '40', '45', '50',
                                            '55', '60', '65', '70', '75', '80', '85', '90', '95', '100', '105', '110',
                                            '115', '120', '125', '130', '135', '140', '145', '150', '155', '160', '165',
                                            '170', '175', '180', '185', '190', '195', '200', '205', '210', '215', '220',
                                            '225', '230', '235', '240', '245', '250', '255', '260', '265', '270', '275',
                                            '280', '285', '290', '295', '300', '305', '310', '315', '320', '325', '330',
                                            '335', '340', '345', '350', '355', '360'),
                                            textvariable = self.desired_hold_time,
                                            state='readonly',
                                            width=7,
                                            wrap=True)
        hold_spin_button.place(relx=0.35, rely=0.37, relheight=0.04, relwidth=0.1, bordermode='ignore')

        # Desired deflate time
        self.desired_deflate_time = tk.StringVar(value='2')
        deflate_spin_button = ttk.Spinbox(self,
                                            from_ = 1, to = 20,
                                            textvariable = self.desired_deflate_time,
                                            state='readonly',
                                            width=7,
                                            wrap=True)
        deflate_spin_button.place(relx=0.35, rely=0.45, relheight=0.04, relwidth=0.1, bordermode='ignore')

        # Desired rest time between trials
        self.desired_time_between_trials = tk.StringVar(value='10')
        rest_spin_button = ttk.Spinbox(self,
                                            from_ = 0, to = 360,
                                            values = ('0', '5', '10', '15', '20', '25', '30', '35', '40', '45', '50',
                                            '55', '60', '65', '70', '75', '80', '85', '90', '95', '100', '105', '110',
                                            '115', '120', '125', '130', '135', '140', '145', '150', '155', '160', '165',
                                            '170', '175', '180', '185', '190', '195', '200', '205', '210', '215', '220',
                                            '225', '230', '235', '240', '245', '250', '255', '260', '265', '270', '275',
                                            '280', '285', '290', '295', '300', '305', '310', '315', '320', '325', '330',
                                            '335', '340', '345', '350', '355', '360'),
                                            textvariable = self.desired_time_between_trials,
                                            state='readonly',
                                            width=7,
                                            wrap=True)
        rest_spin_button.place(relx=0.35, rely=0.53, relheight=0.04, relwidth=0.1, bordermode='ignore')

        # Styling for START/STOP buttons
        s = ttk.Style()
        s.configure('button.TButton',
        background='#ffffff',
        #foreground='white',
        highlightthickness='20')
        s.map('button.TButton',
        foreground=[('disabled', 'grey'),
                    ('pressed', 'red'),
                    ('focus', 'green')],
        highlightcolor=[('focus', 'green'),
                        ('!focus', 'red')],
        relief=[('pressed', 'groove'),
                ('!pressed', 'ridge')])

        # START/STOP buttons
        self.start_button = ttk.Button(self,
                                  text = "START",
                                       cursor='hand2',
                                  command = self.confirm,
                                  style = 'button.TButton')
        self.start_button.place(relx=0.35, rely=0.595, relheight=0.06, relwidth=0.1, bordermode='ignore')

        self.stop_button = ttk.Button(self,
                                 text = "STOP",
                                      cursor='hand2',
                                 command = self.stop_trials,
                                 state='disabled',
                                 style = 'button.TButton')
        self.stop_button.place(relx=0.35, rely=0.67, relheight=0.06, relwidth=0.1, bordermode='ignore')
        # set the color of the button to red

        # Choose Directory Button
        # Will not work without a mouse. See line 72
        #self.directory_button = ttk.Button(self.settings_frame,
        #                                   text = "Open Dir",
        #                                   command = self.choose_directory,
        #                                   style = 'button.TButton')
        #self.directory_button.grid(column=1, row= 9, **options)


    ### Actions ###

    # Confirmation message
    def confirm(self):
        answer = askyesno(title = "Start trials?", message = f"""Number of trials: {self.desired_number_of_trials.get()}\nTarget pressure: {self.desired_pressure.get()}\nInflate time: {self.desired_inflate_time.get()}\nHold time: {self.desired_hold_time.get()}\nDeflate time: {self.desired_deflate_time.get()}\nReset time: {self.desired_time_between_trials.get()}\nStart trials with these settings?\n""")
        if answer:
            self.stop_button['state'] = 'enabled'
            self.pump_control = PumpControl(float(self.desired_number_of_trials.get()),
                                                    float(self.desired_pressure.get()),
                                                    float(self.desired_inflate_time.get()),
                                                    float(self.desired_hold_time.get()),
                                                    float(self.desired_deflate_time.get()),
                                                    float(self.desired_time_between_trials.get()))
            # Disable start button when trials have successfully begun
            self.start_button['state'] = 'disabled'
            self.trials = threading.Thread(target = self.start_trials)
            self.trials.start()
    # Directory chooser for CSV file output
    # Will not work without a mouse. See line 72
    #def choose_directory(self):
    #    self.directory.set(filedialog.askdirectory(initialdir = self.directory.get(), mustexist=True))

    def show_status(self, pressure:float, start_time:float):
            self.pressure.append(pressure)
            self.current_pressure.set(pressure)
            self.elapsed_time.append(time.perf_counter() - start_time)
            self.current_time.set(self.elapsed_time[-1])
            # Plotting
            self.axis.clear()
            self.axis.set_xlabel("Number of Samples")
            self.axis.set_ylabel("Pressure (mmHg)")
            self.axis.plot(self.pressure, label = 'Current Pressure')
            self.axis.legend(loc=0)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.output_frame)
            self.canvas.get_tk_widget().grid(column=0, row=5, padx= 5, pady= 5, sticky='W')

    def stop_trials(self):
        self.running = False
        # START/STOP buttons disabled when cancelling trials
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'disabled'


    def start_trials(self):
        # Set running marker to True
        self.running = True
        PC = self.pump_control
        ## Total trial time equation.
        # Total = (# of Trials)*(Inflate time + Hold time + Deflate time) + ((Rest time )*(# of Trials))
        total_trial_time = PC.desired_number_of_trials * (PC.desired_inflate_time + PC.desired_hold_time + PC.desired_deflate_time) + (PC.desired_time_between_trials * (PC.desired_number_of_trials - 1))
        self.pressure, self.elapsed_time = [0.0], [0.0]

        try:
            self.trial_status.set('Running Trials...')
            start_time = time.perf_counter()
            while self.running and (time.perf_counter() - start_time) < total_trial_time:
                ## Inflation cycle. Starting time for inflation is recorded, and a function is called to compare current pressure
                ## to desired pressure at the current time. While loop keeps this running for as long as desired inflate time
                ## has not been reached
                PC.log_activity([datetime.now().strftime("%H:%M:%S"), "Raise Pressure Start", PC.current_pressure])
                inflate_start_time = time.perf_counter()
                while self.running and ((time.perf_counter() - PC.desired_inflate_time - inflate_start_time) < 0):
                    PC.raise_pressure(PC.inflation_line_pressure(PC.desired_pressure, (time.perf_counter() - inflate_start_time), PC.desired_inflate_time))
                    self.show_status(PC.current_pressure, start_time)

                PC.log_activity([datetime.now().strftime("%H:%M:%S"), "Actual inflate time", str(time.perf_counter() - inflate_start_time)])
                self.show_status(PC.current_pressure, start_time)

                ## While loop essentially waits the program for the hold time requested
                hold_start_time = time.perf_counter()
                while self.running and ((time.perf_counter() - hold_start_time) < PC.desired_hold_time):
                    PC.get_pressure()
                    self.show_status(PC.current_pressure, start_time)

                PC.log_activity([datetime.now().strftime("%H:%M:%S"), "Actual hold time", str(time.perf_counter() - hold_start_time)])
                self.show_status(PC.current_pressure, start_time)

                ## Deflation cycle. Essentially the same as inflation cycle
                deflate_start_time = time.perf_counter()
                PC.log_activity([datetime.now().strftime("%H:%M:%S"), "Lower Pressure Start", PC.current_pressure])
                while self.running and ((time.perf_counter() - PC.desired_deflate_time - deflate_start_time) < 0):
                    PC.lower_pressure(PC.deflation_line_pressure(PC.desired_pressure, deflate_start_time, PC.desired_deflate_time))
                    self.show_status(PC.current_pressure, start_time)

                PC.log_activity([datetime.now().strftime("%H:%M:%S"), "Actual deflate time", str(time.perf_counter() - deflate_start_time)])
                self.show_status(PC.current_pressure, start_time)

                rest_start_time = time.perf_counter()
                while self.running and ((time.perf_counter() - rest_start_time) < PC.desired_time_between_trials):
                    self.show_status(PC.current_pressure, start_time)
        except:
            PC.emergency_shutoff
            self.trial_status.set("ERROR")

        PC.log_activity([datetime.now().strftime("%H:%M:%S"), 'All trials completed'])
        PC.emergency_shutoff
        log_file = PC.FileHandler()
        log_file.write_session(PC.activity_log)

        # Enable start button when trials have successfully completed
        self.start_button['state'] = 'enabled'
        self.stop_button['state'] = 'disabled'


        if self.running:
            self.trial_status.set('COMPLETE')
            self.running = False
        else:
            self.trial_status.set('HALTED')


# Initialize main window
root_window = GuiWindow()

# Start trial by pressing start button (Set to RETURN key during development)
# TODO: Tie stop button to self.running, and turn it to False when pressed
#root_window.bind_all('<space>', lambda event: root_window.confirm())

if __name__ == '__main__':
    root_window.mainloop()
