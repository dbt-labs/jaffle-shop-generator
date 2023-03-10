# 🥪 Jaffle Shop Generator 🏭

The Jaffle Shop Generator or `jafgen` is a python package with a simple command line tool for generating a synthetic data set suitable for analytics engineering practice or demonstrations.

## Installation

If you have [pipx](https://pypa.github.io/pipx/installation/) installed, `jafgen` is an ideal tool to use via pipx. You can generate data without installing anything in the local workspace using the following:

```shell
pipx run jafgen [options]
```

You can also install jafgen into your project or workspace, ideally in a virtual environment.

```shell
pip install jafgen
```

## Use

`jafgen` takes one argument, years, which sets the length of time the simulation generates synthetic data for.

```shell
# generate a simulation spanning 3 years from 2016-2019
jafgen --years 3
```

## Purpose

Finding a good data set to practice, learn, or teach analytics engineering with can be difficult. Most open datasets are great for machine learning -- they offer single wide tables that you can manipulate and analyze. Full, real relational databases on the other hand are generally protected by private companies. Not only that, but they're a bit _too_ real. To get to a state that a beginner or intermediate person can understand, there needs to be an advanced amount of analytics engineering transformation applied.

## Approach

Coming soon.

## Contribution

Coming soon.
