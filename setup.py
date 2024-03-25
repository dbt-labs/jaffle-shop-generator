from setuptools import find_packages, setup


def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


requirements = parse_requirements("requirements.in")
setup(
    name="jaffle-shop-generator",
    version="0.2",
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"],
    ),
    package_dir={"jafgen": "jafgen"},
    entry_points={"console_scripts": ["jafgen = jafgen.main:main"]},
    install_requires=requirements,
)
