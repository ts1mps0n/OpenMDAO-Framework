"""
Flat Head Cylinder Model 

T. C. Wagner and P. Y. Papalambros, Optimal Engine Design Using 
Non Linear Proramming and the Engine System Assesment Model, 
Ann Arbor, Michigan, Aug. 1991.

"""


from openmdao.main.api import Component
from openmdao.main.problem_formulation import OptProblem
from openmdao.lib.datatypes.api import Float

from math import pi

class CylinderGeometry(Component): 
    
    v = Float(0.0,iotype="in",desc="displacement volume", units = "mm**3")
    b = Float(0.0, iotype="in", desc = "cylinder bore", units = "mm")
    
    S_v = Float(0.0,iotype="out",desc="Surface to volume ratio", units="mm**-1")
    
    def execute(self): 
        
        self.S_v = .83*((8+4*self.c_r)+1.5*pi*self.N_c*(self.c_r-1)/self.v*self.b**3)/((2+self.c_r)*self.b)


class CylinderThermodynamics(Component): 
    
    w = Float(0.0,iotype="in",desc="revolutions per minute at peak power*10^-3", units = "rpm/1000")
    b = Float(0.0, iotype="in", desc = "cylinder bore", units = "mm")
    v = Float(0.0,iotype="in",desc="displacement volume", units = "mm**3")
    c_r = Float(0.0,iotype="in",desc="compression ratio")
    
    #coupling inputs
    S_v = Float(0.0,iotype="in",desc="Surface to volume ratio", units="mm**-1")

    
    V_p = Float(0.0,iotype="out",desc="mean piston speed", units="m/min")
    FMEP = Flaot(0.0,iotype="out",desc="friction mean effective pressure", units="bar")
    eta_tad = Float(0.0,iotype="out",desc="adiabatic thermal efficiency")
    eta_t = Float(0.0,iotype="out",desc="thermal efficiency")
    eta_tw = Float(0.0,iotpye="out",desc="thermal efficiency at representative part load point, 1500 rpm, AFR 14.6")
    
    
    
    def execute(self): 
        self.V_p =  (8*self.v)/(pi*self.N_c)*self.w*self.b**-2  
        
        self.FMEP = 4.826(self.c_r-9.2)+(7.97+0.253*self.V_p+9.7e-6*self.V_p**2)
        self.eta_tad = 0.8595*(1-self.c_r**-0.33)
        self.eta_t = self.eta_tad-self.S_v*(1.5/self.w)**0.5
        self.eta_tw = 0.8595*(1-self.c_r**-0.33)- self.S_v


class FlatHeadCylinder(OptProblem): 
    pass
    
    