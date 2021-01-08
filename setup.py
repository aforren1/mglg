import setuptools
import sys
from Cython.Build import cythonize
from setuptools.extension import Extension
import numpy as np
from sys import platform

extra_compile_args = []
# strip debug symbols for linux wheels
if sys.platform == 'linux':
    extra_compile_args.append('-g0')

eca = extra_compile_args
defs = [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")]
inc_path = np.get_include()

ext = [Extension('mglg.ext.sdf',
                 sources=["mglg/ext/sdf/_sdf.pyx", "mglg/ext/sdf/sdf.c"],
                 extra_compile_args=eca),
       Extension('mglg.graphics._particle',
                 sources=['mglg/graphics/particle.pyx'],
                 include_dirs=[inc_path],
                 define_macros=defs,
                 extra_compile_args=eca),
       Extension('mglg.graphics.easing',
                 sources=['mglg/graphics/easing.pyx'],
                 extra_compile_args=eca),
       Extension('mglg.ext.earcut',
                 sources=['mglg/ext/_earcut/earcut.py'],
                 extra_compile_args=eca)]

with open("README.md", "r") as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="mglg",
    version="0.2.23",
    install_requires=requirements,
    extras_require={'freetype': ['freetype-py']},
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
    ext_modules=cythonize(ext,
                          compiler_directives={'language_level': 3},
                          annotate=True)
)
