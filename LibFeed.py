from enum import Enum
from LibConst import *
import numpy as np
#from scipy.integrate import dblquad


# ---------- BEGIN Common Functions from Numpy ----------
cos = np.cos
sin = np.sin
rad2deg = np.rad2deg
deg2rad = np.deg2rad
log10 = np.log10
# ---------- END Common Functions from Numpy ----------


class FeedType(Enum):
    Cos_theta_q = "E(Theta) = cos(Theta)^Q"


# ---------- BEGIN Feed Functions ----------
# TODO: Reduce the numeric error when updating the feed parameters

def q_to_gain_lin(q):
    integrant = lambda phi, theta: cos(theta)**(2*q)*sin(theta)
    #p_total,_ = dblquad(integrant, 0, pi/2, 0, 2*pi)
    #gain_lin = 4*pi / p_total
    gain_lin = 4*q + 2
    return gain_lin
def q_to_gain_dbi(q):
    gain_lin = q_to_gain_lin(q)
    return 10*log10(gain_lin)


def gain_lin_to_q(gain_lin):
    return (gain_lin - 2)/4
def gain_dbi_to_q(gain_dbi):
    g_lin = 10.0**(gain_dbi/10.0)
    return gain_lin_to_q(g_lin)


def q_to_hpbw(q):
    return 2*np.arccos(np.power(2, -1/2/q))
def hpbw_to_q(hpbw):
    return -3/(20*log10(np.cos(hpbw/2)))


def hpbw_to_gain_dbi(hpbw):
    q = hpbw_to_q(hpbw)
    return q_to_gain_dbi(q)
# ---------- END Feed Functions ----------


class Feed:
    def __init__(self):
        self.type = FeedType.Cos_theta_q
        self.__init_parameters()
        pass
    
    def update_type(self, type):
        self.type = type
        self.__init_parameters()

    def __init_parameters(self):
        self.parameters={}
        if self.type == FeedType.Cos_theta_q:
            # Dependent Values: Freq - Wavelength
            self.parameters['Freq (GHz)'] = 1.0
            self.parameters['Wavelength (mm)'] = c/1e9*1e3

            # Dependent Values: HPBW - Gain - Q
            self.parameters['HPBW (deg)'] = 20.0
            self.parameters['Gain (dBi)'] = hpbw_to_gain_dbi(deg2rad(20))
            self.parameters['Q'] = gain_dbi_to_q(self.parameters['Gain (dBi)'])
            
            # Dependent Values: XYZ - RThetaPhi
            self.parameters['PosX (mm)'] = 0.0
            self.parameters['PosY (mm)'] = 0.0
            self.parameters['PosZ (mm)'] = 1.0
            self.parameters['PosR (mm)'] = 1.0
            self.parameters['PosTheta (Deg)'] = 0.0
            self.parameters['PosPhi (Deg)'] = 0.0
        else:
            pass
    
    def get_parameter_linear_SI(self, name):
        if name not in self.parameters:
            return None
        if "mm" in name:
            return self.parameters[name]*1e-3
        if "GHz" in name:
            return self.parameters[name]*1e9
        if "Deg" in name:
            return deg2rad(self.parameters[name])
        if "dBi" in name:
            return 10**(self.parameters[name]/10)
        return self.parameters[name]

    def update_parameter(self, name, value):
        try:
            value = float(value)
        except ValueError:
            return False
        
        if self.type == FeedType.Cos_theta_q:
            if name not in self.parameters:
                return False
            
            # Try to update the parameter, if it fails, return False and print the corresponding error message
            try:
                self.parameters[name] = value
                if name == 'Freq (GHz)':
                    self.parameters['Wavelength (mm)'] = c/(value*1e9)*1e3
                elif name == 'Wavelength (mm)':
                    self.parameters['Freq (GHz)'] = c/(value*1e-3)*1e-9
                elif name == 'Gain (dBi)':
                    self.parameters['Q'] = gain_dbi_to_q(value)
                    self.parameters['HPBW (deg)'] = rad2deg(q_to_hpbw(self.parameters['Q']))
                elif name == 'HPBW (deg)':
                    self.parameters['Q'] = hpbw_to_q(deg2rad(value))
                    self.parameters['Gain (dBi)'] = q_to_gain_dbi(self.parameters['Q'])
                elif name == 'Q':
                    self.parameters['Gain (dBi)'] = q_to_gain_dbi(value)
                    self.parameters['HPBW (deg)'] = rad2deg(q_to_hpbw(value))
                elif name == 'PosX (mm)' or name == 'PosY (mm)' or name == 'PosZ (mm)':
                    x = self.parameters['PosX (mm)']
                    y = self.parameters['PosY (mm)']
                    z = self.parameters['PosZ (mm)']
                    self.parameters['PosR (mm)'] = np.sqrt(x**2 + y**2 + z**2)
                    self.parameters['PosTheta (Deg)'] = rad2deg(np.arccos(z/self.parameters['PosR (mm)']))
                    self.parameters['PosPhi (Deg)'] = rad2deg(np.arctan2(y, x))
                elif name == 'PosR (mm)' or name == 'PosTheta (Deg)' or name == 'PosPhi (Deg)':
                    r = self.parameters['PosR (mm)']
                    theta = deg2rad(self.parameters['PosTheta (Deg)'])
                    phi = deg2rad(self.parameters['PosPhi (Deg)'])
                    self.parameters['PosX (mm)'] = r*sin(theta)*cos(phi)
                    self.parameters['PosY (mm)'] = r*sin(theta)*sin(phi)
                    self.parameters['PosZ (mm)'] = r*cos(theta)
                else:    
                    pass
            except:
                print("Invalid Value for {}".format(name))
                return False
            return True


if __name__ == "__main__":
    print(np.rad2deg((q_to_hpbw(hpbw_to_q(np.deg2rad(20))))))
    print(hpbw_to_q(q_to_hpbw(2)))
    print(hpbw_to_gain_dbi(deg2rad(20)))
