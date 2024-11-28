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
    url='https://gitlab.kuleuven.be/u0125842/dicomorganizer',  
    packages=find_packages(),  # Automatically find packages in your project
    install_requires=[
        'tqdm',     
        "pydicom>=2.0.0",  
        "pandas>=1.0.0", 
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Adjust based on your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Specify the Python version requirement
)
