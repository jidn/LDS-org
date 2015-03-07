#!/usr/bin/env python
import os
from setuptools import setup, find_packages

__version__ = open(os.path.join(os.path.dirname(__file__), 'VERSION')).read().strip()

requirements = [
    'requests',
    'certifi'
]

setup(
    name='LDS-org',
    author='Clinton James',
    author_email='clinton.james@anuit.com',
    url='https://www.github.com/jidn/lds-org/',
    download_url='https://github.com/jidn/lds-org/tarball/' + __version__,
    description='Access LDS.org json information',
    long_description=open('README.md').read(),
    version=__version__,
    keywords=['lds'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
    ],
    py_modules=['lds_org'],
    # packages=find_packages(exclude=['tests']),
    zip_safe=False,
    include_package_data=True,
    install_requires=requirements,
    # Install these with "pip install -e '.[paging]'" or '.[docs]'
    # extras_require={
    #     'docs': 'sphinx',
    # }
)
