"""
Read the Docs "unofficial" web API (the user-facing dashboard UI)

https://readthedocs.org/dashboard/
"""
import browser_cookie3
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote as urlescape, urljoin


ua = requests.Session()

# RTD requires a "sessionid" cookie and "csrftoken" cookie
ua.cookies = browser_cookie3.load(domain_name = ".readthedocs.org")


def add_project_maintainer(project_slug: str, username: str):
    _update_users("add", project_slug, username)

def remove_project_maintainer(project_slug: str, username: str):
    _update_users("delete", project_slug, username)

def _update_users(action: str, project_slug: str, username: str):
    assert action in {"add", "delete"}

    if action == "add":
        path = f"{urlescape(project_slug)}/users/"
        key = "user"

    elif action == "delete":
        path = f"{urlescape(project_slug)}/users/delete/"
        key = "username" # lol

    res = ua.post(
        api_url(path),
        data = {
            key: username,
            **csrf_token(GET(f"{urlescape(project_slug)}/users/")),
        },
        headers = {
            # Required by their CSRF protection middleware.
            "Referer": api_url(f"{urlescape(project_slug)}/users/"),
        },
        # No point in following this extra request.
        allow_redirects = False,
    )

    res.raise_for_status()


def csrf_token(html: str):
    name = "csrfmiddlewaretoken"
    doc = BeautifulSoup(html, "html.parser")
    token = doc.find(attrs = {"name": name})
    return {name: token["value"]}


def GET(path):
    res = ua.get(api_url(path))
    res.raise_for_status()
    return res.text


def api_url(path):
    return urljoin("https://readthedocs.org/dashboard/", path.lstrip("/"))
