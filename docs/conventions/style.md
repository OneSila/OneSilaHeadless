# Code Style

## Always kwargs, no args

To ensure we are using ‘adjustable’ code throughout and avoid surprises when refactoring is to force ourselves to always use kwargs.  No args.

How to accomplish this?

Put a * in front of your args.  Ex:

```python
def test(*, name, target):
    print(name, target)
```

Running this, will yield:

```python
In [1]: def test(*, name, target):
   ...:     print(name, target)
   ...:

In [2]: test(1,2)
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Cell In[2], line 1
----> 1 test(1,2)

TypeError: test() takes 0 positional arguments but 2 were given

In [3]: test(name=1, target=2)
1 2
```

## File sizes

Let’s try to keep files below 500 lines of code.  If it’s getting near this limit, separate into the usual folder structure.

# Pre-commit / PEP8

Let’s use this configuration to when setting up our repo’s locally:

`.pre-commit-config.yaml`

```python
# .pre-commit-config.yamlrepos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.1  # Use the ref you want to point at
    hooks:
    -   id: check-yaml
    -   id: end-of-file-fixer
    -   id: trailing-whitespace
-   repo: https://github.com/pre-commit/mirrors-autopep8
    rev: 'v1.5.7'  # Use the sha / tag you want to point at
    hooks:
    -   id: autopep8
```

`setup.cfg`

```python
# setup.cfg
[pycodestyle]
count = False
ignore = E128
max-line-length = 160
exclude = migrations, venv
```
