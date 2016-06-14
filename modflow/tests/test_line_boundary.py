# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 16:19:59 2016

@author: aybulat
"""

import unittest
from imports.utils import line_boundary_interpolation


class Test_line_area_intersector(unittest.TestCase):

    def setUp(self):
        self.points = [[0., 0.], [400., 300.]]
        self.nx, self.ny = 11, 11
        self.point_vals = [[50,100], [50,100], [50,100]]
        self.stress_period_list = [0, 1, 2]
        self.interract_layers = [0, 1]
        self.xmin, self.xmax, self.ymin, self.ymax = 0., 400., 0., 400.
        self.line = [[0., 0.], [0., 300.], [400., 300.],
                     [400., 0.], [0., 0.]]
        self.layers_botm = [0,-10]
        self.strt_head_mode = 'warmed_up'
        self.stress_period_data = line_boundary_interpolation.give_SPD(self.points,
                                                                 self.point_vals,
                                                                 self.line,
                                                                 self.stress_period_list,
                                                                 self.interract_layers,
                                                                 self.xmax, self.xmin,
                                                                 self.ymax, self.ymin,
                                                                 self.nx, self.ny,
                                                                 self.layers_botm,
                                                                 self.strt_head_mode)

    def tearDown(self):
        del self

    def test_number_of_stress_periods(self):
        if self.strt_head_mode == 'warmed_up':
            self.assertEqual(len(self.stress_period_data),
                             len(self.stress_period_list) + 1)
        else:
            self.assertEqual(len(self.stress_period_data),
                             len(self.stress_period_list))

    def test_number_of_boundary_cells_in_each_sp(self):
        _boundary_line_lenght = 36
        for i in self.stress_period_list:
            self.assertEqual(len(self.stress_period_data[i]),
                             _boundary_line_lenght * len(self.interract_layers))



if __name__ == '__main__':
    unittest.main()