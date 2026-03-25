import numpy as np
from scipy.optimize import minimize

class MPCController:

    def __init__(self, params, limits, weights, N, Ts):
        self.params = params
        self.limits = limits
        self.W = weights
        self.N = N
        self.Ts = Ts

    # ================= VEHICLE MODEL =================
    def vehicle_model(self, x, u):
        psi = x[2]
        v   = x[3]

        delta = u[0]
        a     = u[1]

        L  = self.params['L']
        lr = self.params['lr']

        beta = np.arctan((lr / L) * np.tan(delta))

        xdot = np.zeros(4)
        xdot[0] = v * np.cos(psi + beta)
        xdot[1] = v * np.sin(psi + beta)
        xdot[2] = (v / L) * np.cos(beta) * np.tan(delta)
        xdot[3] = a

        x1 = x + self.Ts * xdot
        
        return x1

    # ================= COST =================
    def cost(self, z, x0, last_u, refH):
        x = x0.copy()
        u_prev = last_u.copy()
        J = 0.0

        for k in range(self.N):
            uk = z[2*k:2*k+2]

            x = self.vehicle_model(x, uk)

            # errori
            e_pos = x[0:2] - refH[k,0:2]
            e_psi = self.wrap_to_pi(x[2] - refH[k,2])
            e_v   = x[3] - refH[k,3]

            # tracking
            J += self.W['w_pos'] * np.dot(e_pos, e_pos)
            J += self.W['w_psi'] * (e_psi**2)
            J += self.W['w_v']   * (e_v**2)

            # input
            J += self.W['w_u'][0]*uk[0]**2 + self.W['w_u'][1]*uk[1]**2

            # smoothness
            du = uk - u_prev
            J += self.W['w_du'][0]*du[0]**2 + self.W['w_du'][1]*du[1]**2

            u_prev = uk

        # terminal
        eN = x[0:2] - refH[-1,0:2]
        J += self.W['w_goal'] * np.dot(eN, eN)

        return J

    # ================= CONSTRAINTS =================
    def constraints(self, z, x0, last_u):
        cons = []

        # rate constraints
        u_prev = last_u.copy()

        for k in range(self.N):
            uk = z[2*k:2*k+2]
            du = (uk - u_prev) / self.Ts

            cons += [
                self.limits['dDeltaMax'] - du[0],
                du[0] - self.limits['dDeltaMin'],
                self.limits['dAMax'] - du[1],
                du[1] - self.limits['dAMin'],
            ]

            u_prev = uk

        # velocity constraints
        x = x0.copy()

        for k in range(self.N):
            uk = z[2*k:2*k+2]
            x = self.vehicle_model(x, uk)

            v = x[3]

            cons += [
                self.limits['vMax'] - v,
                v - self.limits['vMin']
            ]

        return np.array(cons)

    # ================= SOLVER =================
    def solve(self, x0, last_u, refH):

        z0 = np.tile(last_u, self.N)

        bounds = []
        for _ in range(self.N):
            bounds.append((self.limits['deltaMin'], self.limits['deltaMax']))
            bounds.append((self.limits['aMin'], self.limits['aMax']))

        constraints = {
            'type': 'ineq',
            'fun': lambda z: self.constraints(z, x0, last_u)
        }

        res = minimize(
            fun=lambda z: self.cost(z, x0, last_u, refH),
            x0=z0,
            bounds=bounds,
            constraints=constraints,
            method='SLSQP',
            options={
                'maxiter': 50,
                'ftol': 1e-3,
                'disp': False
            }
        )

        if not res.success:
            print("⚠️ MPC failed:", res.message)

        u0 = res.x[0:2]
        return u0

    # ================= UTILS =================
    @staticmethod
    def wrap_to_pi(a):
        return (a + np.pi) % (2*np.pi) - np.pi