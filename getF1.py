import numpy as np

from sesame.observables2 import *

def getF(sys, v, efn, efp):
    ###########################################################################
    #               organization of the right hand side vector                #
    ###########################################################################
    # A site with coordinates (i) corresponds to a site number s as follows:
    # i = s
    #
    # Rows for (efn_s, efp_s, v_s)
    # ----------------------------
    # fn_row = 3*s
    # fp_row = 3*s+1
    # fv_row = 3*s+2

    Nx = sys.xpts.shape[0]
    dx = sys.dx

    # right hand side vector
    vec = np.zeros((3*Nx,))

    ###########################################################################
    #                     For all sites in the system                         #
    ###########################################################################
    sites = [i for i in range(Nx)]

    # carrier densities
    n = get_n(sys, efn, v, sites)
    p = get_p(sys, efp, v, sites)

    # bulk charges
    rho = sys.rho - n + p

    # recombination rates
    r = get_rr(sys, n, p, sys.n1, sys.p1, sys.tau_e, sys.tau_h, sites)

    # extra charge density
    if hasattr(sys, 'Nextra'): 
        # find sites containing extra charges
        matches = [s for s in sites if s in sys.extra_charge_sites]

        nextra = sys.nextra[matches]
        pextra = sys.pextra[matches]
        _n = n[matches]
        _p = p[matches]

        # extra charge density
        f = (_n + pextra) / (_n + _p + nextra + pextra)
        rho[matches] += sys.Nextra[matches] / 2. * (1 - 2*f)

        # extra charge recombination
        r[matches] += get_rr(sys, _n, _p, nextra, pextra, 1/Sextra[matches],
                             1/Sextra[matches], matches)

    # charge devided by epsilon
    rho /= sys.epsilon[sites]

    ###########################################################################
    #                   inside the system: 0 < i < Nx-1                       #
    ###########################################################################
    # We compute fn, fp, fv. Those functions are only defined on the
    # inner part of the system. All the edges containing boundary conditions.

    # list of the sites inside the system
    sites = [i for i in range(1,Nx-1)]
    sites = np.asarray(sites)

    # dxbar
    dxbar = (dx[sites] + dx[sites-1]) / 2.

    # gather all relevant pairs of sites to compute the currents
    sm1_s = [i for i in zip(sites - 1, sites)]
    s_sp1 = [i for i in zip(sites, sites + 1)]

    # compute the currents
    jnx_s   = get_jn(sys, efn, v, s_sp1)
    jnx_sm1 = get_jn(sys, efn, v, sm1_s)

    jpx_s   = get_jp(sys, efp, v, s_sp1)
    jpx_sm1 = get_jp(sys, efp, v, sm1_s)

    #--------------------------------------------------------------------------
    #------------------------------ fn ----------------------------------------
    #--------------------------------------------------------------------------
    fn = (jnx_s - jnx_sm1) / dxbar + sys.g[sites] - r[sites]

    vec[[3*s for s in sites]] = fn

    #--------------------------------------------------------------------------
    #------------------------------ fp ----------------------------------------
    #--------------------------------------------------------------------------
    fp = (jpx_s - jpx_sm1) / dxbar + r[sites] - sys.g[sites]

    vec[[3*s+1 for s in sites]] = fp

    #--------------------------------------------------------------------------
    #------------------------------ fv ----------------------------------------
    #--------------------------------------------------------------------------
    fv = ((v[sites]-v[sites-1]) / dx[sites-1] - (v[sites+1]-v[sites]) / dx[sites]) / dxbar\
       - rho[sites]

    vec[[3*s+2 for s in sites]] = fv

    ###########################################################################
    #                       left boundary: i = 0                              #
    ###########################################################################
    # compute the currents
    s_sp1 = [(0, 1)]
    jnx = get_jn(sys, efn, v, s_sp1)
    jpx = get_jp(sys, efp, v, s_sp1)

    # compute an, ap, av
    n_eq = 0
    p_eq = 0
    #TODO tricky here to decide
    if sys.rho[0] < 0: # p doped
        p_eq = -sys.rho[0]
        n_eq = sys.ni[0]**2 / p_eq
    else: # n doped
        n_eq = sys.rho[0]
        p_eq = sys.ni[0]**2 / n_eq
        
    an = jnx - sys.Scn[0] * (n[0] - n_eq)
    ap = jpx + sys.Scp[0] * (p[0] - p_eq)
    av = 0 # to ensure Dirichlet BCs

    vec[[0]] = an
    vec[[1]] = ap
    vec[[2]] = av

    ###########################################################################
    #                         right boundary: i = Nx-1                        #
    ###########################################################################
    # dxbar
    dxbar = dx[-1]

    # compute the currents
    sm1_s = [(Nx-1 - 1, Nx-1)]

    # compute the currents
    jnx_sm1 = get_jn(sys, efn, v, sm1_s)
    jpx_sm1 = get_jp(sys, efp, v, sm1_s)

    jnx_s = jnx_sm1 + dxbar * (r[sites] - sys.g[sites])
    jpx_s = jpx_sm1 + dxbar * (sys.g[sites] - r[sites])

    # b_n, b_p and b_v values
    n_eq = 0
    p_eq = 0
    if sys.rho[-1] < 0: # p doped
        p_eq = -sys.rho[-1]
        n_eq = sys.ni[-1]**2 / p_eq
    else: # n doped
        n_eq = sys.rho[-1]
        p_eq = sys.ni[-1]**2 / n_eq
        
    bn = jnx_s + sys.Scn[1] * (n[-1] - n_eq)
    bp = jpx_s - sys.Scp[1] * (p[-1] - p_eq)
    bv = 0 # Dirichlet BC

    vec[[3*(Nx-1)]] = bn
    vec[[3*(Nx-1)+1]] = bp
    vec[[3*(Nx-1)+2]] = bv      

    ###########################################################################
    #                         top and bottom boundaries                       #
    ###########################################################################
    # I want periodic boundary conditions so, I have a bunch of zeros in the
    # vector on the right hand side and place 1 and -1 values in the Jacobian.

    return vec
