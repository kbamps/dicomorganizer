import argparse
import csv
import os
from pathlib import Path
import sys
import re
import pandas as pd
from apps.cli.utils import log_config
from dicomorganizer import DicomManager
from pydicom.datadict import tag_for_keyword, keyword_for_tag
import json

def validate_filters(filters):
    valid_filters = {}
    for filter in filters:
        if '=' not in filter:
            raise ValueError(f"Filter '{filter}' is not in the correct format key=value.")
        key, value = filter.split('=', 1)
        try:
            valid_filters[key] = re.compile(value)
        except re.error as e:
            raise ValueError(f"Invalid regular expression '{value}' for key '{key}': {e}")
    return valid_filters

def organize_dicom(input_dir, output_dir, groupby="SeriesInstanceUID", anonymize=False, verbose=False, log_dir="logs", num_workers=1, save_output_json=False, filters=None, save_csv=False):
    # Initialize logging
    logger = log_config.setup_logging(log_dir)

    # Debug: Print arguments if verbose mode is on
    if verbose:
        logger.info("Arguments Received:")
        logger.info(f"      Input Directory: {input_dir}")
        logger.info(f"      Output Directory: {output_dir}")
        logger.info(f"      Group by: {groupby}")
        logger.info(f"      Anonymize: {anonymize}")
        logger.info(f"      Verbose Mode: {verbose}")
        logger.info(f"      Number of Workers: {num_workers}")
        logger.info(f"      Save Output JSON: {save_output_json}")
        logger.info(f"      Save CSV: {save_csv}")
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
        def filter_by(row):
            for key, regex in filters.items():
                value = row.get(key, None)  # Get value, default to empty string
            
                if  value is None:  # If value is None or empty string
                    return False  
                
                if not regex.search(value):  # If regex does NOT match
                    return False  # Row does not match filter criteria

            return True
        
        manager.filter(filter_by)
    
    # Organize the DICOM files
    dict_results_folder_export = manager.export_to_folder_structure(output_dir + "/DCM")

    # transform to nifti 
    dict_results_nii_export = manager.export_to_nifti(output_dir, folder_exists=True)
    
    if save_output_json:
        json_output_path = os.path.join(output_dir, "output_results.json")
        with open(json_output_path, 'w') as json_file:
            json.dump({
                "folder_export": dict_results_folder_export,
                "nii_export": dict_results_nii_export
            }, json_file, indent=4)
        logger.info(f"Output results saved to {json_output_path}")
        
    if save_csv:
        # Define the headers
        headers = [
            "id", "patient_name", "patient_id", "study_id", "study_description",
            "study_date", "acquisition_date", "protocol", "modality", "series_number",
            "series_description", "series_instance_uid", "nii_path"
        ]

        # Create an empty DataFrame
        df = pd.DataFrame(columns=headers)

        # Assuming `manager.df_dicom` is available
        rows = []
        for i, (sid, series) in enumerate(manager.df_dicom, start=1):
            row = series.iloc[0]
            
            nii_path = f"{row['PatientID']}/{row['Modality']}/{row['StudyDate']}/{row['SeriesNumber']}_{row['SeriesDescription']}/image.nii.gz"
            
            # Collect data in a list of dictionaries
            rows.append({
                "id": i,
                "patient_name": row["PatientName"],
                "patient_id": row["PatientID"],
                "study_id": row["StudyID"],
                "study_description": row["StudyDescription"],
                "study_date": row["StudyDate"],
                "acquisition_date": row["AcquisitionDate"],
                "protocol": row["ProtocolName"],
                "modality": row["Modality"],
                "series_number": row["SeriesNumber"],
                "series_description": row["SeriesDescription"],
                "series_instance_uid": row["SeriesInstanceUID"],
                "nii_path": nii_path
            })

        # Convert list of dictionaries to DataFrame
        df = pd.DataFrame(rows, columns=headers)

        # Define the file path
        file_path = Path(output_dir.split('$')[0]) / "organized_dicoms_output.csv"

        # Save the DataFrame to CSV
        df.to_csv(file_path, index=False)         
        
        
    logger.info("DICOM organization process completed.")
        
    return dict_results_folder_export, dict_results_nii_export
    
def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=f"""
        Load DICOM files and sort them by the specified grouping parameter (default: series ID).
        Instances are saved to the output folder with the structure:
          id/studydate/series_description/

        Example Usage:
        ###############
        
        Basic usage to organize a dataset:
          dicomorganizer /path/to/input/ /path/to/output/

        To anonymize the dataset:
          dicomorganizer /path/to/input/ /path/to/output/ --anonymize
        """
    )
    
    # Positional arguments
    parser.add_argument(
        "input_dir", 
        type=str, 
        help="Path to the input DICOM directory."
    )
    parser.add_argument(
        "output_dir", 
        type=str, 
        help="Path to the output directory."
    )

    # Optional arguments
    parser.add_argument(
        "--groupby", 
        type=str, 
        default="SeriesInstanceUID", 
        help="Parameter to group instances by (default: SeriesInstanceUID)."
    )
    parser.add_argument(
        "--anonymize", 
        action="store_true", 
        help="Anonymize DICOM files."
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true", 
        help="Enable verbose output."
    )
    parser.add_argument(
        "--log_dir", 
        type=str, 
        default="logs", 
        help="Directory to save log files (default: logs)."
    )
    parser.add_argument(
        "--num_workers", 
        type=int, 
        default=1, 
        help="Number of workers for processing (default: 1)."
    )
    
    parser.add_argument(
        "--save_output_json",
        action="store_true",
        help="Save the output as a JSON"
    )
    
    parser.add_argument(
        "--filters", 
        nargs='*', 
        help="Filters in the format key1=value1 key2=value2 ..."
    )
    
    parser.add_argument(
        "--save_csv",
        action="store_true",
        help="Save the output as a CSV"
    )

    args = parser.parse_args()

    organize_dicom(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        groupby=args.groupby,
        anonymize=args.anonymize,
        verbose=args.verbose,
        log_dir=args.log_dir,
        num_workers=args.num_workers,
        save_output_json=args.save_output_json,
        filters=args.filters,
        save_csv=args.save_csv
    )

if __name__ == "__main__":
    main()
