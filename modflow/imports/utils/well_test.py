# -*- coding: utf-8 -*-
"""
Created on Mon Jun 06 11:58:15 2016

@author: aybulat
"""

from well_spd import give_well_spd

xmin = 0.
xmax = 100.
ymin = 0.
ymax = 100.
nx = 10
ny = 10
x = [0, 30, 75, 100]
y = [0, 50, 85, 100]
#rates = [300,-1000,0, 1000]
rates = [[300,300,700], [100,-1000,0], [700,300,-1000], [800,10,-100]]
layers = [2,2,2,3]
stress_periods = [0,1,2]
strt_mode='warmed_up'
print give_well_spd(xmin, xmax, ymin, ymax, nx, ny,
                  x, y, rates, layers,
                  strt_mode, stress_periods)