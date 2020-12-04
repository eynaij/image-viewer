# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import io
import re

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with io.open("image_viewer/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

setup(
    name='image-viewer',
    version='1.0.1',
    description='image viewer tool',
    long_description=readme,
    author='weizhen.wu',
    url='http://gitlab.hobot.cc/weizhen.wu/image_viewer',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'scripts')),
    include_package_data=True,
    entry_points={"console_scripts": ["image-viewer = image_viewer.main:main"]},
    scripts=['scripts/image-viewer-cfg'],
)
