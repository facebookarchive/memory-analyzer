#!/usr/bin/env python3
#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

with open("requirements.txt") as f:
    requires = f.read().strip().splitlines()

setup(
    name="memory_analyzer",
    description="Python 3 memory analyzer for running processes",
    long_description=readme,
    long_description_content_type="text/markdown",
    version="0.1.2",
    author="Lisa Roach, Facebook",
    author_email="lisroach@fb.com",
    url="https://github.com/facebookincubator/memory-analyzer",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    license="MIT",
    packages=find_packages(),
    package_data={"memory_analyzer": ["templates/*.template"]},
    test_suite="memory_analyzer.tests",
    python_requires=">=3.6",
    setup_requires=["setuptools"],
    install_requires=requires,
    entry_points={
        "console_scripts": ["memory_analyzer = memory_analyzer.memory_analyzer:cli"]
    },
)
