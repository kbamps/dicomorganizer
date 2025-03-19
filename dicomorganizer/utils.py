import concurrent.futures
import re
import sys, os
from tqdm import tqdm
import logging

# Pool =  #concurrent.futures.ThreadPoolExecutor #if os.name == 'nt' else concurrent.futures.ProcessPoolExecutor

logger = logging.getLogger(__name__)

def parallel_tasks(function, arguments_list, num_workers=1, description="processing", show_bar=True, force_single_thread=False):
    """
    Executes a function in parallel using multiple worker processes.
    
    Args:
        function (callable): The function to execute in parallel.
        arguments_list (list): A list of argument tuples to pass to the function.
        num_workers (int, optional): Number of workers to use for parallel execution. Defaults to 1.
        show_bar (bool, optional): Whether to display a progress bar using tqdm. Defaults to True.
        force_single_thread (bool, optional): Forces single-threaded execution, useful for debugging.
    
    Returns:
        list: A list of results from the parallel execution, in the same order as the input argument list.
    """
    force_single_thread = force_single_thread
    disabled = not show_bar
    results_list = [None] * len(arguments_list)  # Preallocate the result list
    total_tasks = len(arguments_list)
    if num_workers is None:
        force_single_thread = True
    else:
        num_workers = min(len(arguments_list), num_workers or 1)
    # Pool = concurrent.futures.ThreadPoolExecutor if os.name == 'nt' else concurrent.futures.ProcessPoolExecutor
    Pool = concurrent.futures.ProcessPoolExecutor

    with tqdm(total=total_tasks, desc=description, unit="item", disable=disabled) as pbar:
        if not force_single_thread:
            with Pool(max_workers=num_workers) as executor:
                futures = {executor.submit(function, *args): idx for idx, args in enumerate(arguments_list)}
                
                for future in concurrent.futures.as_completed(futures):
                    idx = futures[future]  # Get the index for the completed future
                    try:
                        results_list[idx] = future.result()  # Store the result at the correct index
                    except Exception as e:
                        logger.info(f"Unable to get result for task {idx}-{arguments_list[idx]}: {e}")
                    
                    pbar.update(1)
        else:
            for idx, args in enumerate(arguments_list):
                try:
                    results_list[idx] = function(*args)
                except Exception as e:
                    logger.info(f"Unable to get result for task {idx}-{arguments_list[idx]}: {e}")

                pbar.update(1)

    return results_list


def replace_invalid_characters(filename):
    invalid_characters = '<>:"/\|?*'
    reserved_words = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

    # Replace invalid characters with an underscore
    for char in invalid_characters:
        filename = filename.replace(char, '_')

    # Check if filename is a reserved word
    if filename.upper() in reserved_words:
        filename += '_'

    # Remove leading and trailing periods and spaces
    filename = filename.strip('.')
    filename = filename.strip()

    return filename


def extract_format(format_file, dict_format=None):
        pattern = r'\$([^$]+)\$'
        placeholders = re.findall(pattern, format_file)
        
        # Extract DICOM tag values
        # tag_values = {placeholder: dict_format.get(placeholder, '') for placeholder in placeholders}
        
        # Replace placeholders in output_format with actual tag values
        output_file = format_file
        for placeholder in placeholders:
            if '?' in placeholder:
                conditional_tags = placeholder.split('?')
                for ct in conditional_tags:
                    value = dict_format.get(ct, None)
                    if value is not None:
                        break
                

            else:
                value = dict_format.get(placeholder, None)
            
            
            if value is None:
                raise ValueError(f"Placeholder '{placeholder}' not found in dictionary. Pattern: {format_file}")
            
            if value == "":
                raise ValueError(f"Placeholder '{placeholder}' has an empty value. Pattern: {format_file}")
                
            placeholder_str = f"${placeholder}$"
            output_file = output_file.replace(placeholder_str, replace_invalid_characters(str(value)))
            
        
        output_file = output_file.replace(" ", "_")
        return 

def validate_filters(filters):
    """
    Validates and compiles a list of filter strings into a dictionary of regular expressions.

    Args:
        filters (list): A list of strings in the format "key=value", where `key` is the filter key
                        and `value` is a regular expression pattern.

    Returns:
        dict: A dictionary where keys are filter keys and values are compiled regular expressions.

    Raises:
        ValueError: If a filter string is not in the correct format "key=value" or if the regular
                    expression is invalid.
    """
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

def create_dicommanager_filter(filter_str):
    """
    Creates a DICOM filter function from a string in the format ["key1=value1","key2=value2", ...].
    Example: ['SeriesDescription=^sRLT_(66B|66|50B|50|25B|25|REST|RUST)(?!_FLOW)$', ...]

    Args:
        filter_str (list): A list of strings containing key-value pairs in the format key=value.

    Returns:
        function: A function `filter_by(row)` that takes a dictionary `row` and returns True if the row matches the filters, False otherwise.
    """
    # Validate and compile the filters
    filters = validate_filters(filter_str)

    def filter_by(row):
        """
        Filters a row based on the compiled filters.

        Args:
            row (dict): A dictionary representing a row of data.

        Returns:
            bool: True if the row matches all filters, False otherwise.
        """
        for key, regex in filters.items():
            value = row.get(key, None)  # Get value, default to None
            
            if value is None:  # If value is None
                return False  
            
            if not regex.search(value):  # If regex does NOT match
                return False  # Row does not match filter criteria

        return True

    return filter_by

if __name__ == '__main__':
    pass

