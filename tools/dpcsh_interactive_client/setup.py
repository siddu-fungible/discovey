#!/usr/bin/python

from setuptools import setup


setup(
    name="dpcsh_interactive_client",
    version="1.0",
    description="Interactive Client over DPC",
    scripts=["dpc_cli"],
    packages=["dpcsh_interactive_client"],
    package_dir={'': 'src'},
    zip_safe=False,
    keywords='dpcsh_interactive_client',
    install_requires=[
        "ipaddress",
        "netaddr",
        "prettytable",
        "cmd2 == 0.8.5",
    ],
)
