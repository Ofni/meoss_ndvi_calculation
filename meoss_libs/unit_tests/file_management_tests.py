import logging
import os
import unittest


from meoss_libs.file_management import list_files, generate_output_file_name

# avoid non pertinent log messages
logger = logging.getLogger('FILE MANAGEMENT')
logger.disabled = True

class TestListFiles(unittest.TestCase):
    """
    Test the list_files function
    """

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.test_file = os.path.join(self.test_dir, 'test_file.txt')

        self.test_subdir = os.path.join(self.test_dir, 'test_subdir')
        self.test_subfile1 = os.path.join(self.test_subdir, 'test_subfile1.txt')
        self.test_subfile2 = os.path.join(self.test_subdir, 'test_subfile2.txt')

        os.makedirs(self.test_subdir)

        with open(self.test_file, 'w') as f:
            f.write('test')

        with open(self.test_subfile1, 'w') as f:
            f.write('test')

        with open(self.test_subfile2, 'w') as f:
            f.write('test')

    def tearDown(self):
        os.remove(self.test_file)
        os.remove(self.test_subfile1)
        os.remove(self.test_subfile2)
        os.rmdir(self.test_subdir)

    def test_list_existing_files(self):
        # Test with an existing file
        files = list_files(pattern=['*file*'], directory=self.test_dir, extension='txt', subfolder=False)
        self.assertEqual(files, [self.test_file])

    def test_list_existing_files_in_subdirectory(self):
        # Test with files exisiting in directory and sub directory
        files = list_files(pattern=['*file1*', '*file2*'], directory=self.test_dir, extension='txt', subfolder=True)
        self.assertEqual(files, [self.test_subfile1, self.test_subfile2])

    def test_list_not_existing_files(self):
        # Test with a not existing file
        files = list_files(pattern=['non_existent_file'], directory=self.test_dir, extension='txt', subfolder=False)
        self.assertEqual(files, [])

    def test_list_not_existing_directory(self):
        # Test with a not existing directory
        files = list_files(pattern=['*'], directory='non_existent_directory', extension='txt', subfolder=False)
        self.assertEqual(files, [])

    def test_list_not_existing_extension(self):
        # Test with a not existing extension
        files = list_files(pattern=['*'], directory=self.test_dir, extension='non_existent_extension')
        self.assertEqual(files, [])


class TestGenerateOutputFileName(unittest.TestCase):
    """
    test the generate_output_file_name function
    """

    def setUp(self):
        self.test_S2_2A_file = 'SENTINEL2A_20231012-105856-398_L2A_T31TCJ_C_V3-1_ATB_R1.tif'
        self.test_S2_2A_ESA_file = 'test_file_ESA.tif'
        self.test_dir = os.path.dirname(os.path.realpath(__file__))

        self.test_S2_2A_file_path = os.path.join(self.test_dir, self.test_S2_2A_file)
        self.test_S2_2A_ESA_file_path = os.path.join(self.test_dir, self.test_S2_2A_ESA_file)

    def test_generate_output_name_with_S22A_format(self):
        # Test with a S2-2A format
        output_file = generate_output_file_name(self.test_S2_2A_file_path, format="S2-2A", prefix='prefix', prefix2='prefix2', suffix='suffix')
        self.assertEqual(output_file, 'prefix_prefix2_T31TCJ_20231012T105856_suffix.tif')

    def test_generate_output_name_with_S22AESA_format(self):
        # Test with a S2-2A-ESA format
        output_file = generate_output_file_name(self.test_S2_2A_ESA_file_path, format="S2-2A-ESA", prefix='prefix', prefix2='prefix2', suffix='suffix')
        self.assertEqual(output_file, 'prefix_prefix2_test_file_suffix.tif')

    def test_generate_output_name_with_no_format(self):
        # Test without format
        output_file = generate_output_file_name(self.test_S2_2A_file, format=None, prefix='prefix', prefix2='prefix2', suffix='suffix')
        self.assertEqual(output_file, 'SENTINEL2A_20231012-105856-398_L2A_T31TCJ_C_V3-1_ATB_R1.no_format.tif')

    def test_generate_output_name_with_unknown_format(self):
        # Test with unknown format
        output_file = generate_output_file_name(self.test_S2_2A_file, format='unknown', prefix='prefix', prefix2='prefix2', suffix='suffix')
        self.assertEqual(output_file, 'SENTINEL2A_20231012-105856-398_L2A_T31TCJ_C_V3-1_ATB_R1.no_format.tif')

    def test_generate_output_name_with_error_format(self):
        # TODO: to implement test with error format
        # need to mock and exception not time for that now !
        pass


if __name__ == '__main__':
    unittest.main()