from setuptools import setup, find_packages

setup(
    packages=["chialisp_stdlib"],
    package_data={"": ["stable/*.clib", "nightly/*.clib"]},
)
