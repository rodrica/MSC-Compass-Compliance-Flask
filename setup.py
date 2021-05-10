#!/usr/bin/env python

"""
  TODO: Add Copyright and license info
"""
import datetime
import os

from setuptools import find_packages, setup


def get_version():
    """
    Get a PEP440 compliant version number
    https://www.python.org/dev/peps/pep-0440/
    """
    # If building a tag, tag is the version. Tag builds are release builds.
    if "CI_COMMIT_TAG" in os.environ:
        return os.environ["CI_COMMIT_TAG"]

    # Prefix with lowercase branch name
    version = "1.0.0.dev0"  # public version identifier
    version_fmt = "{}+{}"  # after '+' comes local version identifier
    if "CI_COMMIT_REF_SLUG" in os.environ:
        version = version_fmt.format(version, os.environ["CI_COMMIT_REF_SLUG"])
        version_fmt = "{}.{}"

    # Add either commit sha, or datetime
    if "CI_COMMIT_SHA" in os.environ:
        return version_fmt.format(version, os.environ["CI_COMMIT_SHA"])
    else:
        return version_fmt.format(version, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))


setup(
    name='tl-msc-user-management-service',
    version=get_version(),
    description='TechLock User Management service',
    author='Michiel Vanderlee',
    author_email='jmt.vanderlee@gmail.com',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'tl_msc_common==1.0.0.dev0+master.8caa856559975b2950a672bf270985e35e447e64',
        'Flask-HTTPAuth==3.3.0',
    ],
)
