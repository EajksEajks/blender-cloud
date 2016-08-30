#!/usr/bin/env python

"""Setup file for testing, not for packaging/distribution."""

import setuptools

setuptools.setup(
    name='blender-cloud',
    version='1.0',
    packages=setuptools.find_packages('.', exclude=['tests']),
    tests_require=[
        'pytest>=2.9.1',
        'responses>=0.5.1',
        'pytest-cov>=2.2.1',
        'mock>=2.0.0',
    ],
    zip_safe=False,
)
