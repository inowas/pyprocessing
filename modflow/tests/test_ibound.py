import unittest
from imports.utils import ibound


class SimpleWidgetTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_default_widget_size(self):
        snrow = 11
        sncol = 11
        snx, sny = sncol, snrow
        sxmin, sxmax, symin, symax = 0., 400., 0., 400.
        sline = [[0., 0.], [0., 300.], [400., 300.],
                 [400., 0.], [0., 0.]]
        snumber_of_layers = 1
        control = [[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
                    [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
                    [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
                    [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
                    [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
                    [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
                    [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
                    [-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
                    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]]
        returned = ibound.give_ibound(sline, snumber_of_layers,
                           snx, sny, sxmin, sxmax,
                           symin, symax, -1)

        self.assertEqual(returned.tolist(), control)

if __name__ == '__main__':
    unittest.main()
