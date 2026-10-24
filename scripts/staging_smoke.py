"""Read-only HTTP smoke test for a staging origin; no credentials needed."""
import argparse
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

PUBLIC_PATHS = (
    "/", "/courses/", "/articles/", "/about/", "/contact/",
    "/account/login/", "/sitemap.xml", "/robots.txt",
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def request_page(opener, url):
    request = Request(url, headers={"User-Agent": "SCSGyanStagingSmoke/1.0"})
    try:
        with opener.open(request, timeout=15) as response:
            return response.status, response.headers, response.read(250_000)
    except HTTPError as error:
        return error.code, error.headers, error.read(4000)


def check(base_url, allow_http=False):
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" and not (allow_http and parsed.scheme == "http"):
        raise ValueError("Staging requires HTTPS; --allow-http is for local CI only.")
    if not parsed.netloc or parsed.username or parsed.password or parsed.path not in ("", "/"):
        raise ValueError("Provide only the hostname origin without credentials/subpaths.")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    opener = build_opener(NoRedirect())
    issues = []
    for path in PUBLIC_PATHS:
        status, headers, body = request_page(opener, urljoin(origin, path))
        if status != 200:
            issues.append(f"{path}: expected HTTP 200, got HTTP {status}")
            continue
        if path.endswith(".xml") and b"<urlset" not in body:
            issues.append("Sitemap response has no XML urlset.")
        if path.endswith(".txt") and b"Sitemap:" not in body:
            issues.append("robots.txt lacks sitemap reference.")
        if path not in ("/robots.txt", "/sitemap.xml"):
            canonical = f'href="{origin}{path}"'.encode()
            if canonical not in body:
                issues.append(f"{path}: canonical scheme or host mismatch.")
    path = "/account/dashboard/"
    status, headers, _ = request_page(opener, urljoin(origin, path))
    if status != 302 or urlsplit(headers.get("Location", "")).path != "/account/login/":
        issues.append(f"{path}: expected 302 to login, got HTTP {status}.")
    if issues:
        raise AssertionError("\n".join(issues))
    print(f"PASS: {len(PUBLIC_PATHS)} public routes and private-dashboard redirect at {origin}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="HTTPS staging origin")
    parser.add_argument("--allow-http", action="store_true", help="Local CI use only")
    args = parser.parse_args()
    for attempt in range(30):
        try:
            check(args.base_url, args.allow_http)
            return
        except (URLError, ConnectionError, TimeoutError, OSError):
            if attempt == 29:
                raise
            time.sleep(1)


if __name__ == "__main__":
    main()
