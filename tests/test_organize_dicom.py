import os
import shutil
import unittest
import pickle
from dicomorganizer.dicom_manager import DicomManager, organize_dicom

class TestOrganizeDicom(unittest.TestCase):
    def setUp(self):
        self.input_dir = 'tests/data/dcm/63146262'
        self.output_dir = 'tests/output/$PatientID$/$Modality$/$StudyDate$/$SeriesNumber$_$SeriesDescription$'
        self.log_dir = 'test/logs'
        self.filters = ['SeriesDescription=^sRLT_(66B|66|50B|50|25B|25|REST|RUST)(?!_FLOW)$']
        self.manager_path = "tests/output/manager.pkl"

        # Create output and log directories if they don't exist
        os.makedirs(self.log_dir, exist_ok=True)

        # if os.path.exists(self.manager_path):
        #     with open(self.manager_path, 'rb') as f:
        #         self.manager = pickle.load(f)
        # else:
        #     self.manager = DicomManager(directory=self.input_dir, group_by="SeriesInstanceUID", num_workers=50)
        #     self.manager.df_dicom
        #     # Save manager to load it in the test to be quicker
        #     with open(self.manager_path, 'wb') as f:
        #         pickle.dump(self.manager, f)


    # def test_load_manager(self):
    #     self.assertIsNotNone(self.manager)


    # def test_iterate(self):
    #     for idx, df_group in self.manager.df_dicom:
    #         print(idx)
    #         print()

    def test_organize_dicom_with_filters(self):

        results = organize_dicom(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            groupby="SeriesInstanceUID",
            anonymize=False,
            verbose=True,
            log_dir=self.log_dir,
            num_workers=25,
            filters=self.filters
            )
        
        print(len(results["succeeded"]))
        print(len(results["failed"]))


        # # Check if output directory is created and contains files
        # self.assertTrue(os.path.exists(self.output_dir))
        # self.assertTrue(len(os.listdir(self.output_dir)) > 0)

        # # Check if NIfTI files are created
        # nifti_files = [f for f in os.listdir(self.output_dir) if f.endswith('.nii') or f.endswith('.nii.gz')]
        # self.assertTrue(len(nifti_files) > 0)

if __name__ == '__main__':
    unittest.main()
