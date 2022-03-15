"""
Read the Docs web API v3

https://docs.readthedocs.io/en/stable/api/v3.html
"""
import requests
from os import environ
from urllib.parse import quote as urlescape, urljoin


RTD_TOKEN = environ.get("RTD_TOKEN")

ua = requests.Session()

if RTD_TOKEN:
    ua.headers["Authorization"] = f"Token {RTD_TOKEN}"


def projects():
    return GET("projects/", {"limit": 100})

def project(project_slug: str):
    return GET(f"projects/{urlescape(project_slug)}/")

def project_redirects(project_slug: str):
    return GET(f"projects/{urlescape(project_slug)}/redirects/", {"limit": 100})

def create_project_redirect(project_slug: str, redirect: dict):
    return POST(f"projects/{urlescape(project_slug)}/redirects/", redirect.to_dict())

def delete_project_redirect(project_slug: str, redirect_pk: str):
    return DELETE(f"projects/{urlescape(project_slug)}/redirects/{urlescape(redirect_pk)}")


def GET(path, params = None):
    url = api_url(path)

    # Paged collection
    if params and "limit" in params:
        total = None
        results = []

        while url:
            res = ua.get(url, params = params)
            res.raise_for_status()

            body = res.json()

            if total is None:
                total = body["count"]

            if body["results"]:
                results += body["results"]

            url = body["next"]

        assert len(results) == total

        return results

    # Single resource
    else:
        res = ua.get(url, params = params)
        res.raise_for_status()
        return res.json()


def POST(path, body):
    res = ua.post(api_url(path), json = body)
    res.raise_for_status()

    return res


def DELETE(path):
    res = ua.delete(api_url(path))
    res.raise_for_status()

    return res


def api_url(path):
    return urljoin("https://readthedocs.org/api/v3/", path.lstrip("/"))
