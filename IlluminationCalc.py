"""
Copyright (C) 2025  YimingYang

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from LibConst import *
from LibFeed import Feed, FeedType
from LibAperture import Aperture, ApertureType
from LibCalc import CalculationType, Calculation
from LibTkExtension import LabelEntryPair, LabelPicklistPair, TracePlotWindow


# --------- BEGIN Create the Main Window ---------
# Create the main window
root = tk.Tk()
root.title("Illumination Calculator (C) 2025  YimingYang")
root.geometry("800x700")

# Create the main frame
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=1)
main_left_frame = ttk.Frame(main_frame)
main_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
main_right_frame = ttk.Frame(main_frame)
main_right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
# --------- END Create the Main Window ---------



# --------- BEGIN Initialize the Feed and Aperture Data Objects ---------
feed_data = Feed()
aperture_data = Aperture()
# --------- END Initialize the Feed and Aperture Data Objects ---------



# --------- BEGIN Initialize the Calculation Data Object ---------
calculation_data = Calculation()
# --------- END Initialize the Calculation Data Object ---------



# ---------- BEGIN Create the calculation setup frame ----------
calculation_frame = ttk.LabelFrame(main_right_frame, text="Calculation Setup")
calculation_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=tk_padx, pady=tk_pady, expand=1)
# Add calculation setup entries with radial buttons
calculation_type_frame = ttk.LabelFrame(calculation_frame, text="Type")
calculation_type_frame.pack(padx=tk_padx, pady=tk_pady, fill=tk.BOTH, expand=1)
calculation_type = tk.StringVar()
calculation_type.set(CalculationType.DirectCalc.value)
calculation_type_radios = []
for t in CalculationType:
    radio = ttk.Radiobutton(calculation_type_frame, text=t.value, variable=calculation_type, value=t.value)
    radio.pack(fill=tk.X, side=tk.TOP, expand=1)
    calculation_type_radios.append(radio)
# Add calculation parameter entries
calculation_parameter_frame = ttk.LabelFrame(calculation_frame, text="Parameters")
calculation_parameter_frame.pack(padx=tk_padx, pady=tk_pady, fill=tk.BOTH, expand=1)
# Each Sweep Variable (string) parameter is mapped to a picklist with entries from the feed and aperture parameters
# Each numeric parameter is mapped to a pair of label and entry
calculation_parameter_pairs = []
# If the parameter is changed, update the corresponding parameter in the Calculation object
def update_calculation_parameter_entry(event):
    for pair in calculation_parameter_pairs:
        if not isinstance(pair, LabelEntryPair):
            continue
        if event.widget == pair.entry:
            name = pair.label.cget('text')
            value = pair.entry.get()
            if calculation_data.update_parameter(name, value) == False:
                # If the value is invalid, reset the entry to the previous value
                pair.entry.delete(0, tk.END)
                pair.entry.insert(0, str(calculation_data.parameters[name]))
                print("Invalid value for {}".format(name))  # Debugging
            print("Updated {} to {}".format(calculation_data.parameters[name], calculation_data.parameters[name]))  # Debugging
            break
# If the parameter is changed, update the corresponding parameter in the Calculation object
def update_calculation_parameter_combobox(event):
    for pair in calculation_parameter_pairs:
        if not isinstance(pair, LabelPicklistPair):
            continue
        if event.widget == pair.picklist:
            name = pair.label.cget('text')
            value = pair.picklist.get()
            if calculation_data.update_parameter(name, value) == False:
                # If the value is invalid, reset the picklist to the previous value
                pair.picklist.set(calculation_data.parameters[name])
            break
# Update the calculation parameter entries when the calculation type changes
def update_calculation_parameter_gui(is_first_run=False):
    # Update the calculation type based on the radio button
    for radio in calculation_type_radios:
        if radio.instate(['selected']):
            # Ignore if the calculation type is not changed
            if calculation_data.type == CalculationType(radio.cget('text')) and not is_first_run:
                return
            calculation_data.update_type(CalculationType(radio.cget('text')))
            break
    # Rebuild the calculation parameter labels and entries based on the updated parameters
    for pair in calculation_parameter_pairs:
        pair.destroy()
    calculation_parameter_pairs.clear()
    for parameter in calculation_data.parameters:
        if isinstance(calculation_data.parameters[parameter], str):
            pickable_parameters = list(feed_data.parameters.keys()) + list(aperture_data.parameters.keys())
            pair = LabelPicklistPair(calculation_parameter_frame, parameter, "", pickable_parameters)
            idx = pickable_parameters.index(calculation_data.parameters[parameter])
            pair.picklist.current(idx)
            pair.picklist.bind("<<ComboboxSelected>>", update_calculation_parameter_combobox)
        else:
            pair = LabelEntryPair(calculation_parameter_frame, parameter, "")
            pair.entry.insert(0, str(calculation_data.parameters[parameter]))
            pair.entry.bind("<FocusOut>", update_calculation_parameter_entry)
        calculation_parameter_pairs.append(pair)

# Bind the update_calculation_parameter_gui function to the radio buttons
for radio in calculation_type_radios:
    radio.config(command=update_calculation_parameter_gui)

# Update the calculation parameter entries when the GUI is first created
update_calculation_parameter_gui(is_first_run=True)
# ---------- END Create the calculation setup frame ----------



# ---------- BEGIN Create the Calculation Command Frame ----------
# Create the calculation command frame
calculation_command_frame = ttk.LabelFrame(calculation_frame, text="Commands")
calculation_command_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=tk_padx, pady=tk_pady, expand=1)
# Progress Bar
progress_bar = ttk.Progressbar(calculation_command_frame, orient=tk.HORIZONTAL)
progress_bar.pack(side=tk.BOTTOM, fill=tk.X, expand=1, pady=tk_pady)
progress_bar['value'] = 0
# Command Button: Calculate from ttk.Button, Plot from ttk.Button
def calculate():
    print("Calculate and Plot")
    progress_bar['value'] = 0
    if calculation_data.type == CalculationType.DirectCalc:
        taper_efficiency, spillover_efficiency = calculation_data.calc_taper_and_spillover_efficiency_oneshot(feed_data, aperture_data)
        aperture_efficiency = taper_efficiency * spillover_efficiency
        # Create a messagebox from tkinter showing the results
        str_msg = "Taper Efficiency: {0:.2f}%\nSpillover Efficiency: {1:.2f}%\nTaper x Spillover Efficiency: {2:.2f}%".format(taper_efficiency * 100, spillover_efficiency * 100, aperture_efficiency * 100)
        progress_bar['value'] = 100
        progress_bar.update_idletasks()
        tk.messagebox.showinfo("Results", str_msg)
    elif calculation_data.type == CalculationType.Sweep1D:
        taper_efficiency, spillover_efficiency = calculation_data.sweep_taper_and_spillover_efficiencies_1d(feed_data, aperture_data, progressbar=progress_bar)
        aperture_efficiency = taper_efficiency * spillover_efficiency
        plot_window = TracePlotWindow(root)
        var_name = calculation_data.parameters['Sweep Variable']
        var_start = calculation_data.parameters['Sweep Start']
        var_end = calculation_data.parameters['Sweep Stop']
        var_step = calculation_data.parameters['Sweep Steps'] 
        var_linspace = np.linspace(var_start, var_end, var_step)
        plot_window.add_trace(var_linspace, taper_efficiency*100, "Taper Efficiency") # TODO: Make it Dash Line
        plot_window.add_trace(var_linspace, spillover_efficiency*100, "Spillover Efficiency") # TODO: Make it Dash Line
        plot_window.add_trace(var_linspace, aperture_efficiency*100, "Taper x Spillover Efficiency")
        plot_window.set_title("Efficiencies (%)")
        plot_window.set_x_label(var_name)
        progress_bar['value'] = 100
        progress_bar.update_idletasks()
        plot_window.show()
    elif calculation_data.type == CalculationType.Sweep2D:
        pass
    pass
calculate_button = ttk.Button(calculation_command_frame, text="Calculate and Plot", command=calculate)
calculate_button.pack(side=tk.TOP, fill=tk.X, expand=1)
# ---------- END Create the Calculation Command Frame ----------


# ---------- BEGIN Create the aperture frame ----------
aperture_frame = ttk.LabelFrame(main_left_frame, text="Aperture")
aperture_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=tk_padx, pady=tk_pady, expand=1)
# Add aperture type radio buttons from ApertureType
aperture_type_frame = ttk.LabelFrame(aperture_frame, text="Type")
aperture_type_frame.pack(padx=tk_padx, pady=tk_pady, fill=tk.BOTH, expand=1)
aperture_type = tk.StringVar()
aperture_type.set(ApertureType.Circular.value)
aperture_type_radios = []
for t in ApertureType:
    radio = ttk.Radiobutton(aperture_type_frame, text=t.value, variable=aperture_type, value=t.value)
    radio.pack(fill=tk.X, side=tk.TOP, expand=1)
    aperture_type_radios.append(radio)
# Add aperture parameter entries
aperture_parameter_frame = ttk.LabelFrame(aperture_frame, text="Parameters")
aperture_parameter_frame.pack(side=tk.LEFT, padx=tk_padx, pady=tk_pady, fill=tk.BOTH, expand=1)
# Each parameter is mapped to a pair of label and entry
aperture_parameter_label_entry_pairs = []

# If the parameter is changed, update the corresponding parameter in the Aperture object
def update_aperture_parameter(event):
    for pair in aperture_parameter_label_entry_pairs:
        entry = pair.entry
        label = pair.label
        if event.widget == entry:
            name = label.cget('text') # TODO: Reiterate the Unit of the selected parameter
            value = entry.get()
            if aperture_data.update_parameter(name, value) == False:
                # If the value is invalid, reset the entry to the previous value
                entry.delete(0, tk.END)
                entry.insert(0, str(aperture_data.parameters[name]))
            break

# Update the aperture parameter entries when the aperture type changes
def update_aperture_parameter_gui(is_first_run=False):
    # Update the aperture type based on the radio button
    for radio in aperture_type_radios:
        if radio.instate(['selected']):
            # Ignore if the aperture type is not changed
            if aperture_data.type == ApertureType(radio.cget('text')) and not is_first_run:
                return
            aperture_data.update_type(ApertureType(radio.cget('text')))
            break
    # Rebuild the aperture parameter labels and entries based on the updated parameters
    for pair in aperture_parameter_label_entry_pairs:
        pair.label.destroy()
        pair.entry.destroy()
        pair.destroy()
    aperture_parameter_label_entry_pairs.clear()
    for parameter in aperture_data.parameters:
        pair = LabelEntryPair(aperture_parameter_frame, parameter, "")
        pair.entry.insert(0, str(aperture_data.parameters[parameter]))
        pair.entry.bind("<FocusOut>", update_aperture_parameter)
        aperture_parameter_label_entry_pairs.append(pair)
    # Rebuild Calculation parameters based on the updated aperture parameters
    update_calculation_parameter_gui(is_first_run=True)

# Bind the update_aperture_parameter_gui function to the radio buttons
for radio in aperture_type_radios:
    radio.config(command=update_aperture_parameter_gui)

# Update the aperture parameter entries when the GUI is first created
update_aperture_parameter_gui(is_first_run=True)

# ---------- END Create the aperture frame ----------



# ---------- BEGIN Create the feed frame ----------

# Create the feed frame
feed_frame = ttk.LabelFrame(main_left_frame, text="Feed")
feed_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=tk_padx, pady=tk_pady, expand=1)

# Add feed type radio buttons from FeedType
feed_type_frame = ttk.LabelFrame(feed_frame, text="Type")
feed_type_frame.pack(padx=tk_padx, pady=tk_pady, fill=tk.BOTH, expand=1)
feed_type = tk.StringVar()
feed_type.set(FeedType.Cos_theta_q.value)
feed_type_radios = []
for t in FeedType:
    radio = ttk.Radiobutton(feed_type_frame, text=t.value, variable=feed_type, value=t.value)
    radio.pack(fill=tk.X, side=tk.TOP, expand=1)
    feed_type_radios.append(radio)

# Add feed parameter entries
feed_parameter_frame = ttk.LabelFrame(feed_frame, text="Parameters")
feed_parameter_frame.pack(padx=tk_padx, pady=tk_pady, fill=tk.BOTH, expand=1)
# Add one label-entry pair for each parameter
feed_parameter_label_entry_pairs = []

# If the parameter is changed, update the corresponding parameter in the Feed object
def update_feed_parameter(event):
    for pair in feed_parameter_label_entry_pairs:
        entry = pair.entry
        label = pair.label
        if event.widget == entry:
            name = label.cget('text')
            value = entry.get()
            if feed_data.update_parameter(name, value) == False:
                # If the value is invalid, reset the entry to the previous value
                entry.delete(0, tk.END)
                entry.insert(0, str(feed_data.parameters[name]))
            break
    # Refresh the feed parameter entries to update dependent values
    for pair in feed_parameter_label_entry_pairs:
        entry = pair.entry
        label = pair.label
        name = label.cget('text')
        entry.delete(0, tk.END)
        entry.insert(0, str(feed_data.parameters[name]))

# Update the feed parameter entries when the feed type changes
def update_feed_parameter_gui(is_first_run=False):
    # Update the feed type based on the radio button
    for radio in feed_type_radios:
        if radio.instate(['selected']):
            # Ignore if the feed type is not changed
            if feed_data.type == FeedType(radio.cget('text')) and not is_first_run:
                return
            feed_data.update_type(FeedType(radio.cget('text')))
            break
    # Rebuild the feed parameter labels and entries based on the updated parameters
    for pair in feed_parameter_label_entry_pairs:
        pair.label.destroy()
        pair.entry.destroy()
        pair.destroy()
    feed_parameter_label_entry_pairs.clear()
    for parameter in feed_data.parameters:
        pair = LabelEntryPair(feed_parameter_frame, parameter, "")
        pair.entry.insert(0, str(feed_data.parameters[parameter]))
        pair.entry.bind("<FocusOut>", update_feed_parameter)
        feed_parameter_label_entry_pairs.append(pair)
    # Rebuild Calculation parameters based on the updated feed parameters
    update_calculation_parameter_gui(is_first_run=True)

# Bind the update_feed_parameter_gui function to the radio buttons
for radio in feed_type_radios:
    radio.config(command=update_feed_parameter_gui)

# Update the feed parameter entries when the GUI is first created
update_feed_parameter_gui(is_first_run=True)
# ---------- END Create the feed ----------

root.mainloop()

