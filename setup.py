from setuptools import find_packages, setup

setup(
    name="jaffle-shop-generator",
    version="0.4.1",
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"],
    ),
    package_dir={"jafgen": "jafgen"},
    entry_points={"console_scripts": ["jafgen = jafgen.cli:app"]},
    install_requires=["numpy", "pandas", "Faker", "typer[all]"],
)
