# -*- coding: utf-8 -*-
""" mockabledoctests -- allows doctests to have global variables mocked"""

from setuptools import setup, find_packages
import os


PKG_NAME = 'mockabledoctests'


def get_install_requirements(req_f):
    with open(os.path.join(os.path.dirname(__file__), req_f)) as reqs:
        return [
            req
            for req in reqs.readlines()
            if req and not req.startswith('#')]


# Grab version string from __init__.py to avoid import that may break
# installation if dependent packages imported by this pkg are not yet installed
def get_version(pkg_name):
    init = os.path.join(os.path.dirname(__file__), pkg_name, '__init__.py')
    version_line = list(filter(lambda l: l.startswith('__version__'), open(init)))[0]
    return eval(version_line.split('=')[-1])


setup(
    name=PKG_NAME.replace('_', '-'),
    version=get_version(PKG_NAME),
    author="Aaron Lehmann",
    author_email="aaron.p.lehmann@gmail.com",
    url="https://github.com/aaron-p-lehmann/mockable_doctests",
    description="Allows mocking in doctests",
    license="MIT",
    packages=find_packages(exclude=[]),
    install_requires=get_install_requirements("requirements.txt")
)
