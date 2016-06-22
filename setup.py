#! /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from setuptools import setup, find_packages, Command

from stratus import __version__

class WriteVersion(Command):
    description = "Write version from git"
    user_options = [('version=', 'v',
         "Write version into package if no version specify use git")]

    def initialize_options(self):
        self.version = None

    def finalize_options(self):
        if self.version is None:
            commit_b = subprocess.check_output(
                'git rev-parse --verify --short HEAD', shell=True)
            commit = commit_b.decode('utf-8').strip()
            current_version = __version__.split('-')[0]
            self.version = '{}-{}'.format(current_version, commit)

    def run(self):
        with open('stratus/__init__.py' , 'w') as version_file:
            version_file.write('__version__ = \'{}\''.format(self.version))

setup(
    name='stratus',
    version=__version__,
    description='An hypervisor manager without agent',
    license='GPLv3',
    url='https://github.com/Zempashi/stratus',
    packages=find_packages(),
    package_data={'stratus.managers.aknansible': ['playbooks/*.yml']},
    install_requires=['django',
                      'channels'],
    cmdclass={
	'writeversion': WriteVersion
    },
)
