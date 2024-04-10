# 🥪 Jaffle Shop Generator 🏭

> [!NOTE]
> This is not an official dbt Labs project. It is maintained on a volunteer basis by dbt Labs employees who are passionate about analytics engineering, the dbt Community, and jaffles, and feel that generating datasets for learning and practicing is important. Please understand it's a work in progress and not supported in the same way as dbt itself.

The Jaffle Shop Generator or `jafgen` is a simple command line tool for generating synthetic datasets suitable for analytics engineering practice or demonstrations. The data is generated in CSV format and is designed to be used with a relational database. It follows a simple schema, with tables for:

- Customers (who place Orders)
- Orders (from those Customers)
- Products (the food and beverages the Orders contain)
- Order Items (of those Products)
- Supplies (needed for making those Products)
- Stores (where the Orders are placed and fulfilled)

It uses some straightforward math to create seasonality and trends in the data, for instance weekends being less busy than weekdays, customers having certain preferences, and new store locations opening over time. We plan to add more data types and complexity as the codebase evolves.

## Installation

If you have [pipx](https://pypa.github.io/pipx/installation/) installed, `jafgen` is an ideal tool to use via pipx. You can generate data without installing anything in the local workspace using the following:

```shell
pipx run jafgen [options]
```

You can also install `jafgen` into your project or workspace, ideally in a virtual environment.

```shell
pip install jafgen
```

## Use

`jafgen` takes one argument:

- `[int]` Years to generate data for. The default is 1 year.

The following options are available:

- `--pre` sets a prefix for the generated files in the format `[prefix]_[file_name].csv`. It defaults to `raw`.

Generate a simulation spanning 3 years from 2016-2019 with a prefix of `cool`:

```shell
jafgen 3 --pre cool
```

## Purpose

Finding a good data set to practice, learn, or teach analytics engineering with can be difficult. Most open datasets are great for machine learning -- they offer single wide tables that you can manipulate and analyze. Full, real relational databases on the other hand are generally protected by private companies. Not only that, but they're a bit _too_ real. To get to a state that a beginner or intermediate person can understand, there needs to be an advanced amount of analytics engineering transformation applied.

To that end, this project generates relatively simple, clean (but importantly, not _perfect_) data for a variety of entities in discrete tables, which can be transformed and combined into analytical building blocks. There are even trends (like seasonality) and personas (like buying patterns) that can be sussed out through data modeling!

## Approach

The great [@drewbanin](https://github.com/drewbanin) watched the movie [Synecdoche, New York](https://en.wikipedia.org/wiki/Synecdoche,_New_York), and was inspired by the idea of creating a complete simulation of a world. Rather than using discrete rules to generate synthetic data, instead setting up entities with behavior patterns and letting them loose to interact with each other. This was the birth of the Jaffle Shop Generator. There are customers, stores, products, and more, all with their own behaviors and interactions as time passes. These combine to create unique and realistic datasets on every run.

An important caveat is that `jafgen` is _not_ idempotent. By design, it generates new data every time you run it based on the simulation's interactions. This is intended behavior, as it allows for more realistic and interesting data generation. Certain aspects are hard coded, like stores opening at certain times, but the output data is always unique.

We hope over time to add more complex behaviors and trends to the simulation!

## Contribution

We welcome contribution to the project! It's relatively simple to get started, just clone the repo, spin up a virtual environment, and install the dependencies:

```shell
gh repo clone dbt-labs/jaffle-shop-generator
python3 -m venv .venv
# Install the package requirements
pip install -r requirements.txt
# Install the dev tooling (ruff and pytest)
pip install -r dev-requirements.txt
# Install the package in editable mode
pip install -e .
```

Working out from the `jafgen` command, you can see the main entrypoint in `jaffle_shop_generator/cli.py`. This calls the simulation found in `jafgen/simulation.py`. The simulation is where most of the magic happens.
