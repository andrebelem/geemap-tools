from setuptools import setup, find_packages

setup(
    name='geemap-tools',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'earthengine-api>=0.1',
        'eemont>=0.3.5',
        'pyproj>=3.0',
        'pandas>=1.2',
        'tqdm>=4.60',
        'xarray>=2023.1',
        'rioxarray>=0.13',
        'matplotlib>=3.3',
        'geemap>=0.20',
    ],
    description='Ferramentas adicionais para geemap.',
    author='Andre Belem',
    author_email='andrebelem@id.uff.br',
    url='https://github.com/andrebelem/geemap-tools-dev',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
