import sesame
import numpy as np
from scipy.io import savemat

# dimensions of the system
Lx = 3e-4   # [cm]
Ly = 3e-4   # [cm]

# Mesh
x = np.concatenate((np.linspace(0, .2e-4, 30, endpoint=False),
                    np.linspace(0.2e-4, 1.4e-4, 60, endpoint=False),
                    np.linspace(1.4e-4, 2.7e-4, 60, endpoint=False),
                    np.linspace(2.7e-4, 2.98e-4, 30, endpoint=False),
                    np.linspace(2.98e-4, Lx, 10)))

y = np.concatenate((np.linspace(0, 1.25e-4, 60, endpoint=False),
                    np.linspace(1.25e-4, 1.75e-4, 50, endpoint=False),
                    np.linspace(1.75e-4, Ly, 60)))

# Create a system
sys = sesame.Builder(x, y)

# Dictionary with the material parameters
mat = {'Nc':8e17, 'Nv':1.8e19, 'Eg':1.5, 'epsilon':9.4, 'Et': 0,
       'mu_e':320, 'mu_h':40, 'tau_e':10*1e-9, 'tau_h':10*1e-9}

# Add the material to the system
sys.add_material(mat)

# function defining region of reduced mobility
xGB = 1.5e-4  # GB x-coordinate
Lmu = .25e-4  # distance from GB over which mobility is reduced
def reduced_mu_region(pos):
    x, y = pos
    return ((x < xGB+Lmu) & (x > xGB-Lmu) & (y > .1e-4) & (y < 2.9e-4))

# function defining region of reduced mobility
def my_mu(pos):
    muGB = 10
    x, y = pos
    # mobility varies linearly between GB core and Lmu
    return 10 + 310*np.abs((x-xGB)/Lmu)

mat2 = {'Nc': 8e17, 'Nv': 1.8e19, 'Eg': 1.5, 'epsilon': 9.4, 'Et': 0,
       'mu_e': my_mu, 'mu_h': 40, 'tau_e': 10 * 1e-9, 'tau_h': 10 * 1e-9}

# Add the material to the system
sys.add_material(mat2, reduced_mu_region)


sesame.plot(sys, sys.mu_e)


# extent of the junction from the left contact [cm]
junction = .1e-4    # [cm]
# define a function specifiying the n-type region
def region1(pos):
    x, y = pos
    return x < junction
# define a function specifiying the p-type region
def region2(pos):
    x, y = pos
    return x >= junction

nD = 1e17   # donor density[cm^-3]
# Add the donors
sys.add_donor(nD, region1)
nA = 1e15   # acceptor density [m^-3]
# Add the acceptors
sys.add_acceptor(nA, region2)


# Define contacts: CdS and CdTe contacts are Ohmic
sys.contact_type('Ohmic','Ohmic')
# Define the surface recombination velocities for electrons and holes [cm/s]
Sn_left, Sp_left, Sn_right, Sp_right = 1e7, 1e7, 1e7, 1e7
# This function specifies the simulation contact recombination velocity
sys.contact_S(Sn_left, Sp_left, Sn_right, Sp_right)



# GB defect state properties
rho_GB = 1e14               # defect density [1/cm^2]
S_GB = 1e-14                # capture cross section [cm^2]
E_GB = 0.4                  # energy of gap state from intrinsic level [eV]
# Specify the two points that make the line containing additional charges
p1 = (.1e-4, 1.5*1e-4)      # [cm]
p2 = (2.9e-4, 1.5*1e-4)     # [cm]


# add donor defect along GB
sys.add_defects([p1, p2], rho_GB, S_GB, E=E_GB, transition=(1,0))
# add acceptor defect along GB
sys.add_defects([p1, p2], rho_GB, S_GB, E=E_GB, transition=(0,-1))


# Solve equilibirum problem first
solution = sesame.solve(sys, 'Poisson')


# define a function for generation profile
f = lambda x, y: 2.3e21*np.exp(-2.3e4*x)
# add generation to the system
sys.generation(f)

# Solve problem under short-circuit current conditions
solution = sesame.solve(sys, guess=solution)
# Get analyzer object to compute observables
az = sesame.Analyzer(sys, solution)
# Compute short-circuit current
j=az.full_current()
# Print Jsc
print(j*sys.scaling.current*sys.scaling.length*1e3)


# specify applied voltages
voltages = np.linspace(0, .9, 10)
# find j-v
j = sesame.IVcurve(sys, voltages, solution, '2dGB_V')

# save the result
result = {'voltages':voltages, 'j':j}
np.save('IV_values',result)

