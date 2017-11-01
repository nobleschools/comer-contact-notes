"""Minimal setup file for comer-contact-notes project."""

from setuptools import setup, find_packages

setup(
    name="comer_contact_notes",
    version="0.1.0",
    license="proprietary",
    description=(
        "Lambda-ready package to upload Comer and Noble Salesforce "
        "Contact Note objects"
    ),

    author="Noble Network of Charter Schools",
    url="https://github.com/noblenetworkcharterschools/comer-contact-notes",

    packages=find_packages(where="src"),
    package_dir={"": "src"},

    install_requires=[],
)
