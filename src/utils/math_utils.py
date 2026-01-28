import numpy as np

class SigmoidController:
    def __init__(self, min_gain=1.0, max_gain=15.0, v_inf=25, k=0.2):
        """
        Hyperparameters for Mouse Ballistics:
        min_gain: Precision sensitivity (pixel per pixel).
        max_gain: Speed sensitivity (flicking across screen).
        v_inf: Velocity threshold where behavior switches.
        k: Slope (how snappy the switch is).
        """
        self.min_gain = min_gain
        self.max_gain = max_gain
        self.v_inf = v_inf
        self.k = k

    def get_gain(self, velocity):
        # The Logistic Function (S-Curve)
        return self.min_gain + (self.max_gain - self.min_gain) / (1 + np.exp(-self.k * (velocity - self.v_inf)))

class OneEuroFilter:
    """
    Standard jitter reduction filter for HCI.
    Filters out jitters when hand is slow, reduces lag when hand is fast.
    """
    def __init__(self, min_cutoff=1.0, beta=0.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    def smoothing_factor(self, t_e, cutoff):
        r = 2 * np.pi * cutoff * t_e
        return r / (r + 1)

    def exponential_smoothing(self, a, x, x_prev):
        return a * x + (1 - a) * x_prev

    def __call__(self, x, t):
        if self.x_prev is None:
            self.x_prev = x
            self.t_prev = t
            return x

        t_e = t - self.t_prev
        self.t_prev = t
        
        # Calculate derivative (velocity)
        dx = (x - self.x_prev) / t_e if t_e > 0 else 0
        dx_hat = self.exponential_smoothing(self.smoothing_factor(t_e, 1.0), dx, self.dx_prev)
        
        # Calculate dynamic cutoff
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        
        # Smooth position
        x_hat = self.exponential_smoothing(self.smoothing_factor(t_e, cutoff), x, self.x_prev)
        
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        return x_hat