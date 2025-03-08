from enum import Enum
from LibAperture import ApertureType, Aperture
from LibFeed import FeedType, Feed
import numpy as np
from scipy.integrate import nquad
from copy import deepcopy
from LibConst import *


# ---------- BEGIN Common Functions from Numpy ----------
norm = np.linalg.norm
pi = np.pi
cos = np.cos
sin = np.sin
cos_vec = lambda v1, v2: v1 @ v2 / (norm(v1)*norm(v2))
def dblquad(func, x0, x1, y0, y1, epsabs=1e-3, epsrel=1e-3, max_iter=10):
    return nquad(func, [[x0, x1], [y0, y1]], 
                 opts=[{'limit': max_iter, 'epsabs': epsabs, 'epsrel': epsrel}, 
                       {'limit': max_iter, 'epsabs': epsabs, 'epsrel': epsrel}])
# ---------- END Common Functions from Numpy ----------


class CalculationType(Enum):
    DirectCalc = "Direct Calculation"
    Sweep1D = "Linear 1D Sweep"
    #Sweep2D = "Linear 2D Sweep" # TODO: Implement Sweep 2D


class Calculation:
    def __init__(self):
        self.type = CalculationType.DirectCalc
        self.__init__parameters()
        self.results = None
        pass

    def __init__parameters(self):
        self.parameters = {}
        if self.type == CalculationType.DirectCalc:
            pass
        elif self.type == CalculationType.Sweep1D:
            self.parameters['Sweep Variable'] = "Freq (GHz)"
            self.parameters['Sweep Start'] = 0.1
            self.parameters['Sweep Stop'] = 1.0
            self.parameters['Sweep Steps'] = 10 # TODO: Change the name 'Steps' to 'Points'
        elif self.type == CalculationType.Sweep2D:
            self.parameters['Sweep Variable A'] = "Freq (GHz)"
            self.parameters['Sweep Start A'] = 0.1
            self.parameters['Sweep Stop A'] = 1.0
            self.parameters['Sweep Steps A'] = 10
            self.parameters['Sweep Variable B'] = "Freq (GHz)"
            self.parameters['Sweep Start B'] = 0.1
            self.parameters['Sweep Stop B'] = 1.0
            self.parameters['Sweep Steps B'] = 10
        else:
            pass
    
    def save_results(self, results):
        self.results = results

    def empty_results(self):
        self.results = None

    def update_type(self, type):
        self.type = type
        self.__init__parameters()
    
    def update_parameter(self, name, value):
        if name not in self.parameters:
            return False
        
        if "Variable" in name:
            self.parameters[name] = value
            return True
        
        if "Steps" in name:
            try:
                self.parameters[name] = int(value)
                return True
            except ValueError:
                return False
        
        try:
            self.parameters[name] = float(value)
            return True
        except ValueError:
            return False

    # TODO: Add messagebox when computation error is occurred.
    def calc_taper_and_spillover_efficiency_oneshot(self, feed: Feed, aperture: Aperture):
        # Common variables for calculation
        q = feed.get_parameter_linear_SI('Q')
        x_feed = feed.get_parameter_linear_SI("PosX (mm)")
        y_feed = feed.get_parameter_linear_SI("PosY (mm)")
        z_feed = feed.get_parameter_linear_SI("PosZ (mm)")
        vec_feed = np.array([x_feed, y_feed, z_feed])

        # Get the field strength (sqrt of intensity) along theta for a given feed type
        if feed.type == FeedType.Cos_theta_q:
            def field_strength_along_theta(theta):
                return cos(theta)**q
        else:
            field_strength_along_theta = None
        
        # Calculate the normalized total power of the feed (Solid Angle Integration)
        def total_power_integrant(theta, phi):
            return field_strength_along_theta(theta)**2 * sin(theta)
        total_power, _ = dblquad(total_power_integrant, 0, pi/2, 0, pi*2, 
                                 epsabs=quad_error, epsrel=quad_error, max_iter=max_iter)

        # Calculate the powers based on the integration domain of the aperture
        if aperture.type == ApertureType.Circular:
            # Calculate the total power on the aperture (Cartesian to Solid-Angle Integration)
            r_max = aperture.get_parameter_linear_SI("Radius (mm)")
            area = pi * r_max**2
            def total_power_on_aperture_integrant(r, phi):
                x = r * cos(phi)
                y = r * sin(phi)
                vec_pos = np.array([x, y, 0])
                vec_incidence = vec_pos - vec_feed
                vec_incidence_len = norm(vec_incidence)
                dir_incidence = vec_incidence / vec_incidence_len
                cos_theta = -1 * dir_incidence @ vec_feed / norm(vec_feed)
                projection = dir_incidence @ np.array([0, 0, -1])
                return cos_theta**(q*2) / vec_incidence_len**2 * projection * r
            total_power_on_aperture, _ = dblquad(total_power_on_aperture_integrant, 0, r_max, 0, pi*2, 
                                                 epsabs=quad_error, epsrel=quad_error, max_iter=max_iter)

            # Calculate the power of the average incidence on the aperture (Cartesian to Solid-Angle Integration)
            def field_integrant(r, phi):
                x = r * cos(phi)
                y = r * sin(phi)
                vec_pos = np.array([x, y, 0])
                vec_incidence = vec_pos - vec_feed
                vec_incidence_len = norm(vec_incidence) 
                dir_incidence = vec_incidence / vec_incidence_len
                cos_theta = -1 * dir_incidence @ vec_feed / norm(vec_feed)
                projection = dir_incidence @ np.array([0, 0, -1])
                return cos_theta**(q) / vec_incidence_len* r * projection**0.5
            field_avg, _ = dblquad(field_integrant, 0, r_max, 0, pi*2, 
                                   epsabs=quad_error, epsrel=quad_error, max_iter=max_iter)


            field_avg /= area
            total_power_of_field_avg = field_avg**2 * area

        elif aperture.type == ApertureType.Rectangular or aperture.type == ApertureType.Square:
            # Get the integration limits
            if aperture.type == ApertureType.Square:
                size = aperture.get_parameter_linear_SI("Width (mm)")
                area = size**2
                x0 = -size/2
                x1 = size/2
                y0 = -size/2
                y1 = size/2
            else:
                size_x = aperture.get_parameter_linear_SI("X Length (mm)")
                size_y = aperture.get_parameter_linear_SI("Y Length (mm)")
                area = size_x * size_y
                x0 = -size_x/2
                x1 = size_x/2
                y0 = -size_y/2
                y1 = size_y/2
            
            # Calculate the total power on the aperture (Cartesian to Solid-Angle Integration)
            def total_power_on_aperture_integrant(x, y):
                vec_pos = np.array([x, y, 0])
                vec_incidence = vec_pos - vec_feed
                vec_incidence_len = norm(vec_incidence)
                dir_incidence = vec_incidence / vec_incidence_len
                cos_theta = -1 * dir_incidence @ vec_feed / norm(vec_feed)
                projection = dir_incidence @ np.array([0, 0, -1])
                return cos_theta**(q*2) / vec_incidence_len**2 * projection
            total_power_on_aperture, _ = dblquad(total_power_on_aperture_integrant, x0, x1, y0, y1, 
                                                 epsabs=quad_error, epsrel=quad_error, max_iter=max_iter)

            # Calculate the power of the average incidence on the aperture (Cartesian to Solid-Angle Integration)
            def field_integrant(x, y):
                vec_pos = np.array([x, y, 0])
                vec_incidence = vec_pos - vec_feed
                vec_incidence_len = norm(vec_incidence) 
                dir_incidence = vec_incidence / vec_incidence_len
                cos_theta = -1 * dir_incidence @ vec_feed / norm(vec_feed)
                projection = dir_incidence @ np.array([0, 0, -1])
                return cos_theta**(q) / vec_incidence_len * projection**0.5
            field_avg, _ = dblquad(field_integrant, x0, x1, y0, y1, 
                                   epsabs=quad_error, epsrel=quad_error, max_iter=max_iter)

            field_avg /= area
            total_power_of_field_avg = field_avg**2 * area

        else:
            taper_efficiency = 0

        taper_efficiency = total_power_of_field_avg / total_power_on_aperture
        spillover_efficiency = total_power_on_aperture / total_power
        return taper_efficiency, spillover_efficiency

    def sweep_taper_and_spillover_efficiencies_1d(self, feed: Feed, aperture: Aperture, progressbar=None):
        # The general idea of sweeping is that:
        # First store a record of the feed and aperture as a back up.
        # In the sweep loop, for each point to be calculated, update the parameters of the feed and aperture.
        feed_sweep = deepcopy(feed)
        aperture_sweep = deepcopy(aperture)

        if not self.type == CalculationType.Sweep1D:
            return None
        var_name = self.parameters['Sweep Variable']
        var_start = self.parameters['Sweep Start']
        var_end = self.parameters['Sweep Stop']
        var_step = self.parameters['Sweep Steps'] 
        var_linspace = np.linspace(var_start, var_end, var_step)
        taper_efficiencies = []
        spillover_efficiencies = []
        for i in range(len(var_linspace)):
            if var_name in feed_sweep.parameters.keys():
                feed_sweep.update_parameter(var_name, var_linspace[i])
            else:
                aperture_sweep.update_parameter(var_name, var_linspace[i])
            # Calculate the taper efficiency and spillover efficiency for each point.
            taper, spill = self.calc_taper_and_spillover_efficiency_oneshot(feed_sweep, aperture_sweep)
            # Store these values in lists.
            taper_efficiencies.append(taper)
            spillover_efficiencies.append(spill)
            if progressbar is not None:
                progressbar['value'] = int(float(i/len(var_linspace)) * 100)
                progressbar.update_idletasks()
        # Return the lists of taper efficiencies and spillover efficiencies.
        return np.array(taper_efficiencies), np.array(spillover_efficiencies)


    def sweep_taper_and_spillover_efficiencies_2d(self, feed: Feed, aperture: Aperture):
        if not self.type == CalculationType.Sweep2D:
            return None
        var_name_a = self.parameters['Sweep Variable A']
        var_name_b = self.parameters['Sweep Variable B']
        return 0, 0
