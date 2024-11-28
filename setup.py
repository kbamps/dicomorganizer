from setuptools import setup, find_packages
from dicomorganizer import __version__

setup(
    name='Dicom Organizer',  # Replace with your package name
    version=__version__,
    author='Kobe Bamps',
    author_email='kobe.bamps@uzleuven.be',
    description="A package to manage, process, and anonymize DICOM files.",  
    long_description=open('README.md').read(), 
    long_description_content_type='text/markdown',  
    url='https://gitlab.kuleuven.be/u0125842/dicomorganizer',  # Replace with your repo URL
    packages=find_packages(),  # Automatically find packages in your project
    install_requires=[
        'tqdm',      # For progress bar functionality
        "pydicom>=2.0.0",  # pydicom is required for DICOM file handling
        "pandas>=1.0.0",  # pandas for DataFrame management
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Adjust based on your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Specify the Python version requirement
)
