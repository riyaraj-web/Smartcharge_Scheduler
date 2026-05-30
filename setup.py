"""
Setup file for the scheduler package
"""

from setuptools import setup, find_packages

setup(
    name="scheduler",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "ortools>=9.7.0",
    ],
)
