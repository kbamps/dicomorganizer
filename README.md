# DicomManager

**DicomManager** is a Python utility for managing, processing, and anonymizing DICOM files. This tool enables you to extract metadata, filter DICOM datasets, and anonymize files with ease using multithreading capabilities.

---

## Features

- Extract metadata from DICOM files, including customizable tags.
- Filter DICOM datasets using user-defined functions.
- Anonymize DICOM files by clearing sensitive metadata.
- Supports parallel processing for faster execution.

---

## Quick Start

```python
from dicomorganizer import DicomManager

# 1. Initialize the DicomManager
directory = "/path/to/dicom/files"
dicom_manager = DicomManager(directory)

# 2. Extract metadata
# Access DICOM metadata as a DataFrame

df = dicom_manager.df_dicom
print(df.head())

# Group Metadata:

# Group the metadata by SeriesInstanceUID
dicom_manager = DicomManager(directory, group_by="SeriesInstanceUID")
grouped_df = dicom_manager.df_dicom
for group, data in grouped_df:
    print(f"Group: {group}")
    print(data)


# 3. Filter DICOM files by modality (e.g., keep only 'CT')
def filter_by_modality(row):
    return row['Modality'] == 'CT'

filtered_df = dicom_manager.filter(filter_by_modality)
print(filtered_df)

# 4. Anonymize DICOM files
output_dir = "/path/to/anonymized/files"
anonymized_files = dicom_manager.anonymize_dicom(output_dir)
print(f"Anonymized {len(anonymized_files)} files.")`


#5. Filter DICOM Files

# Define a filter function
def filter_ct_modality(row):
    return row["Modality"] == "CT"

# Apply the filter
filtered_df = dicom_manager.filter(filter_ct_modality)
print(filtered_df)


# 6. Parallel Processing

dicom_manager = DicomManager(directory="path/to/dicom/folder", num_workers=4)

# Parallel metadata extraction
df = dicom_manager.df_dicom

# Parallel anonymization
anonymized_files = dicom_manager.anonymize_dicom(output_directory=output_directory, num_workers=4)
```

# Additional Information

**Default Tags Extracted**: ["PatientName", "PatientID", "StudyID", "StudyDate", "SOPInstanceUID", "SeriesInstanceUID", "Modality", "BurnedInAnnotation", "SOPClassUID", "StudyInstanceUID"]

**Default Tags Cleared**: ["PatientBirthDate", "PatientAge", "InstitutionName", "StationName", "StudyID", "AccessionNumber", "SeriesDescription", "StudyDescription"]