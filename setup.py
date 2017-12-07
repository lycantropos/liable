from setuptools import setup

import liable

project_base_url = 'https://github.com/lycantropos/liable/'

setup_requires = [
    'pytest-runner>=3.0'
]
tests_require = [
    'pydevd>=1.1.1',  # debugging
    'pytest>=3.3.0',
    'pytest-cov>=2.5.1',
    'hypothesis>=3.38.5',
]

setup(name='liable',
      scripts=['liable.py'],
      version=liable.__version__,
      description=liable.__doc__,
      long_description=open('README.rst').read(),
      author='Azat Ibrakov',
      author_email='azatibrakov@gmail.com',
      url=project_base_url,
      download_url=project_base_url + 'archive/master.zip',
      setup_requires=setup_requires,
      tests_require=tests_require)
