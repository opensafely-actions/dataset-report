# Notes for developers

## System requirements

### `just`

[`just`][1] is a handy way to save and run project-specific commands.
It's unrelated to the package with the same name on PyPI.

```sh
# macOS
brew install just

# Linux
# Install from https://github.com/casey/just/releases

# Show all available commands
just # Shortcut for just --list
```

## Development

Set up a local development environment with

```sh
just devenv
```

and create a new branch.
Then, iteratively:

* Make changes to the code
* Run the tests with

  ```sh
  just test
  ```

* Check the code for issues with

  ```sh
  just check
  ```

* Fix any issues with

  ```sh
  just fix
  ```

* Commit the changes

Finally, push the branch to GitHub and open a pull request against the `main` branch.

### Environments

A reusable action is run within a container,
which is created from a image,
which in turn is created from a repository.
As this is a Python reusable action, it is run within a Python container,
which is created from a Python image,
which in turn is created from the [opensafely-core/python-docker][] repository.

The Python container provides the reusable action with its production environment.
From a developer's perspective, the most important characteristic of the production environment is that it contains __Python 3.8__.
The next most important characteristic is that it contains the versions of the packages listed in [_requirements.txt_][3] from the opensafely-core/python-docker repository.

Notice, however, that there are two sets of requirements files within this reusable action's repository:

* The versions of the packages listed in _requirements.prod.in_ are for local development
  and should mirror the production environment.
  In other words,
  the versions of the packages listed in _requirements.prod.in_
  should mirror the versions of the packages listed in _requirements.txt_ from the opensafely-core/python-docker repository.

* The versions of the packages listed in _requirements.dev.in_ are for local development
  and need not mirror the production environment.

## Tagging a new version

This reusable action follows [Semantic Versioning, v2.0.0]().

A new __patch__ version is automatically tagged when a group of commits is pushed to the `main` branch;
for example, when a group that comprises a pull request is merged.
Alternatively, a new patch version is tagged for each commit in the group that has a message title prefixed with `fix`.
For example, a commit with the following message title would tag a new patch version when it is pushed to the `main` branch:

```
fix: a bug fix
```

A new __minor__ version is tagged for each commit in the group that has a message title prefixed with `feat`.
For example, a commit with the following message title would tag a new minor version when it is pushed to the `main` branch:

```
feat: a new feature
```

A new __major__ version is tagged for each commit in the group that has `BREAKING CHANGE` in its message body.
For example, a commit with the following message body would tag a new major version:

```
Remove a function

BREAKING CHANGE: Removing a function is not backwards-compatible.
```

Whilst there are other prefixes besides `fix` and `feat`, they do not tag new versions.

[1]: https://github.com/casey/just/
[2]: https://semver.org/spec/v2.0.0.html
[3]: https://github.com/opensafely-core/python-docker/blob/main/requirements.txt
[opensafely-core/python-docker]: https://github.com/opensafely-core/python-docker
