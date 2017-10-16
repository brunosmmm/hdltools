"""Setup."""

from setuptools import setup, find_packages

setup(
    name="hdltools",
    version="0.1",
    packages=find_packages(),
    package_dir={'': '.'},

    install_requires=[],

    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="HDL Tools",

    scripts=['tools/mmap_docgen', 'tools/axi_slave_builder'],
    )
