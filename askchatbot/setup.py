"""To install all packages into the environment.
 Two install options: 
 (1) python -m pip install -e .   # editable 
 (2) python -m pip install .
"""
from setuptools import setup, find_packages

setup(
    name="askchatbot",
    version="0.0.3",
    url="",
    author="",
    author_email="",
    description="Askchatbot with Rasa & Elasticsearch",
    packages=find_packages(),
    install_requires=[],
)
