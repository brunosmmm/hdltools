"""Setup."""

from setuptools import setup, find_packages

setup(
    name="hdltools",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "."},
    package_data={"hdltools": ["vecgen/*.tx"]},
    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="HDL Tools",
    install_requires=[
        "git+https://github.com/brunosmmm/scoff.git@master#egg=scoff",
        "git+https://github.com/brunosmmm/dictator.git@master#egg=dictator",
    ],
    scripts=[
        "tools/mmap_docgen",
        "tools/axi_slave_builder",
        "tools/inputgen",
        "tools/vgc",
    ],
)
