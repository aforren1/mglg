import setuptools
import sys
from Cython.Build import cythonize
from setuptools.extension import Extension

ext = Extension('mglg.ext.sdf', 
                sources=["mglg/ext/sdf/_sdf.pyx", "mglg/ext/sdf/sdf.c"])

with open("README.md", "r") as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="mglg",
    version="0.1.0",
    install_requires=requirements,
    author="Alex Forrence",
    author_email="alex.forrence@gmail.com",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aforren1/mglg",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    ext_modules=cythonize(ext, compiler_directives={'language_level': 3}, annotate=True)
)
