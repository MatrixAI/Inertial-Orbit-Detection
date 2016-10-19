import numpy as np

def sine(freq, time, amp, phase, vertical_disp):    
    return amp * np.sin(freq * 2 * np.pi * time + phase) + vertical_disp