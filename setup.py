from setuptools import (setup,
                        find_packages)

project_base_url = 'https://github.com/lycantropos/liable.py/'

setup_requires = [
    'pytest-runner>=3.0'
]
install_requires = [
    'click>=6.7',
    'pathspec>=0.5.5',
    'autopep8>=1.3.3',
    'inflect>=0.2.5',
    'nltk>=3.2.5',
    'hypothesis>=3.38.5',
    'pytest>=3.3.0',
]
tests_require = [
    'pydevd>=1.1.1',  # debugging
    'pytest>=3.3.0',
    'pytest-cov>=2.5.1',
    'hypothesis>=3.38.5',
]

setup(name='liable',
      packages=find_packages(exclude=('tests',)),
      version='0.0.1',
      description='Auto-tests generator.',
      long_description=open('README.rst').read(),
      author='Azat Ibrakov',
      author_email='azatibrakov@gmail.com',
      url=project_base_url,
      download_url=project_base_url + 'archive/master.zip',
      setup_requires=setup_requires,
      install_requires=install_requires,
      tests_require=tests_require,
      entry_points={'console_scripts': ['liable = liable.liable:main']})
