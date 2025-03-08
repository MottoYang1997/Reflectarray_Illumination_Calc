from tkinter import ttk
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.pyplot import Figure
from LibConst import *

class LabelEntryPair(ttk.Frame):
    def __init__(self, master, label_text, entry_textvar):
        super().__init__(master)
        # Self is a frame that contains a label and an entry
        self.pack(side=tk.TOP, fill=tk.X, expand=1, padx=tk_padx, pady=tk_pady)
        self.label = ttk.Label(self, text=label_text)
        self.label.pack(side=tk.LEFT)
        self.entry = ttk.Entry(self, textvariable=entry_textvar)
        self.entry.pack(side=tk.RIGHT)
    def destroy(self):
        self.label.destroy()
        self.entry.destroy()
        super().destroy()

class LabelPicklistPair(ttk.Frame):
    def __init__(self, master, label_text, picklist_textvar, picklist_values):
        super().__init__(master)
        # Self is a frame that contains a label and a picklist
        self.pack(side=tk.TOP, fill=tk.X, expand=1, padx=tk_padx, pady=tk_pady)
        self.label = ttk.Label(self, text=label_text)
        self.label.pack(side=tk.LEFT)
        self.picklist = ttk.Combobox(self, textvariable=picklist_textvar, values=picklist_values)
        self.picklist.pack(side=tk.RIGHT)
        # Make picklist only selectable, not typeable
        self.picklist.bind("<Key>", lambda e: "break")
        
    def destroy(self):
        self.label.destroy()
        self.picklist.destroy()
        super().destroy()

# This class is a window that displays a plot of the trace data using matplotlib Tkinter backend.
class TracePlotWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        # Self is a top level window that contains a matplotlib figure and axes
        self.title("1D Trace Plot")
        self.figure = Figure(figsize=(8, 6))
        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True)  # Turn on axis grid
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        # Add matplotlib Toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_idletasks() # Ensure the window is properly sized before returning
        self.geometry(f"+{master.winfo_rootx()+50}+{master.winfo_rooty()+50}")
        self.focus_set()
        self.bind("<Escape>", self.on_closing)
        self.bind("<Return>", self.on_ok)
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Ensure the window is properly sized before returning
        self.withdraw() # Hide the window initially
    
    def on_closing(self):
        self.destroy()
    
    def on_ok(self):
        pass
    def add_trace(self, x, y, label="trace"):
        # TODO: Add Interfaces to define line type and color
        self.axes.plot(x, y, label=label)
        self.axes.legend()
        self.canvas.draw()
        self.update_idletasks() # Ensure the plot is properly updated before returning
    
    def set_x_label(self, label):
        self.axes.set_xlabel(label)
        self.canvas.draw()
        self.update_idletasks()

    def set_title(self, title):
        self.axes.set_title(title)
        self.canvas.draw()
        self.update_idletasks()

    def clear_plot(self):
        self.axes.clear()
        self.canvas.draw()
        self.update_idletasks() # Ensure the plot is properly updated before returning

    def show(self):
        self.deiconify() # Show the window
        self.wait_window() # Wait for the window to be closed or destroyed
