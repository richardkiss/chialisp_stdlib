from setuptools import setup, find_packages

PACKAGES = ["chialisp_stdlib", "chialisp_stdlib.nightly", "chialisp_stdlib.stable"]

setup(
    packages=PACKAGES,
    package_data={"": ["stable/*.clib", "nightly/*.clib"]},
)
