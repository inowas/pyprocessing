# -*- coding: utf-8 -*-
"""
Created on Mon Jun 06 11:21:26 2016

@author: aybulat
"""


def give_well_spd(xmin, xmax, ymin, ymax, nx, ny, x, y, rates, layers,
                  strt_mode, stress_periods):
    """

    """
    if len(rates) == 0:
        return []
    else:
        rows = [int(((ymax - i)/(ymax - ymin))*ny) if i > ymin else 0 for i in y]
        cols = [int(((i - xmin)/(xmax - xmin))*nx) if i < xmax else nx for i in x]
        WEL_stress_period_data = {}
        if strt_mode == 'simple':
            for period in stress_periods:
                SPD_single = []
                for i in range(len(rows)):
                    rate = rates[i][period] if len(rates[0]) > 1 else rates[i][0]
                    SPD_single.append([layers[i], rows[i], cols[i], rate])
                WEL_stress_period_data[period] = SPD_single

        elif strt_mode == 'warmed_up':
            for period in stress_periods:
                SPD_single = []
                for i in range(len(rows)):
                    rate = rates[i][period] if len(rates[0]) > 1 else rates[i][0]
                    SPD_single.append([layers[i], rows[i], cols[i], rate])
                if len(WEL_stress_period_data) == 0:
                    WEL_stress_period_data[period] = SPD_single
                WEL_stress_period_data[period + 1] = SPD_single
        else:
            print 'given strt_mode is not supported'
            return

    return WEL_stress_period_data
