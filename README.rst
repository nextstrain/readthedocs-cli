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

.. code-block:: bash

    python3 -m venv .venv
    source .venv/bin/activate

    python3 -m pip install --upgrade pip setuptools wheel
    python3 -m pip install -e .

    rtd --version
