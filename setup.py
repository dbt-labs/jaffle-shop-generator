from setuptools import find_packages, setup

setup(
    name="jafgen",
    version="0.4.1",
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"],
    ),
    authors=["gwenwindflower", "drewbanin"],
    description="A synthetic data generator CLI for a fictional Jaffle Shop",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    package_dir={"jafgen": "jafgen"},
    entry_points={"console_scripts": ["jafgen = jafgen.cli:app"]},
    install_requires=["numpy", "pandas", "Faker", "typer[all]"],
)
