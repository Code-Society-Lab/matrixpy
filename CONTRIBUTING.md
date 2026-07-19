# Contributing to matrix.py
Thank you for your interest in contributing to the matrix.py! As an open source project, many kinds of contributions are welcome.

## How can you contribute?
You can contribute to this project in the following ways

- Report Bugs
- Add new features
- Fix a bug
- Improve the documentation

**Warning:** Non-trivial pull requests must have an [issue](https://github.com/Code-Society-Lab/matrixpy/issues) proposing the changes.

## Setup
1. Clone the matrix.py repository
2. Create and activate a virtual environment
3. Install the development dependencies and enable the Git hooks.

```bash
pip install -e ".[dev]"
pre-commit install
```


After installation, the Git hooks run automatically before each commit to check formatting, typing, and tests.
The hooks include running:
- black
- mypy
- pytest

Run the full hook suite manually with:

```bash
pre-commit run --all-files
```

## Guidelines
Read any issue instructions carefully. Feel free to ask for clarification if any details are missing.

Add docstrings to all of your code (functions, methods, classes, ...). The codebase should have enough examples for you to copy from.

Write tests for your code.
- If you are fixing a bug, add a regression test that references the original issue.
- If you are implementing a new feature, add tests covering the new functionality.

## Before opening a PR

Before you open your PR, please go through this checklist and make sure you've checked all the items that apply:

- [ ] Format your code, ensure that your code is clean and follows Python's [PEP-0008](https://www.python.org/dev/peps/pep-0008/)
- [ ] All your code has docstrings in the style of the rest of the codebase
- [ ] All your code is typed ([type hinting](https://docs.python.org/3/library/typing.html))
- [ ] Your code passes all tests (run [`pytest`](https://docs.pytest.org/en/stable/))
- [ ] Verify your code for grammar and spelling mistakes (The code, documentation and other text must be in English)


## After opening a PR
When you open a PR, your code will be reviewed by one of the maintainers. In that review process,

- We will take a look at all of the changes you are making
- We might ask for clarifications (why did you do X or Y?)
- We might ask for more tests/more documentation
- We might ask for some code changes

The primary goal of these interactions is to ensure that, over time, everyone enjoys the best possible experience with matrix.py and the feature you're implementing or fixing.

Don't be discouraged if a reviewer requests code changes, this is a normal part of the process. Even within the team, maintainers frequently request revisions from each other

# Join the community
Need help, have some questions or want to participate more directly in the evolution of the framework? Join our community on [Discord](https://discord.gg/6GEF9H9m)!
