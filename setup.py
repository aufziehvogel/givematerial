import re
from setuptools import setup

version = re.search(
    r'^__version__\s*=\s*\'(.+)\'',
    open('givematerial/__init__.py').read(),
    re.M).group(1)

with open('README.md', 'rb') as f:
    long_descr = f.read().decode('utf-8')

install_requires = [
    'classla',
]

setup(
    name='givematerial',
    packages=[
        'givematerial',
    ],
    entry_points={
        'console_scripts': [
            'givematerial=givematerial.cli:main',
            'gm-read=givematerial.cli:manage_read',
        ],
    },
    install_requires=install_requires,
    version=version,
    description='Get text recommendations for foreign languages',
    long_description=long_descr,
    author='Stefan Koch',
)
