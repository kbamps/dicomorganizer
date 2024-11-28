import os
import unittest
from dicomorganizer.dicom_manager import DicomManager

class TestDicomManager(unittest.TestCase):

    def setUp(self):
        self.test_directory = "tests/data"
        self.test_tags = ["PatientName", "PatientID", "SeriesDescription"]
        self.test_group_by = "PatientID"
        self.test_num_workers = 4

    def test_init_with_all_arguments(self):
        manager = DicomManager(
            directory=self.test_directory,
            tags=self.test_tags,
            group_by=self.test_group_by,
            num_workers=self.test_num_workers
        )
        self.assertEqual(manager.directory, self.test_directory)
        self.assertEqual(manager.tags, self.test_tags)
        self.assertEqual(manager.group_by, self.test_group_by)
        self.assertEqual(manager.num_workers, self.test_num_workers)
        self.assertIsNone(manager._df_dicom)

    def test_init_with_default_tags(self):
        manager = DicomManager(directory=self.test_directory)
        self.assertEqual(manager.tags, DicomManager.DEFAULT_DICOM_TAGS)

    def test_init_with_default_num_workers(self):
        manager = DicomManager(directory=self.test_directory)
        self.assertIsNone(manager.num_workers)

    def test_init_with_default_group_by(self):
        manager = DicomManager(directory=self.test_directory)
        self.assertIsNone(manager.group_by)

if __name__ == "__main__":
    unittest.main()