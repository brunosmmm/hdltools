"""Setup."""

from setuptools import setup, find_packages

setup(
    name="hdltools",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "."},
    install_requires=[],
    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="HDL Tools",
    dependency_links=[
        "http://github.com/brunosmmm/scoff/tarball/master#egg=scoff-0.1",
        "http://github.com/brunosmmm/dictator/tarball/master#egg=dictator-0.1",
    ],
    scripts=["tools/mmap_docgen", "tools/axi_slave_builder", "tools/inputgen"],
)
