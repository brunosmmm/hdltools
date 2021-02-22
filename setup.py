"""Setup."""

from setuptools import setup, find_packages

setup(
    name="hdltools",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "."},
    package_data={
        "hdltools": [
            "vecgen/*.tx",
            "binutils/*.tx",
            "vcd/trigger/*.tx",
            "mmap/*.tx",
        ]
    },
    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="HDL Tools",
    install_requires=[
        "colorama",
        "textX",
        "astunparse",
        "scoff @ git+https://github.com/brunosmmm/scoff@77abf0306443d98155e5dfc9e7626297cbc2c38b#egg=scoff",
        "dictator @ git+https://github.com/brunosmmm/dictator@80e135607682140b4a2787cc226a09753ffa1a1c#egg=dictator",
    ],
    scripts=[
        "tools/mmap_docgen",
        "tools/axi_slave_builder",
        "tools/inputgen",
        "tools/vgc",
        "tools/vcdhier",
        "tools/vcdtracker",
        "tools/vcdevts",
    ],
)
