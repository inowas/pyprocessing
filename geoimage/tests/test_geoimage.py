import unittest
from geoImage import RasterImage
import os
from scipy import misc


class Test_geoimage(unittest.TestCase):

    def setUp(self):
        sample_data_name = 'example_data.json'
        name = 'newimage'
        workspace = 'images'
        self.r = RasterImage()
        self.fileName = os.path.join(workspace, name + '.png')
        if os.path.exists(self.fileName):
            os.remove(self.fileName)
        self.r.from_file(sample_data_name)
        self.r.setOutputFileName(name)
        self.r.makeImage()

    def tearDown(self):
#        if os.path.exists(self.fileName):
#            os.remove(self.fileName)
        self.r = None
        self.fileName = None

    def test_if_file_created(self):
        self.assertTrue(os.path.exists(self.fileName))

    def test_image_properities(self):
        image = misc.imread(self.fileName)
        self.assertEqual(len(image.shape), 3)
        self.assertEqual(image.shape[2], 4)
        self.assertEqual(image.dtype, 'uint8')

if __name__ == '__main__':
    unittest.main()
