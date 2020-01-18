"""Setup."""

from setuptools import setup, find_packages

setup(
    name="hdltools",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "."},
    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="HDL Tools",
    install_requires=[
        "scoff @ git+https://github.com/brunosmmm/scoff@master#egg=scoff",
        "dictator @ git+https://github.com/brunosmmm/dictator@master#egg=dictator",
    ],
    scripts=["tools/mmap_docgen", "tools/axi_slave_builder", "tools/inputgen"],
)
