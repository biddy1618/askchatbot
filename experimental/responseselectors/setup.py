"""To install all packages into the environment.
 Two install options: 
 (1) python -m pip install -e .   # editable 
 (2) python -m pip install .
"""
from setuptools import setup, find_packages

setup(
    name="responseselectors",
    version="0.0.3",
    url="",
    author="",
    author_email="",
    description="ResponseSelectors for Ask Extension Data",
    packages=find_packages(),
    install_requires=[],
)
