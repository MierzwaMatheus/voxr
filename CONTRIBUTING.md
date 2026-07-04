# Contributing to Voxr

## Setup

```bash
git clone https://github.com/MierzwaMatheus/voxr.git
cd voxr
pip install -e ".[dev]"
```

## Development workflow

All features must follow **TDD (Red → Green → Refactor)**:

1. Write a failing test first
2. Implement the minimum code to make it pass
3. Refactor without breaking tests

## Running checks

```bash
pytest tests/unit/ -v                   # unit tests
pytest --cov=voxr --cov-fail-under=80  # coverage ≥ 80%
ruff check voxr/ tests/                # lint
```

## Commit style

Follow [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): description`.

## Branch naming

`feature/<issue-number>-<short-description>`

## PR checklist

Before opening a pull request, verify all items below pass locally:

- [ ] `pytest tests/unit/ -v` — zero failures
- [ ] `pytest --cov=voxr --cov-fail-under=80` — coverage ≥ 80%
- [ ] `ruff check voxr/ tests/` — zero lint errors
- [ ] New behavior is covered by at least one unit test
- [ ] No commented-out code or debug prints left behind
- [ ] Commit messages follow Conventional Commits
