from setuptools import setup

PACKAGES = ["chialisp_stdlib", "chialisp_stdlib.nightly", "chialisp_stdlib.stable"]

setup(
    packages=PACKAGES,
    package_data={"": ["stable/*.clib", "nightly/*.clib"]},
)
