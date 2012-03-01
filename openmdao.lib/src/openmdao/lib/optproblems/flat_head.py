"""
Flat Head Cylinder Model 

T. C. Wagner and P. Y. Papalambros, Optimal Engine Design Using 
Non Linear Proramming and the Engine System Assesment Model, 
Ann Arbor, Michigan, Aug. 1991.

"""


from openmdao.main.api import Component
from openmdao.main.problem_formulation import OptProblem
from openmdao.lib.datatypes.api import Float, Int

from math import pi,exp

#problem constants
Q = 43958 #kJ/kg
rho = 1.225 #kg/m**3
A_f = 14.6
gamma = 1.33
N_c = 4.0 # number of cylinders
v = 1.856e6 #mm**3 cylinder volume

class CylinderGeometry(Component): 
    
    b = Float(0.0, iotype="in", desc = "cylinder bore", units = "mm")
    s = Float(0.0,iotype="in", desc = "cylinder stroke", units = "mm")
    w = Float(0.0,iotype="in",desc="revolutions per minute at peak power*10^-3", units = "rpm/1000")
    c_r = Float(0.0,iotype="in",desc="compression ratio")
    
    S_v = Float(0.0,iotype="out",desc="Surface to volume ratio", units="mm**-1")
    V_p = Float(0.0,iotype="out",desc="mean piston speed", units="m/min")      
    h = Float(0.0,iotype="out",desc="compound valve chamber deck height", units = "mm")

    
    def execute(self): 
        
        self.S_v = .83*((8+4*self.c_r)+1.5*pi*N_c*(self.c_r-1)/v*self.b**3)/((2+self.c_r)*self.b)
        self.V_p =  (8*v)/(pi*N_c)*self.w*self.b**-2  
        self.h = self.s/(self.c_r-1)

class CylinderThermodynamics(Component): 
    
    w = Float(0.0,iotype="in",desc="revolutions per minute at peak power*10^-3", units = "rpm/1000")
    b = Float(0.0, iotype="in", desc = "cylinder bore", units = "mm")
    c_r = Float(0.0,iotype="in",desc="compression ratio")
    C_s = Float(0.44,iotype="in",desc="port discharge coefficient")
    d_i = Float(0.0,iotype="in",desc="intake valve diameter",units="mm")
    d_e = Float(0.0,iotype="in",desc="exhaust valve diameter",units="mm")
    
    #coupling inputs
    S_v = Float(0.0,iotype="in",desc="Surface to volume ratio", units="mm**-1")
    V_p = Float(0.0,iotype="in",desc="mean piston speed", units="m/min")
    
    
    FMEP = Float(0.0,iotype="out",desc="friction mean effective pressure", units="bar")
    IMEP = Float(0.0,iotype="out",desc="indicated mean effective pressure", units="bar")
    BMEP = Float(0.0,iotype="out",desc="brake mean effective pressure", units="bar")
    eta_tad = Float(0.0,iotype="out",desc="adiabatic thermal efficiency")
    eta_t = Float(0.0,iotype="out",desc="thermal efficiency")
    eta_tw = Float(0.0,iotpye="out",desc="thermal efficiency at representative part load point, 1500 rpm, AFR 14.6")
    eta_vb = Float(0.0,iotpye="out",desc="base volumetric efficiency")
    eta_v = Float(0.0,iotype="out",desc="volumetric efficiency")
    
    
    
    def execute(self): 
        
        self.FMEP = 4.826(self.c_r-9.2)+(7.97+0.253*self.V_p+9.7e-6*self.V_p**2)
        
        self.eta_tad = 0.8595*(1-self.c_r**-0.33)
        self.eta_t = self.eta_tad-self.S_v*(1.5/self.w)**0.5
        self.eta_tw = 0.8595*(1-self.c_r**-0.33)- self.S_v
        
        if self.w >= 5.25: 
            self.eta_vb = 1.067 - 0.038*exp(w-5.25)
        else: 
            self.eta_vb = 0.637 + 0.13*self.w - 0.014*self.w**2 + 0.00066*2**3

        self.eta_v = self.eta_vb*(1+5.96e-3*w**2)/(1+(9.428e-5*(4*v)/(pi*N_c*self.C_s)*(self.w)/(self.d_i**2))**2)
        
        self.IMEP = self.eta_t*self.eta_v*(rho*Q/A_f)
        self.BMEP = self.IMEP - self.FMEP
        
class FlatHeadCylinder(OptProblem): 
    
    def __init__(self): 
        super(FlatHeadCylinder,self).__init__()
        
        #bring the constants into the assembly, for use with constraints/objectives 
        
        self.N_c = N_c
        self.Q = Q 
        self.rho = rho
        self.A_f = A_f
        self.gamma = gamma
        self.v = v 
        
        self.K0 = 1.0/120.0 #unit conversion constant
        self.K1 = 1.2 #20% bore spacing 
        self.K2 = 2.0
        self.K2 = 0.82
        
        self.L1 = 400 #mm
        self.L2 = 200 #mm

        
        #create the analysis components
        self.add('geom',CylinderGeometry())
        self.add('thermo',CylinderThermodynamics())
        
        #global des vars
        self.add_parameter(['geom.b','thermo.b'],low=0.0,high=200.0,start=82.0,name='b')
        
        #local des vars
        self.add_parameter('thermo.d_i',low = 10.0, high = 100.0, start = 20.0)
        self.add_parameter('thermo.d_e',low = 10.0, high = 100.0, start = 20.0)
        
        self.add_objective('thermo.BMEP*thermo.w/120')
        
        self.add_constraint('geom.b/geom.s < 1.13')
        self.add_constraint('geom.b/geom.s > .7')
        
        self.add_constraint('K1*N_c*geom.b <= L1')
        self.add_constraint('K2*geom.s <= L2')
        self.add_constraint('thermo.d_i + thermo.d_e <= K3*thermo.b')
        
        
        
if __name__ == "__main__": 
    
    f = FlatHeadCylinder()
    
    
    