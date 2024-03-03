import setuptools
import PyVuka.pyvuka as pvk

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=pvk.__app_name__,
    version=pvk.__version__,
    author=pvk.__author__,
    author_email=pvk.__email__,
    description=pvk.__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bostonautolytics/pyvuka",
    packages=setuptools.find_packages(),
    install_requires=["asteval>=0.9.31", "chardet>=5.2.0", "lmfit>=1.2.2", "matplotlib>=3.8.3", "numpy>=1.26.4",
                      "Pillow>=10.2.0", "psutil>=5.9.8", "scipy>=1.12.0",
                      "xlrd>=2.0.1", "XlsxWriter>=3.1.9"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Free For Educational Use",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
)