#!/usr/bin/env python3
import click
import json
import re
import rich.box
import yaml
from itertools import filterfalse, tee
from os import environ
from rich.console import Console as RichConsole
from rich.table import Table as RichTable
from rich.tree import Tree as RichTree
from shutil import which
from typing import List, NamedTuple
from urllib.parse import quote as urlescape, urljoin

from . import api


__version__ = 5


console = RichConsole(markup = False)

# RichConsole.pager() is documented to respect MANPAGER first then PAGER.  If
# neither are set and less is available, then use it.
PAGER = environ.get("MANPAGER", environ.get("PAGER"))

if not PAGER:
    PAGER = which("less")
    if PAGER:
        environ["PAGER"] = PAGER

pager_is_less = bool(re.search(r"(^|/)less( |$)", PAGER))

if pager_is_less:
    # Setup less to handle styling.  Other pages won't get styles, sorry!
    #
    # -F is --quit-if-one-screen
    # -K is --quit-on-intr (^C)
    # -R is --RAW-CONTROL-CHARS (emit ANSI color escape sequences but no others (unlike -r))
    # -X is --no-init (don't send termcap init, e.g. don't clear the screen)
    #
    environ.setdefault("LESS", "")
    environ["LESS"] += "FKRX"
    pager_styles = True
else:
    pager_styles = False


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
        with console.pager(styles = pager_styles):
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
        with console.pager(styles = pager_styles):
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


# rtd projects <name> maintainers
@rtd_projects.group("maintainers", invoke_without_command = True)
@click.pass_context
def rtd_projects_maintainers(ctx):
    maintainers = project_maintainers(ctx.obj.project_slug)

    # List
    if ctx.invoked_subcommand is None:
        with console.pager(styles = pager_styles):
            if ctx.obj.json:
                console.print_json(as_json(maintainers))
            else:
                for u in maintainers:
                    console.print(u)

    # Subcommand context
    else:
        ctx.obj.maintainers = maintainers


# rtd projects <name> maintainers sync
@rtd_projects_maintainers.command("sync")
@click.pass_context

@click.option("-f", "--file",
    metavar  = "<maintainers.txt>",
    required = True,
    help     = "File listing desired maintainers (by username)",
    type     = click.File("r"))

@click.option("--dry-run/--wet-run",
    default = True,
    help    = "Pretend to make changes (--dry-run, the default) or actually make changes (--wet-run)")

def rtd_projects_maintainers_sync(ctx, file, dry_run):
    if not dry_run and api.unofficial is None:
        raise click.UsageError(f"Support for actually syncing maintainers is not installed.  Please re-install with the maintainers-sync extra, e.g. readthedocs-cli[maintainers-sync].", ctx = ctx)

    existing = set(ctx.obj.maintainers)
    desired = set(line.strip() for line in file)

    to_add    = desired - existing
    to_remove = existing - desired
    to_keep   = existing - to_remove

    for username in sorted(existing | desired):
        if username in to_add:
            console.print(f"+ {username}", style = "green")

            if not dry_run:
                api.unofficial.add_project_maintainer(ctx.obj.project_slug, username)

        elif username in to_remove:
            console.print(f"- {username}", style = "red")

            if not dry_run:
                api.unofficial.remove_project_maintainer(ctx.obj.project_slug, username)

        else:
            console.print(f"• {username}")

    if not dry_run:
        current = set(project_maintainers(ctx.obj.project_slug))
        assert current == desired, f"failed to update maintainers on RTD: {current} != {desired}"

    console.print()
    console.print(f"Added ([green]+[/]) [green]{len(to_add):,}[/], removed ([red]-[/]) [red]{len(to_remove):,}[/], kept {len(to_keep):,}.", style = "bold", markup = True)

    if dry_run:
        console.print("")
        console.print("No changes made in --dry-run mode.  Pass --wet-run for realsies.", style = "bold magenta")


def project_maintainers(project_slug: str) -> List[str]:
    project = api.v3.project(project_slug)
    return sorted(u["username"] for u in project["users"])


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
