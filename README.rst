=================
Read The Docs CLI
=================

*A work in progress.*

Made to sync RTD project redirects from an authoritative YAML file kept in
version control.  May never do anything else!


Synopsis
========

Provide an RTD API token via the environment:

.. code-block:: console

    $ export RTD_TOKEN=…

List projects:

.. code-block:: console

    $ rtd projects
    nextstrain
    ├── nextstrain-ncov
    ├── nextstrain-nextclade
    ├── nextstrain-augur
    ├── nextstrain-auspice
    ├── nextstrain-cli
    └── nextstrain-sphinx-theme

Show a project (very sparse currently):

.. code-block:: console

    $ rtd projects nextstrain
    nextstrain <https://docs.nextstrain.org/en/latest/>

Show a project's redirects:

.. code-block:: console

    $ rtd projects nextstrain redirects
                                                                                 Redirects

      Type   From URL                                                     To URL
     ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
      page   /guides/                                                     /
      page   /guides/index.html                                           /index.html
      page   /guides/install/                                             install-nextstrain.html
      page   /guides/install/augur_install.html                           https://docs.nextstrain.org/projects/augur/en/stable/installation/installation.html
      page   /guides/install/auspice-install                              https://docs.nextstrain.org/projects/auspice/en/stable/introduction/install.html
      page   /guides/install/auspice-install.html                         https://docs.nextstrain.org/projects/auspice/en/stable/introduction/install.html
      page   /guides/install/cli-install.html                             https://docs.nextstrain.org/projects/cli/en/latest/installation/
      page   /guides/install/index.html                                   install-nextstrain.html
      page   /guides/install/local-installation.html                      install-nextstrain.html
      page   /guides/install/windows-help.html                            install-nextstrain.html
      page   /install-nextstrain.html                                     /install.html
      page   /learn/                                                      /
      page   /learn/about-nextstrain.html                                 /learn/about.html
      page   /learn/index.html                                            /index.html
      page   /reference/                                                  /
      page   /reference/formats/                                          /reference/data-formats.html
      page   /reference/formats/data-formats.html                         /reference/data-formats.html
      page   /reference/formats/index.html                                /reference/data-formats.html
      page   /reference/index.html                                        /index.html
      …

Sync a project's redirects:

.. code-block:: console

    $ rtd projects nextstrain redirects sync -f redirects.yml
    Creating: page /tutorials/quickstart.html → /tutorials/running-a-workflow.html
    Creating: page /tutorials/tb_tutorial.html → /tutorials/creating-a-workflow-vcf.html
    Creating: page /tutorials/zika.html → /tutorials/creating-a-workflow.html

              Created

      Type   From URL                      To URL
     ──────────────────────────────────────────────────────────────────────────────
      page   /tutorials/quickstart.html    /tutorials/running-a-workflow.html
      page   /tutorials/tb_tutorial.html   /tutorials/creating-a-workflow-vcf.html
      page   /tutorials/zika.html          /tutorials/creating-a-workflow.html

                                        Deleted

      Type   From URL   To URL
     ──────────────────────────

    Created 3, deleted 0, kept 38.

    No changes made in --dry-run mode.  Pass --wet-run for realsies.

For automation or just the full details, ask for JSON output instead of
human-centered output from any command:

.. code-block:: console

    $ rtd --json projects
    [
      {
        "id": 607779,
        "name": "nextstrain",
        "created": "2020-05-28T00:25:49.630013Z",
        "modified": "2021-08-18T23:39:10.271300Z",
        "default_branch": "master",
        "default_version": "latest",
        "homepage": "https://nextstrain.org",
        "language": {
          "code": "en",
          "name": "English"
        },
        "programming_language": {
          "code": "words",
          "name": "Only Words"
        },
        "repository": {
          "type": "git",
          "url": "https://github.com/nextstrain/docs.nextstrain.org.git"
        },
        …
      },
      …
    ]


Install
=======

From `PyPI <https://pypi.org/project/readthedocs-cli/>`_:

.. code-block:: bash

    python3 -m pip install readthedocs-cli

From `source <https://github.com/nextstrain/readthedocs-cli>`_:

.. code-block:: bash

    python3 -m venv .venv
    source .venv/bin/activate

    python3 -m pip install --upgrade pip setuptools wheel
    python3 -m pip install -e .

    rtd --version


Automatic sync using GitHub Actions
===================================

We manage the RTD redirects for <https://docs.nextstrain.org> using a file in
our Git repository, <https://github.com/nextstrain/docs.nextstrain.org>.  The
redirects are automatically synced to RTD via a GitHub Actions workflow that
uses this CLI tool.  It's a good example of how to set up something similar for
your own project.  The pieces are:

1. `redirects.yml`_ file — The redirects themselves, defined as YAML.

2. `.github/workflows/sync-redirects.yaml`_ file — GitHub Actions workflow to
   sync to RTD when *redirects.yml* changes on the ``master`` branch.

3. An ``RTD_TOKEN`` `GitHub Actions secret`_ containing an `RTD API token`_.

.. _redirects.yml: https://github.com/nextstrain/docs.nextstrain.org/blob/master/redirects.yml
.. _.github/workflows/sync-redirects.yaml: https://github.com/nextstrain/docs.nextstrain.org/blob/master/.github/workflows/sync-redirects.yaml
.. _GitHub Actions secret: https://docs.github.com/en/actions/security-guides/encrypted-secrets
.. _RTD API token: https://readthedocs.org/accounts/tokens/


Releasing
=========

This is still a pretty informal piece of software, but it is released to
`PyPI`_ so that we can easily install it various places.

The gist of the release process is:

1. Bump the ``__version__`` variable (just an integer) in
   *src/readthedocs_cli/__init__.py*.

2. Commit, tag, and push.

3. Build and upload.

   You'll need `build <https://pypi.org/project/build/>`_ and `twine
   <https://pypi.org/project/twine/>`_ installed.

   .. code-block:: bash

       # Clear any existing build artifacts for safety
       rm -rf dist/

       # Build source tarball and platform-agnostic wheel
       python3 -m build

       # Upload both to PyPI
       twine upload dist/*
