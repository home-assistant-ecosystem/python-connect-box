#!/usr/bin/env python3
"""Setup file for Compal CH7465LG Python client."""
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.rst"), encoding="utf-8") as readme:
    long_description = readme.read()


setup(
    name="connect_box",
    version="0.2.7",
    description="Python client for interacting with Compal CH7465LG devices.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/fabaff/python-connect-box",
    download_url="https://github.com/fabaff/python-connect-box/releases",
    author="Fabian Affolter",
    author_email="fabian@affolter-engineering.ch",
    license="MIT",
    install_requires=["aiohttp", "defusedxml", "attrs"],
    packages=["connect_box"],
    zip_safe=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities",
    ],
)
