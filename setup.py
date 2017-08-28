#!/usr/bin/env python
import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

setup(
    name='cfwatch',
    version='0.1.0',
    description="Automagically purges CloudFlare's cache when local files are updated.",
    long_description=readme,
    author='Quantum',
    author_email='quantum@dmoj.ca',
    url='https://github.com/quantum5/cfwatch',
    keywords='cloudflare cdn cache purge',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    zip_safe=False,

    py_modules=['cfwatch'],
    entry_points={
        'console_scripts': ['cfwatch = cfwatch:main'],
    },
    install_requires=['requests', 'watchdog'],
)
