# Contributing to mozci-tools

Thank you for contributing!

### Getting Set Up

`mozci-tools` uses a tool called [poetry](https://python-poetry.org/) to manage packages, dependencies and more. So please [install poetry](https://python-poetry.org/docs/#installation) before proceeding.

Then you can run:
```bash
$ cd path/to/mozci-tools

# This will create a virtualenv and install this project along with all of its dependencies into it.
$ poetry install

# This command will show you which virtualenv you have activated. See `poetry env --help` for more env management abilities.
$ poetry env list
```

Alternatively you can disable virtualenv creation and use whichever Python environment is currently active in your shell:
```bash
$ poetry env use system
```

The install command should have added a binary called `citools` which is the entry point to the scripts in this project.
```bash
# Binaries in poetry's envs are accessible via the `poetry run` command.
$ poetry run citools --help

# Alternatively you can use `poetry shell` to activate the env.
$ poetry shell
$ citools --help
```

### Setting up Linters and Hooks

`mozci-tools` uses [pre-commit](https://pre-commit.com/) to handle linters, formatters and hooks. Simply run:
```bash
$ poetry run pre-commit install
```

and now anytime you do a `git commit`, linters / formatters will run automatically. These checks also run in CI.


### Running Tests

Tests are run via the [pytest](https://docs.pytest.org/) framework. To run tests:
```bash
$ poetry run pytest
```

You can also simulate the CI jobs by running [tox](https://tox.readthedocs.io/en/latest/):
```bash
$ poetry run tox
```
