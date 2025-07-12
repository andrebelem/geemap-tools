# setup.py
# Este arquivo é mantido apenas para compatibilidade com ambientes legados
# que não suportam completamente o formato PEP 621 (pyproject.toml).
# A instalação preferencial deve usar: `pip install .` com base no pyproject.toml

from setuptools import setup, find_packages

setup(
    name="geemap-tools",
    version="0.1.0",
    description="Ferramentas auxiliares para Google Earth Engine e geemap",
    author="André Belem",
    author_email="andrebelem@id.uff.br",
    url="",
    packages=find_packages(
        where=".",
        exclude=["geemap_tools/private_dev"]
    ),
    package_data={"geemap_tools": ["*.py"]},
    python_requires=">=3.9",
    install_requires=[
        "earthengine-api>=0.1",
        "eemont>=0.3.5",
        "pyproj>=3.0",
        "pandas>=1.2",
        "tqdm>=4.60",
        "xarray>=2023.1",
        "rioxarray>=0.13",
        "matplotlib>=3.3",
        "geemap>=0.20",
        "openpyxl"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=["gee", "geemap", "remote sensing", "earth engine", "terra climate", "chirps", "ibge", "sidra"],
    license="MIT"
)

