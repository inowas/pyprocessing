
import unittest
from imports.utils import well_spd

class Test_well_spd(unittest.TestCase):

    def setUp(self):
        self.x = [0, 30, 75, 100]
        self.y = [0, 50, 85, 100]
        self.nx, self.ny = 11, 11
        self.rates = [[300, 300, 700],
                      [100, -1000, 0],
                      [700, 300, -1000],
                      [800, 10, -100]]
        self.stress_periods = [0, 1, 2]
        self.layers = [0, 1, 1, 1]
        self.xmin, self.xmax, self.ymin, self.ymax = 0., 400., 0., 400.

        self.strt_mode = 'warmed_up'
        self.stress_period_data = well_spd.give_well_spd(self.xmin, self.xmax,
                                                         self.ymin, self.ymax,
                                                         self.nx, self.ny,
                                                         self.x, self.y,
                                                         self.rates, self.layers,
                                                         self.strt_mode,
                                                         self.stress_periods)

    def tearDown(self):
        del self

    def test_if_output_equals_to_expected(self):
        if self.strt_mode == 'warmed_up':
            self.assertEqual(len(self.stress_period_data),
                             len(self.stress_periods) + 1)
        else:
            self.assertEqual(len(self.stress_period_data),
                             len(self.stress_periods))

    def test_if_number_of_boundary_cells_is_correct(self):
        for i in self.stress_periods:

            self.assertEqual(len(self.stress_period_data[i]),
                             len(self.x))



if __name__ == '__main__':
    unittest.main()
