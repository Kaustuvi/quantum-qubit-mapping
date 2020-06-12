
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import pathlib
from setuptools import setup, find_namespace_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="quantum-qubit-mapping",
    version="0.1.1",
    description="Qubit Mapping package and tools",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Kaustuvi/quantum-qubit_mapping",
    author="Kaustuvi Basu, Petar Korponaić",
    author_email="basu.kaustuvi@gmail.com, petar.korponaic@gmail.com",
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Science/Research"
        ],

    namespace_packages=['qubit-mapping'],
    packages=find_namespace_packages(),
    include_package_data=True,
    install_requires=[],
    entry_points={},
)