#!/usr/bin/env python
"""
Package installer for lambada - an AWS lambda framework
"""
from __future__ import absolute_import
import io
from setuptools import setup, find_packages


with io.open('README.rst', encoding='UTF-8') as readme:
    README = readme.read()

setup(
    name='lambada',
    version='0.2.1',
    packages=find_packages(),
    package_data={},
    license='License :: OSI Approved :: Apache Software License',
    author='Superpedestrian, Inc',
    author_email='dev@superpedetrian.com',
    url='https://github.com/Superpedestrian/lambada',
    description=(
        'A framework for multiple AWS lambdas in one library/package'
    ),
    long_description=README,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
    ],
    entry_points={'console_scripts': [
        'lambada=lambada.cli:cli'
    ]},
    install_requires=[
        'lambda-uploader',
        'click',
        'PyYAML',
        'six',
    ],
    zip_safe=True,
)
