# Contributing

## Getting Started

Please read the [README](./README.md) for more information about the project.

## Pre-Commit Hooks

### Installing

This project uses `pre-commit` to run a series of checks before each commit.
If you don't already have `pre-commit` installed, you can install globally with:

```bash
pip install pre-commit
```
Alternatively, you can use homebrew on macOS:

```bash
brew install pre-commit
```

Then, to install the pre-commit hooks, run:

```bash
pre-commit install
```

### Executing

The pre-commit hooks will run automatically before each commit.
However, many of the hooks can be used to automatically fix issues as well.
To run the pre-commit hooks manually and resolve easily fixed issues, run:

```bash
pre-commit run --all-files
```
