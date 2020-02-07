import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PyVuka", # Replace with your own username
    version="0.1",
    author="R Paul Nobrega",
    author_email="Paul@PaulNobrega.net",
    description="General Purpose Global Data Analysis Package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bostonautolytics/pyvuka",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)