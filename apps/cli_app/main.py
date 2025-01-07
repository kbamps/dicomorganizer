import argparse
import csv
import os
import sys
from __VERSION__ import __VERSION__
import log_config as log_config
from dicomorganizer import DicomManager
from pydicom.datadict import tag_for_keyword, keyword_for_tag


def main():
    
    # Setup argument parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
        description=f"""
        Anonymize and manage DICOM series files.

        This tool allows you to anonymize a series of DICOM files by removing or replacing sensitive metadata fields 
        (tags) while maintaining the integrity of the dataset. The processed files are saved to a specified output 
        directory, with support for parallel processing to handle large datasets efficiently.

        Key Features:
        - Remove sensitive DICOM tags specified in a text file.
        - Replace patient identifiers with unique anonymized identifiers from a CSV file.
        - Utilize multiple workers for faster processing.

        Example Usage:
        ###############

        Basic usage to anonymize a dataset:
        DICOMAnonymizer.exe /path/to/input/ /path/to/output/ /path/to/tags.txt 

        Usage with an identifier CSV file and custom log directory:
        DICOMAnonymizer.exe /path/to/input/ /path/to/output/ /path/to/tags.txt \\
            --identifier_list_csv /path/to/identifiers.csv \\
            --num_workers 4 \\
            --logdir /path/to/logs/

        Version: {__VERSION__}
        """
    )
    
    parser.add_argument('input_path', type=str, help="Path to the input DICOM directory.")
    parser.add_argument('output_path', type=str, help="Path to the output directory for anonymized DICOM files.")
    parser.add_argument('drop_tags_txt', type=str, help="Path to the text file containing DICOM tags to drop.")
    parser.add_argument('--identifier_list_csv', type=str, help="Path to the csv file containing identifiers.", required=False, default=None)
    parser.add_argument('--num_workers', type=int, default=2, help="Number of workers for parallel processing. (default: 2)")
    parser.add_argument('--logdir', type=str, default=None, help="Path to the directory where log files will be saved. (default: script directory)")
    

    try:
        args = parser.parse_args() # '/DATASERVER/MIC/GENERAL/STAFF/kbamps4/workspace/uzl/DicomOrganizer/tests/data/cli_app/DICOM /DATASERVER/MIC/GENERAL/STAFF/kbamps4/workspace/uzl/DicomOrganizer/tests/data/cli_app/out_test tests/data/cli_app/tags.txt --identifier_list_csv tests/data/cli_app/identifier.csv  --num_workers 2'.split() if (sys.gettrace() is not None) else [])
    except SystemExit:
        print("\n")
        parser.print_help()
        sys.exit(1)
        
    input_path = args.input_path
    output_path = args.output_path
    drop_tags_txt = args.drop_tags_txt
    identifier_list_csv = args.identifier_list_csv
    num_workers = args.num_workers
    log_dir = args.logdir
    
    # Initialize logging
    logger = log_config.setup_logging(log_dir)
    
    # check if input path exists
    if not os.path.exists(input_path):
        logger.error(f"Input path '{input_path}' does not exist.")
        sys.exit(1)
    
    # Check that output path is either empty or does not exist
    if os.path.exists(output_path): 
        if len(os.listdir(args.output_path)) != 0:
            logger.error(f"Output path '{output_path}' is not empty.")
            sys.exit(1)
    else:
        os.makedirs(output_path, exist_ok=True)
    
    # Check that drop tags file exists
    if not os.path.exists(drop_tags_txt):
        logger.error(f"Drop tags file '{drop_tags_txt}' does not exist.")
        sys.exit(1)
    
    # Check that identifier list file exists
    if not os.path.exists(identifier_list_csv) and identifier_list_csv is not None:
        logger.error(f"Identifier list file '{identifier_list_csv}' does not exist.")
        sys.exit(1)
    
    # Check that the number of workers is a positive integer
    if num_workers < 1:
        logger.error(f"Number of workers ({num_workers}) must be a positive integer. ")
        sys.exit(1)
        
    logger.info(f"Input path: {input_path}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Drop tags file: {drop_tags_txt}")
    logger.info(f"Number of workers: {num_workers}")
    logger.info(f"Identifier list file: {identifier_list_csv}")
    logger.info(f"Log directory: {log_dir}")
    
    # Start the anonymization process
    logger.info("Starting anonymization process...")
    
    # load the identifiers
    identifiers = {}
    with open(identifier_list_csv, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            identifiers[row[0]] = row[1]
    
    drop_tags = []
    with open(drop_tags_txt, 'r') as f:
        drop_tags = f.read().splitlines()
        
    processed_drop_tags = []
    for tag in drop_tags:
        try:
            processed_tag = keyword_for_tag(tag) if keyword_for_tag(tag) is not None else int(tag, 16)
            processed_drop_tags.append(processed_tag)
        except Exception as e:
            logger.error(f"Error processing drop tag '{tag}': {e}")
            
    drop_tags = processed_drop_tags
    
    tags = DicomManager.DEFAULT_DICOM_TAGS + drop_tags
    manager = DicomManager(input_path, tags=tags, num_workers=num_workers)
    
    # Anonymize the DICOM files
    result = manager.anonymize_dicom(output_path, clear_tags=drop_tags, num_workers=num_workers, identifiers=identifiers)
    
    logger.info("Anonymization completed.")
    
    
    
    
if __name__ == '__main__':
    main()