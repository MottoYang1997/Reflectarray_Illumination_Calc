from enum import Enum
from numpy import deg2rad


class ApertureType(Enum):
    Circular = "Circular Aperture"
    Square = "Square Aperture"
    Rectangular = "Rectangular Aperture"


class Aperture:
    def __init__(self):
        self.type = ApertureType.Circular
        self.__init_parameters()
        pass

    def __init_parameters(self):
        self.parameters = {}
        if self.type == ApertureType.Circular:
            self.parameters['Radius (mm)'] = 1
        elif self.type == ApertureType.Square:
            self.parameters['Width (mm)'] = 1
        elif self.type == ApertureType.Rectangular:
            self.parameters['X Length (mm)'] = 2
            self.parameters['Y Length (mm)'] = 1
        else:
            pass

    def update_type(self, type):
        self.type = type
        self.__init_parameters()        

    def update_parameter(self, name, value):
        try:
            value = float(value)
        except ValueError:
            return False
        
        if name not in self.parameters:
            return False
        
        self.parameters[name] = value
        print("Updated {} to {}".format(name, value)) # Debugging
        return True     
        
    def print_parameters(self):
        for name in self.parameters:
            print(name, self.parameters[name])
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
