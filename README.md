# AI Alerting

# Requirements

### Requirements

Install system wide:

-   [Pyenv](https://github.com/pyenv/pyenv)
-   [Poetry](https://python-poetry.org/docs/#installation)

# Initiate the environment for the project

Execute in project root:

```bash
pyenv install 3.11.7

pyenv local 3.11.7
poetry shell
poetry env use (pyenv which python) # only the first time
poetry install

```

This will setup a local env

# How to start server

Execute in project root:

```bash
docker compose up #first time --build
```
