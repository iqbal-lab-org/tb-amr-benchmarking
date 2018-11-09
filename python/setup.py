import glob
from setuptools import setup, find_packages


setup(
    name='evalrescallers',
    version='0.0.1',
    description='Evaluation of TB AMR callers',
    packages = find_packages(),
    package_data={'evalrescallers': ['data/*']},
    author='Martin Hunt',
    author_email='mhunt@ebi.ac.uk',
    url='https://github.com/iqbal-lab-org/tb-amr-benchmarking',
    scripts=glob.glob('scripts/*'),
    test_suite='nose.collector',
    tests_require=['nose >= 1.3'],
    install_requires=[
        'seaborn'
    ],
    license='GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
    ],
)
