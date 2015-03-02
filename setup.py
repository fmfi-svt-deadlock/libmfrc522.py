#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='libmfrc522',
      description='A library for communicating with the MFRC522 RFID module',
      version='0.1',
      url='https://github.com/fmfi-svt-gate/libmfrc522.py',
      license='MIT',
      packages=find_packages(),
      install_requires=['crcmod'])
