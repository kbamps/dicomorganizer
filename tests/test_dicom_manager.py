import os
import unittest
from dicomorganizer import DicomManager

class TestDicomManager(unittest.TestCase):

    def setUp(self):
        self.test_directory = "tests/data"
        self.test_tags = ["PatientName", "PatientID", "SeriesDescription"]
        self.test_group_by = "PatientID"
        self.test_num_workers = 50
        
        self.manager_grouped_patientid = DicomManager(directory=self.test_directory, group_by="PatientID", num_workers=self.test_num_workers)

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
        
    # def test_df_dicom(self):
    #     info = self.manager_grouped_patientid.df_dicom
    #     self.assertEqual(len(info), 4)
        
        
    def test_filter(self):
        filter_func = lambda x: x["Modality"] == "US"
        length_before = len(self.manager_grouped_patientid.df_dicom.obj)
        self.manager_grouped_patientid.filter(filter_func)
        length_after = len(self.manager_grouped_patientid.df_dicom.obj)
        self.assertGreater(length_before, length_after)
        self.assertEqual(self.manager_grouped_patientid.df_dicom.obj["Modality"].unique(), ["US"])

if __name__ == "__main__":
    unittest.main()