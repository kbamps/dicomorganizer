import os
import shutil
import unittest
from apps.cli.dicomorganizer.main import organize_dicom

class TestOrganizeDicom(unittest.TestCase):
    def setUp(self):
        self.input_dir = 'tests/data/dcm'
        self.output_dir = 'tests/output'
        self.log_dir = 'test/logs'
        self.filters = ['SeriesDescription=sRLT']

        # Create output and log directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

    def tearDown(self):
        # Clean up output and log directories after tests
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        if os.path.exists(self.log_dir):
            shutil.rmtree(self.log_dir)

    def test_organize_dicom_with_filters(self):
        organize_dicom(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            groupby="SeriesInstanceUID",
            anonymize=False,
            verbose=True,
            log_dir=self.log_dir,
            num_workers=1,
            filters=self.filters
        )

        # Check if output directory is created and contains files
        self.assertTrue(os.path.exists(self.output_dir))
        self.assertTrue(len(os.listdir(self.output_dir)) > 0)

        # Check if NIfTI files are created
        nifti_files = [f for f in os.listdir(self.output_dir) if f.endswith('.nii') or f.endswith('.nii.gz')]
        self.assertTrue(len(nifti_files) > 0)

if __name__ == '__main__':
    unittest.main()
