import json
import logging
import os
from pathlib import Path
import re
import shutil
import sqlite3
import numpy as np
import pandas as pd
import pydicom
import pickle
from dicomorganizer.utils import create_dicommanager_filter, extract_format, parallel_tasks, validate_filters

logger = logging.getLogger(__name__)

class DicomManager:
    """
    A class to manage DICOM files, extract metadata, and handle operations on them.

    Attributes:
        directory (str): Path to the directory containing DICOM files.
        tags (list): List of DICOM tags to extract.
        DEFAULT_DICOM_TAGS (list): Default tags to extract if no custom tags are specified.
        CLEAR_TAGS (list): Tags that can be cleared to anonymize DICOM files.
    """

    DEFAULT_DICOM_TAGS = [
        "PatientName", "PatientID", "StudyID", "StudyDate", "StudyDescription", "AcquisitionDate","ProtocolName",
        "SOPInstanceUID", "SeriesInstanceUID", "Modality", 
        "BurnedInAnnotation", "SOPClassUID", "StudyInstanceUID", "SeriesDescription", "SeriesNumber","InstanceNumber","Manufacturer",
    ]
    
    CLEAR_TAGS = [
        "PatientBirthDate", "PatientAge", "InstitutionName", 
        "StationName", "StudyID", "AccessionNumber", 
        "SeriesDescription", "StudyDescription"
    ]

    def __init__(self, directory, tags=None, group_by=None, num_workers=None, *args, **kwargs):
        """
        Initializes the DicomManager class, which is used to manage DICOM files, 
        extract metadata, and handle operations such as filtering and anonymization.

        Args:
            directory (str): 
                Path to the directory containing DICOM files. The directory will be 
                recursively searched for DICOM files (excluding 'DICOMDIR').
            
            tags (list, optional):
                A list of DICOM tags to extract from each DICOM file. Defaults to 
                `DEFAULT_DICOM_TAGS` if not provided. These tags define the metadata 
                to be extracted from each file.
            
            group_by (str or list, optional):
                Column name to group the resulting DataFrame by. This is an optional 
                argument that can be specified when calling methods that return 
                DataFrame results (e.g., `df_dicom`). If provided, the DataFrame will 
                be grouped by the specified column.
            
            num_workers (int, optional):
                The number of threads (workers) to use for parallel processing when 
                extracting DICOM metadata or performing tasks like anonymization. If 
                not provided, processing will be done sequentially.
            
            *args:
                Additional positional arguments to pass to any methods that need them.
            
            **kwargs:
                Additional keyword arguments to pass to any methods that need them. 
                This includes options like `group_by` which can be passed dynamically.
            
        """
         
        self.directory = directory
        self.tags = tags or self.DEFAULT_DICOM_TAGS
        self.num_workers = num_workers
        self.group_by = group_by
        self.args = args
        self.kwargs = kwargs
        self._df_dicom = None  # Lazy-loaded DataFrame to store DICOM metadata.
        
        
        
    @property
    def df_dicom(self):
        """
        Lazily loads and returns a pandas DataFrame containing DICOM metadata.

        Returns:
            pd.DataFrame: DataFrame containing DICOM metadata.
        """
        num_workers = self.num_workers
        group_by = self.group_by
        
        if self._df_dicom is None:
            self._df_dicom = self._get_dicom_info(num_workers=num_workers, group_by=group_by)
        return self._df_dicom
    
    
    def filter(self, filter_func, inplace=False):
        """
        Filters the DICOM DataFrame based on a provided filter function.
        
        Args:
            filter_func (function): A function that takes a row of the DataFrame and returns a boolean value.
        
            # Example filter function
            def filter_by_modality(row):
                return row['Modality'] == 'CT'
        
        Returns:
            pd.DataFrame: Filtered DataFrame containing only the rows for which the filter function returned True.
        """
        if not callable(filter_func):
            raise ValueError("The provided filter_func must be a callable function.")
        
        #first ungroup the DataFrame if it is grouped
        if isinstance(self.df_dicom, pd.core.groupby.DataFrameGroupBy):
            df = self._df_dicom.obj
        else:
            df = self._df_dicom
            
        # Apply the filter function to each row of the DataFrame
        df_filtered = df[df.apply(filter_func, axis=1)]
        
        self._df_dicom = df_filtered.groupby(self.group_by) if self.group_by else df_filtered
        return self._df_dicom
    
    
    def anonymize_dicom(self, output_directory, clear_tags=None, num_workers=None, identifiers=None):
        """
        Anonymizes the DICOM files by clearing the provided tags which are in the self.df_dicom.

        Args:
            output_directory (str): Path to save the anonymized files.
            clear_tags (list): A list of tags to clear from the DICOM files. If None, uses the class's CLEAR_TAGS.
            num_workers (int): Number of workers for parallel processing. If None, runs sequentially.
            
        Returns:
            list: A list of file paths of the anonymized DICOM files.
        """
        clear_tags = clear_tags or self.CLEAR_TAGS  # Use the class's CLEAR_TAGS if no custom tags are provided
        
        assert os.path.exists(output_directory), f"Output directory '{output_directory}' does not exist."
        assert output_directory != self.directory, "Output directory cannot be the same as the input directory."

        # List to keep track of the anonymized files
        anonymized_files = []
        
        #first ungroup the DataFrame if it is grouped
        if isinstance(self.df_dicom, pd.core.groupby.DataFrameGroupBy):
            df = self.df_dicom.obj
        else:
            df = self.df_dicom
        
        # Get all DICOM file paths from the self.df_dicom DataFrame
        dicom_paths = df['filename'].tolist()

        # Prepare arguments for parallel tasks
        args_list = [(path, clear_tags, output_directory, identifiers) for path in dicom_paths]
        
        # Parallelize the anonymization task
        if num_workers is None:
            # Run sequentially if num_workers is not provided
            for args in args_list:
                result = self._anonymize_single_dicom(*args)
                if result:
                    anonymized_files.append(result)
        else:
            # Run in parallel if num_workers is specified
            results = parallel_tasks(self._anonymize_single_dicom, args_list, num_workers, description="Anonymizing DICOM files")
            anonymized_files.extend([r for r in results if r is not None])

        return anonymized_files
        

    def _get_dicom_info(self, group_by=None, num_workers=None):
        """
        Reads all DICOM files in the directory and returns their metadata as a pandas DataFrame.

        Args:
            group_by (str, list, optional): Column name to group the data by. Defaults to None.
            num_workers (int, optional): Number of threads for parallel processing. Defaults to None.

        Returns:
            pd.DataFrame or pd.core.groupby.DataFrameGroupBy: 
                DataFrame containing DICOM metadata, optionally grouped by the specified column.
        """
    
        
        dicom_info = self._get_dicom_info_parallel(self.tags, num_workers)
        df_dicom = pd.DataFrame(dicom_info)
        
        if group_by is not None:
            # Check if group_by columns are present in DICOM metadata
            group_by_list = group_by if isinstance(group_by, list) else list([group_by])
            col_check = [col in df_dicom.columns for col in group_by_list]
            if not all(col_check):
                error_message = ','.join([col_name for col_name, check in zip(group_by_list, col_check) if not check])
                raise ValueError(
                        f"Group by '{error_message}' not found in DICOM metadata. Available columns: {df_dicom.columns}"
                    )
                
            return df_dicom.groupby(group_by)
        
        return df_dicom

    def _get_dicom_info_parallel(self, tags, num_workers):
        """
        Retrieves DICOM metadata from multiple files in parallel.

        Args:
            tags (list): List of DICOM tags to extract from each file.
            num_workers (int): Number of threads to use for parallel processing. If None, processing is done sequentially.

        Returns:
            list[dict]: A list of dictionaries, each containing metadata for a single DICOM file. 
                        Returns an empty list if no valid DICOM files are found.
        """
        dicom_paths = self._get_dicom_file_paths()
        args_list = [(path, tags) for path in dicom_paths]
        
        if num_workers is None:
            result =  [self._get_single_dicom_info(*args) for args in args_list]
            return [r for r in result if r is not None]
        
        results = parallel_tasks(self._get_single_dicom_info, args_list, num_workers, description="Reading DICOM files")
        return [r for r in results if r is not None]

    def _get_dicom_file_paths(self):
        """
        Recursively collects all DICOM file paths from the specified directory (self.directory).

        Returns:
            list[str]: A list of file paths pointing to DICOM files in the directory.
                       Excludes files named 'DICOMDIR'.
        """
        dicom_paths = []
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.upper() == "DICOMDIR":
                    continue
                dicom_paths.append(os.path.join(root, file))
        return dicom_paths

    def _get_single_dicom_info(self, filepath, tags, default_value=None):
        """
        Reads metadata for a single DICOM file.

        Args:
            filepath (str): Path to the DICOM file to read.
            tags (list): List of DICOM tags to extract.

        Returns:
            dict: A dictionary containing the extracted metadata for the specified DICOM file. 
                  Includes an 'error' key if an exception occurs or the file is invalid.
        """
        try:
            dicom_data = pydicom.dcmread(filepath, specific_tags=tags, stop_before_pixels=True)
        except pydicom.errors.InvalidDicomError:
            return None
        except Exception as e:
            return {'error': str(e)}

        dicom_info = {tag: dicom_data.get(tag, default_value) for tag in tags}
        dicom_info["filename"] = filepath
        return dicom_info

    
    def _anonymize_single_dicom(self, dicom_path, clear_tags, output_directory, identifiers=None):
        """
        Anonymizes a single DICOM file by clearing specified tags.

        Args:
            dicom_path (str): Path to the DICOM file to anonymize.
            clear_tags (list): List of tags to clear.
            output_directory (str): Directory to save the anonymized file.
            identifiers (dict, optional): A dictionary mapping patient IDs (keys) to anonymized IDs (values). 
                                      If provided, the function replaces the PatientID and PatientName 
                                      in the DICOM file with the corresponding anonymized ID.

        Returns:
            str: Path to the anonymized DICOM file, or None if the process fails.
        """
        try:
            # Read the DICOM file
            dicom_data = pydicom.dcmread(dicom_path)
            
            # Get the patient ID 
            patient_id = dicom_data.PatientID

            # Clear specified tags
            for tag in clear_tags:
                if tag in dicom_data:
                    dicom_data[tag].value = ""
            
            # Anonymize the patient name and ID
            if identifiers is not None:
                if patient_id in identifiers:
                    anonymized_id = identifiers[patient_id]
                    dicom_data.PatientName = anonymized_id
                    dicom_data.PatientID = anonymized_id 
                else:
                    raise KeyError(f"Patient ID '{patient_id}' not found in the provided identifiers.")
             
            # Determine the output file path
            output_path = extract_format(os.path.join(output_directory, "$PatientID$/$StudyDate$/$SeriesDescription$"), dicom_data)
            os.makedirs(output_path, exist_ok=True)
                        
            # Save the anonymized DICOM file
            dicom_data.save_as(os.path.join(output_path, os.path.basename(dicom_path)))
            
            return output_path
        except Exception as e:
            logger.error(f"Failed to anonymize {dicom_path}:\n => {e}")
            return None
        
    
    def export_to_folder_structure(self, output_path, num_workers=None):
        """
        Exports the DICOM files to a folder structure based on the metadata.

        Args:
            output_path (str): Path to the directory where the files will be exported.
            num_workers (int, optional): Number of workers for parallel processing. If None, runs sequentially.
        """
        paths = []
        failed_files = []

        arg_list = [(output_path, r) for r in self.df_dicom.obj.to_dict(orient="records")]
        results = parallel_tasks(export_single_file, arg_list, num_workers, description="Copying DICOM files")

        for result in results:
            if "succeeded" in result:
                paths.append(result["succeeded"])
            elif "failed" in result:
                failed_files.append(result["failed"])        

        return {'succeeded': paths, 'failed': failed_files}

    # def export_to_nifti(self, output_path, folder_exists=False):
    #     """
    #     Exports the DICOM files to NIFTI format.
    #     Args:
    #         output_path (str): Path to the directory where the files will be exported.
    #     """
    #     if not isinstance(self.df_dicom, pd.core.groupby.DataFrameGroupBy):
    #         raise ValueError("Cannot export to NIFTI format without grouping the DICOM files.")
        
    #     converted_files =  []
    #     failed_files = []
        
    #     for group, df_group in tqdm.tqdm(self.df_dicom, desc="Converting DICOMs to NIFTI"):
    #         try:
    #             dicom_data = df_group.iloc[0].to_dict()
    #             read_path_format = extract_format(output_path + "/DCM", dicom_data)
    #             output_path_format = extract_format(output_path, dicom_data)
    #             output_file = os.path.join(output_path_format, f"image.nii.gz")

    #             if folder_exists:
    #                 convert_result = dicom2nifti.dicom_series_to_nifti(read_path_format, output_file, reorient_nifti=False)
    #             else:
    #                 dicom_array = [pydicom.dcmread(dicom_path) for dicom_path in df_group['filename'].tolist()]
    #                 convert_result = dicom_array_to_nifti(dicom_array, output_file, reorient_nifti=False)
                
                
    #             # swap axes 
    #             # if convert_result is not None:
    #             #     nii = np.transpose(convert_result['NII'].get_fdata(), (1,2,3,0))
    #             #     affine = convert_result['NII'].affine
    #             #     convert_result['NII'] = nib.Nifti1Image(nii, affine)
    #             #     nib.save(convert_result['NII'], output_file)
                
    #             dicom_data['nii_path'] = convert_result["NII_FILE"]
    #             dicom_data.pop('filename', None)
    #             converted_files.append(dicom_data)
                    
    #         except Exception as e:
    #             print(f"Failed to convert DICOMs to NIFTI:\n => {e}")
    #             failed_files.append((e, group))

    #     return {'succeeded': converted_files, 'failed': failed_files}


    def to_sqlfile(self, dbfile, columns=["patient_name", "patient_id", "study_id", "study_date", "study_description", "acquisition_date", "protocol", "modality", "series_description", "series_number","series_instance_uid"]):
        """
        Converts the DicomManager instance to a SQL file.

        Args:
            file (str): Path to the output SQL file.
            columns (list): List of columns to include in the SQL file.
        """
        # Mapping from DICOM tags to desired column names
        tag_map = {
            "PatientName": "patient_name",
            "PatientID": "patient_id",
            "StudyID": "study_id",
            "StudyDate": "study_date",
            "StudyDescription": "study_description",
            "AcquisitionDate": "acquisition_date",
            "ProtocolName": "protocol",
            "Modality": "modality",
            "SeriesDescription": "series_description",
            "SeriesNumber": "series_number",
            "SeriesInstanceUID": "series_instance_uid"
        }

        this_dir = Path(__file__).resolve().parent
        db_template = this_dir / "patients.db"

        dbfile = Path(dbfile)

        if not dbfile.exists():
            shutil.copy(db_template, dbfile)

        # Rename and subset
        df_renamed =self.df_dicom.first().reset_index().rename(columns=tag_map)
        df_subset = df_renamed[list(tag_map.values())]
        df_subset = df_subset.astype(str)
        df_subset["series_description"] = df_subset["series_description"].str.replace(" ","_")
        if df_renamed["Manufacturer"].iloc[0] == "SIEMENS":
            df_subset["nii_path"] = (
                df_subset["patient_id"] + "/" +
                df_subset["modality"] + "/" +
                df_subset["study_date"] + "/" +
                df_subset["series_description"] + "/" +
                "image.nii.gz"
            )
        else:
            df_subset["nii_path"] = (
                df_subset["patient_id"] + "/" +
                df_subset["modality"] + "/" +
                df_subset["study_date"] + "/" +
                df_subset["series_number"] + "_" + df_subset["series_description"] +
                "/image.nii.gz"
            )
        
        # Append to SQL
        conn = sqlite3.connect(dbfile) 
        df_subset.to_sql("patients", conn, if_exists="append", index=False)
        conn.close()

    def save(self, output_path):
        """
        Saves the complete DicomManager model to a pickle file.

        Args:
            output_path (str): Path to the output pickle file.
        """
        with open(output_path, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(input_path):
        """
        Loads the complete DicomManager model from a pickle file.

        Args:
            input_path (str): Path to the input pickle file.

        Returns:
            DicomManager: The loaded DicomManager instance.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"The file '{input_path}' does not exist.")
        
        with open(input_path, 'rb') as f:
            return pickle.load(f)


        
def organize_dicom(input_dir, output_dir, groupby="SeriesInstanceUID", anonymize=False, verbose=False, log_dir="logs", num_workers=1, filters=None, scan_mode=False):
    # Initialize logging
    # logger = log_config.setup_logging(log_dir)  # Remove this line

    # Debug: Print arguments if verbose mode is on
    if verbose:
        logger.info("Arguments Received:")
        logger.info(f"      Input Directory: {input_dir}")
        logger.info(f"      Output Directory: {output_dir}")
        logger.info(f"      Group by: {groupby}")
        logger.info(f"      Anonymize: {anonymize}")
        logger.info(f"      Verbose Mode: {verbose}")
        logger.info(f"      Number of Workers: {num_workers}")
        logger.info(f"      Filters: {filters}")

    # Validate filters
    try:
        filters = validate_filters(filters) if filters else {}
    except ValueError as e:
        logger.error(str(e))
        return

    # Check if paths exist
    if not os.path.exists(input_dir):
        logger.error(f"Input path '{input_dir}' does not exist.")
        return

    # check if groupby parameters is in tags of DicomManager
    if groupby not in DicomManager.DEFAULT_DICOM_TAGS:
        logger.error(f"Group by parameter '{groupby}' is not a valid tag.\nValid tags are: {DicomManager.DEFAULT_DICOM_TAGS}")
        return

    # Start the DICOM organization process
    logger.info("Starting DICOM organization process...")
    manager = DicomManager(directory=input_dir, group_by=groupby, num_workers=num_workers)
    
    # Apply filters
    if filters:
        filter_by = create_dicommanager_filter(filters)
        manager.filter(filter_by)

    # if scan mode is enabled, print the summary and exit
    if scan_mode:
        logger.info("Scan mode enabled. Printing summary of DICOM files...")
        df_dicom = manager.df_dicom

        # Group by the groupby parameter and collect all rows as dicts
        if isinstance(df_dicom, pd.core.groupby.DataFrameGroupBy):
            groups = []
            # aggregate the grouped DataFrame into a list of dictionaries
            # each record will contain the first of the groupby column
            df_group_level = df_dicom.first().reset_index()
            for index, row in df_group_level.iterrows():
                groups.append(row.to_dict())
        else:
            # If not grouped, treat all as one group
            groups = df_dicom[DicomManager.DEFAULT_DICOM_TAGS].to_dict(orient="records")
            
        print(json.dumps(groups, indent=2, default=str))
        logger.info(f"Total DICOM files found: {len(df_dicom)}")
        return
    
    # Organize the DICOM files
    results = manager.export_to_folder_structure(output_dir + "/DCM", num_workers)

    # transform to nifti 
    # manager.export_to_nifti(output_dir, folder_exists=True)
    return results


def export_single_file(output_path, row):
    output_path = Path(output_path)
    try:
        dicom_path = Path(row['filename'])
        dicom_data = row
        output_path_formatted = Path(extract_format(output_path.as_posix(), dicom_data))
        name = dicom_path.name
        output_path_formatted.mkdir(parents=True, exist_ok=True)
        output_file = output_path_formatted / name
        shutil.copy(dicom_path.as_posix(), output_file.as_posix())

        dicom_data['filename'] = output_file.as_posix()
        return {"succeeded": output_file}
    except Exception as e:
        return {"failed": (e, dicom_path)}
            

if __name__ == '__main__':
    # %%
    manager = DicomManager(directory="/DATASERVER/MIC/GENERAL/STAFF/kbamps4/workspace/data/excmr/Exc_validation_cohort/pred/BREXIT", group_by=["SeriesDescription", "PatientID"],num_workers=30)
    # %%
    manager.to_sqlfile("/DATASERVER/MIC/GENERAL/STAFF/kbamps4/workspace/projects/2024_excmr/libs/dicomorganizer/tests/patients.db")
    pass