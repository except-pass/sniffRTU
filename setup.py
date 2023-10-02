import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    install_requires = fh.readlines()

with open("__version__", "r") as fh:
    version = fh.read()
    version = version.strip()

setuptools.setup(
    name="sniffRTU",
    version=version,
    author="Will Gathright",
    author_email="williamg@fortresspower.com",
    description="Read and analyze modbus traffic",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)