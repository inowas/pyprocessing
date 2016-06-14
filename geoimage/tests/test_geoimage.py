import unittest
from geoImage import RasterImage
import os

class Test_geoimage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._r = RasterImage()
    @classmethod
    def tearDownClass(cls):
        cls._r =None

    def test_if_file_created(self):
        sample_data_name = 'example_data.json'
        name = 'newimage'
        workspace = 'images'
        fileName = os.path.join(workspace, name)
        if os.path.exists(fileName):
            os.remove(fileName)
        self._r.from_file(sample_data_name)
        self._r.setOutputFileName(name)
        result = self._r.makeImage()
        self.assertTrue(os.path.exists(fileName + '.png'))

if __name__ == '__main__':
    unittest.main()
