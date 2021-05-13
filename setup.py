import setuptools

from pathlib import Path

with Path('README.md').open() as fd:
    long_description = fd.read()

with Path('requirements.txt').open() as fd:
    requirements = fd.read().splitlines()

setuptools.setup(
    name="ics_filter",
    version="0.0.1",
    author="Bastien Germond",
    author_email="bastien.germond@epita.fr",
    description="ics_filter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: GPLv2",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points='''
        [console_scripts]
        ics-filter=ics_filter.ics_filter:main
    ''',
    test_suite="nose.collector",
)
