from setuptools import setup, find_packages

setup(
    name='geemap-tools',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'earthengine-api',  # Para ee
        'eemont',
        'geopandas',
        'pandas',
        'tqdm',
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
