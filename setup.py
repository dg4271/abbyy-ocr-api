import io
from setuptools import find_packages, setup


# Read in the README for the long description on PyPI
def long_description():
    with io.open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()
    return readme

setup(name='table-extraction',
      version='0.1',
      description='for cj poc',
      long_description=long_description(),
      author='dghong',
      author_email='dghong@saltlux.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
