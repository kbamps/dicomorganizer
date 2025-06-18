import argparse
import multiprocessing
import threading

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=f"""
        DicomOrganizer
        
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
        "--filters", 
        nargs='*', 
        help="Filters in the format key1=value1 key2=value2 ..."
    )

    parser.add_argument("--multiprocessing", action="store_true", help="Enable multiprocessing")

    parser.add_argument(
        "--scan", "-scan",
        action="store_true",
        help="Scan the input directory and print a summary without organizing."
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI log display and run organize_dicom in a background thread."
    )

    args = parser.parse_args()

    from dicomorganizer.dicom_manager import organize_dicom
    
    if args.gui:
        from dicomorganizer.apps.cli.dicomorganizer.gui import create_log_display

        def run_organize():
            organize_dicom(
                input_dir=args.input_dir,
                output_dir=args.output_dir,
                groupby=args.groupby,
                anonymize=args.anonymize,
                verbose=args.verbose,
                log_dir=args.log_dir,
                num_workers=args.num_workers,
                filters=args.filters,
                scan_mode=args.scan,
            )
        create_log_display(run_organize)
    else:
        organize_dicom(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            groupby=args.groupby,
            anonymize=args.anonymize,
            verbose=args.verbose,
            log_dir=args.log_dir,
            num_workers=args.num_workers,
            filters=args.filters,
            scan_mode=args.scan,
        )

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
