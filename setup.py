import setuptools
import sys
from Cython.Build import cythonize
from setuptools.extension import Extension
import numpy as np

defs = [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")]
ext = [Extension('mglg.ext.sdf', 
                sources=["mglg/ext/sdf/_sdf.pyx", "mglg/ext/sdf/sdf.c"]),
       Extension('mglg.graphics.particle',
                 sources=['mglg/graphics/particle.pyx'],
                 include_dirs=[np.get_include()],
                 define_macros=defs)]

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
