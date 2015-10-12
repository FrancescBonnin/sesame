####################################
# Newton-Raphson algorithm
####################################
import sesame
import numpy as np

# from scipy.sparse.linalg import spsolve
from mumps import spsolve
import mumps

def refine(dv):
    for sdx, s in enumerate(dv):
        if abs(s) < 1:
            dv[sdx] /= 2
        if 1 < abs(s) < 3.7:
            dv[sdx] = np.sign(s) * abs(s)**(0.2)/2
        elif abs(s) >= 3.7:
            dv[sdx] = np.sign(s) * np.log(abs(s))/2
    return dv

def poisson_solver(sys, tolerance, guess, max_step=300, info=0):
    # import the module that create F and J
    m = __import__('sesame.getFandJ_eq{0}'.format(sys.dimension), globals(), locals(), ['getFandJ_eq'], 0)
    getFandJ_eq = m.getFandJ_eq

    v = guess
 
    # first step of the Newton Raphson solver
    f, J = getFandJ_eq(sys, v)

    cc = 0
    clamp = 5.
    converged = False

    while converged != True:
        cc = cc + 1
        #-------- solve linear system ---------------------
        dx = spsolve(J, -f)
        dx = dx.transpose()

        #--------- choose the new step -----------------
        error = max(np.abs(dx))

        if error < tolerance:
            converged = True
            v_final = v
            break 

        # use the usual clamping once a proper direction has been found
        elif error < 1e-3:
            # new correction and trial
            dv = dx / (1 + np.abs(dx/clamp))
            v = v + dv
            f, J = getFandJ_eq(sys, v)
            
        # Start slowly this refinement method found in a paper
        else:
            dv = refine(dx)
            v = v + dv
            f, J = getFandJ_eq(sys, v)
            

        # outputing status of solution procedure every so often
        if info != 0 and np.mod(cc, info) == 0:
            print('step = {0}, error = {1}'.format(cc, error), "\n")

        # if no solution found after maxiterations, break
        if cc > max_step:
            print('Poisson solver: too many iterations\n')
            break

    if converged:
        return v_final
    else:
        print("No solution found!\n")
        return None



def solver(sys, guess, tolerance, max_step=300, info=0):
    # guess: initial guess passed to Newton Raphson algorithm
    # tolerance: max error accepted for delta u
    # max_step: maximum number of step allowed before declaring 'no solution
    # found'
    # info: integer, the program will print out the step number every 'info'
    # steps. If info is 0, no output is pronted out

    # import the module that create F and J
    m = __import__('sesame.getF{0}'.format(sys.dimension), globals(), locals(), ['getF'], 0)
    getF = m.getF
    m = __import__('sesame.jacobian{0}'.format(sys.dimension), globals(), locals(), ['getJ'], 0)
    getJ = m.getJ

    efn, efp, v = guess

    f = getF(sys, v, efn, efp)
    J = getJ(sys, v, efn, efp)
    solution = {'v': v, 'efn': efn, 'efp': efp}

    cc = 0
    clamp = 5.
    converged = False

    while converged != True:
        cc = cc + 1
        #-------- solve linear system ---------------------
        dx = spsolve(J, -f)
        dx = dx.transpose()

        #--------- choose the new step -----------------
        error = max(np.abs(dx))

        if error < tolerance:
            converged = True
            solution['efn'] = efn
            solution['efp'] = efp
            solution['v'] = v
            break 

        # use the usual clamping once a proper direction has been found
        elif error < 1e-3:
            # you can see how the variables are arranged: (efn, efp, v)
            defn = dx[0::3]
            defp = dx[1::3]
            dv = dx[2::3]

            defn = dv + (defn - dv) / (1 + np.abs((defn-dv)/clamp))
            defp = dv + (defp - dv) / (1 + np.abs((defp-dv)/clamp))
            dv = dv / (1 + np.abs(dv/clamp))

            efn = efn + defn
            efp = efp + defp
            v = v + dv

            f = getF(sys, v, efn, efp)
            J = getJ(sys, v, efn, efp)

        # Start slowly with this refinement method found in a paper
        else:
            # you can see how the variables are arranged: (efn, efp, v)
            defn = dx[0::3]
            defp = dx[1::3]
            dv = dx[2::3]

            defn = refine(defn)
            defp = refine(defp)
            dv = refine(dv)

            efn = efn + defn
            efp = efp + defp
            v = v + dv

            f = getF(sys, v, efn, efp)
            J = getJ(sys, v, efn, efp)

            A=J.todense()
            # print(A[10,:])
            # print(f)
            # print(np.dot(A,f))


        # outputing status of solution procedure every so often
        if info != 0 and np.mod(cc, info) == 0:
            print('step = {0}, error = {1}'.format(cc, error), "\n")

        # if no solution found after maxiterations, break
        if cc > max_step:
            print('too many iterations\n')
            break

    if converged:
        return solution
    else:
        print("No solution found!\n")
        return None
