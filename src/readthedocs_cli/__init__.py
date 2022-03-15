#!/usr/bin/env python3
import click
import json
import rich.box
import yaml
from itertools import filterfalse, tee
from rich.console import Console as RichConsole
from rich.table import Table as RichTable
from rich.tree import Tree as RichTree
from typing import NamedTuple
from urllib.parse import quote as urlescape, urljoin

from . import api


__version__ = 2


console = RichConsole(markup = False)


class Context:
    json: bool
    project_name: str
    project_slug: str
    redirects: list


# rtd
@click.group("rtd")
@click.pass_context
@click.option("-j", "--json", help = "Output JSON instead of formatted text", is_flag = True)
@click.version_option(__version__)
def rtd(ctx, json):
    ctx.ensure_object(Context)
    ctx.obj.json = json


# rtd projects
@rtd.group("projects", invoke_without_command = True)
@click.pass_context
@click.argument("name", metavar = "<name>", required = False)
def rtd_projects(ctx, name):
    # Unfortunately we always need to get the projects so we can resolve a
    # project name to a project slug.
    #
    # There's a slight optimization here where we could stop pagination early
    # once we find the project (e.g. avoid fetching the second page if the
    # project we're looking for is in the first page), but that would only
    # impact folks with over 100 projects, which seems exceedingly rare.
    #   -trs, 15 March 2022
    projects = api.v3.projects()

    # List or show
    if ctx.invoked_subcommand is None:
        with console.pager(styles = True):
            # rtd projects <name> (show a single project)
            if name is not None:
                project = next((p for p in projects if p["name"] == name), None)

                if not project:
                    raise click.UsageError(f"Could not find project {name!r}", ctx = ctx)

                if ctx.obj.json:
                    console.print_json(as_json(project))
                else:
                    console.print(f"{project['name']} <{project['urls']['documentation']}>")

            # rtd projects (list projects)
            else:
                if ctx.obj.json:
                    console.print_json(as_json(projects))
                else:
                    roots, leaves = partition(lambda p: not p["subproject_of"], projects)

                    for r in roots:
                        tree = RichTree(r["name"])

                        for l in leaves:
                            if l["subproject_of"]["id"] == r["id"]:
                                tree.add(l["name"])

                        console.print(tree)

    # Subcommand context
    else:
        ctx.obj.project_name = name
        ctx.obj.project_slug = next((p["slug"] for p in projects if p["name"] == name), None)


# rtd projects <name> redirects
@rtd_projects.group("redirects", invoke_without_command = True)
@click.pass_context
def rtd_projects_redirects(ctx):
    redirects = sorted(api.v3.project_redirects(ctx.obj.project_slug), key = RedirectKey.from_dict)

    # List
    if ctx.invoked_subcommand is None:
        with console.pager(styles = True):
            if ctx.obj.json:
                console.print_json(as_json(redirects))
            else:
                table = RedirectTable(title = "Redirects")

                for r in redirects:
                    table.add_row(r["type"], r.get("from_url"), r.get("to_url"))

                console.print(table)

    # Subcommand context
    else:
        ctx.obj.redirects = redirects


# rtd projects <name> redirects sync
@rtd_projects_redirects.command("sync")
@click.pass_context

@click.option("-f", "--file",
    metavar  = "<redirects.yaml>",
    required = True,
    help     = "File describing desired redirects",
    type     = click.File("r"))

@click.option("--dry-run/--wet-run",
    default = True,
    help    = "Pretend to make changes (--dry-run, the default) or actually make changes (--wet-run)")

def rtd_projects_redirects_sync(ctx, file, dry_run):
    existing = ctx.obj.redirects
    desired = yaml.safe_load(file)

    existing_by_key = dict(map(lambda r: (RedirectKey.from_dict(r), r), existing))

    existing_set = set(map(RedirectKey.from_dict, existing))
    desired_set  = set(map(RedirectKey.from_dict, desired))

    to_create = desired_set - existing_set
    to_delete = existing_set - desired_set
    to_keep   = existing_set - to_delete

    created = RedirectTable(title = "Created")
    deleted = RedirectTable(title = "Deleted")

    for r in to_create:
        console.print(f"Creating: {r}")

        if not dry_run:
            api.v3.create_project_redirect(ctx.obj.project_slug, r)

        created.add_row(*r)

    for r in to_delete:
        pk = str(existing_by_key[r]["pk"])

        console.print(f"Deleting: {r} (#{pk})")

        if not dry_run:
            api.v3.delete_project_redirect(ctx.obj.project_slug, pk)

        deleted.add_row(*r)

    console.print(created, deleted)
    console.print(f"Created {len(to_create):,}, deleted {len(to_delete):,}, kept {len(to_keep):,}.", style = "bold")

    if dry_run:
        console.print("")
        console.print("No changes made in --dry-run mode.  Pass --wet-run for realsies.", style = "bold magenta")


def as_json(data):
    return json.dumps(data, indent = 2, allow_nan = False)


class RedirectKey(NamedTuple):
    type: str
    from_url: str
    to_url: str

    @staticmethod
    def from_dict(r):
        return RedirectKey(r["type"], r.get("from_url"), r.get("to_url"))

    def to_dict(self):
        return {
            "type": self.type,
            "from_url": self.from_url,
            "to_url": self.to_url,
        }

    def __str__(self):
        return f"{self.type} {self.from_url} → {self.to_url}"


def RedirectTable(**kwargs):
    table = RichTable(box = rich.box.SIMPLE, **kwargs)
    table.add_column("Type")
    table.add_column("From URL")
    table.add_column("To URL")
    return table


def partition(pred, iterable):
    t1, t2 = tee(iterable)
    return filter(pred, t2), filterfalse(pred, t1)
