# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- `jafgen` now takes a `--prefix` argument that appends a prefix with an underscore to the output file names.

## [v0.2.1](https://github.com/dbt-labs/jaffle-shop-generator/releases/tag/v0.2.1) - 2023-01-06

## [v0.2.0](https://github.com/dbt-labs/jaffle-shop-generator/releases/tag/v0.2.0) - 2023-01-06

### Added

- `jafgen` now takes an argument (an integer between 1 and 10) `--years` to control the length of the simulation

### Fixed

- Create directory `jaffle-data` for output if it doesn't already exist

## [v0.1.0](https://github.com/dbt-labs/jaffle-shop-generator/releases/tag/v0.1.0) - 2023-01-06

### Added

- Functioning `jafgen` command generating a fixed amount of synthetic jaffle shop data
