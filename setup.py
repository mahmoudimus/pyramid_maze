import re

import setuptools
from setuptools.command.test import test as TestCommand


version = (
    re
    .compile(r".*__version__ = '(.*?)'", re.S)
    .match(open('pyramid_maze/__init__.py').read())
    .group(1)
)

install_requires = [
    'pyramid >=1.5.1,<1.6.0',
]

extras_require = {
    'tests': [
        'pytest >=2.5.2,<2.6',
        'tox',
        'pytest_pyramid >= 0.1.1',
        'mock >=1.0,<2.0',
        'pytest-cov >=1.7,<2.0',
    ],
}

scripts = []

data_files = []


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        pytest.main(self.test_args)


packages = setuptools.find_packages('.', exclude=('tests', 'tests.*'))
setuptools.setup(
    name='pyramid_maze',
    version=version,
    url='https://github.com/mahmoudimus/pyramid_maze',
    author='mahmoudimus',
    author_email='mabdelkader@gmail.com',
    description='',
    long_description='',
    platforms='any',
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['tests'],
    packages=packages,
    scripts=[],
    data_files=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    cmdclass={'test': PyTest},
)
