"""Capture a safe local Django demo for client UI review.

Uses disposable SQLite/demo content only; never starts a public staging server.
"""
import html
import json
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:8000"
OUTPUT = Path(__file__).resolve().parents[1] / "client-review"
PAGES = [
    ("home", "/", "Build knowledge."),
    ("courses", "/courses/", "Explore Courses"),
    ("course-detail", "/courses/upsc-foundation-course/", "UPSC Foundation Course"),
    ("articles", "/articles/", "Current Affairs & Articles"),
    ("login", "/account/login/", "Login"),
    ("signup", "/account/signup/", "Create"),
    ("about", "/about/", "About"),
    ("contact", "/contact/", "Contact"),
]
VIEWPORTS = [("mobile", 390, 844), ("tablet", 768, 1024), ("desktop", 1280, 800)]


def await_server():
    for _ in range(30):
        try:
            with urlopen(BASE_URL + "/", timeout=2) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError, OSError):
            time.sleep(1)
    raise RuntimeError("Local Django demo server did not become available.")


def capture():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    await_server()
    shots = []
    failures = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for label, width, height in VIEWPORTS + [("small-mobile", 320, 700)]:
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    device_scale_factor=1,
                    reduced_motion="reduce",
                )
                try:
                    for name, path, heading in PAGES:
                        # 320px is an additional overflow gate; main gallery uses 3 viewports.
                        if label == "small-mobile" and name not in ("home", "courses", "login"):
                            continue
                        response = page.goto(BASE_URL + path, wait_until="networkidle", timeout=30000)
                        shot_name = f"{name}-{label}.png"
                        page.screenshot(path=str(OUTPUT / shot_name), full_page=True)
                        shots.append((name, label, shot_name))
                        if response is None or response.status != 200:
                            failures.append(f"{path} at {width}px did not return HTTP 200")
                            continue
                        body = page.locator("body").inner_text()
                        if heading.lower() not in body.lower():
                            failures.append(f"{path} at {width}px: expected heading missing")
                        dimensions = page.evaluate(
                            "() => ({ documentWidth: document.documentElement.scrollWidth,"
                            " viewport: window.innerWidth })"
                        )
                        if dimensions["documentWidth"] > dimensions["viewport"] + 2:
                            failures.append(
                                f"{path} at {width}px: horizontal overflow "
                                f"({dimensions['documentWidth']} > {dimensions['viewport']})"
                            )
                        for link in page.locator('nav[aria-label="Main navigation"] a').all():
                            box = link.bounding_box()
                            if box and (box["x"] < -2 or box["x"] + box["width"] > width + 2):
                                failures.append(f"{path} at {width}px: navigation link clipped")
                                break
                finally:
                    page.close()
        finally:
            browser.close()

    title = "SCS Gyan — Client UI Review"
    cards = "".join(
        f'<figure><a href="{html.escape(filename)}">'
        f'<img loading="lazy" src="{html.escape(filename)}" '
        f'alt="{html.escape(name + " " + label)} screenshot"></a>'
        f'<figcaption>{html.escape(name.replace("-", " ").title())} · '
        f'{html.escape(label.title())}</figcaption></figure>'
        for name, label, filename in shots
    )
    gallery = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
body{{font:16px/1.6 system-ui,sans-serif;margin:0;background:#f5f7fc;color:#19294b}}
main{{max-width:1260px;padding:24px;margin:auto}}
h1{{font-size:clamp(26px,4vw,42px);margin-bottom:8px}}
p{{max-width:860px;color:#56637a}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:22px}}
figure{{margin:0;border:1px solid #dfe6f2;background:white;border-radius:12px;overflow:hidden}}
figure img{{display:block;width:100%;max-height:460px;object-fit:cover;object-position:top}}
figcaption{{padding:14px 18px;font-weight:600}}
</style></head><body><main><h1>{title}</h1>
<p>Automated screenshots from a running local Django application.
All courses, pricing and content are <strong>demonstration data only</strong>.
No live domain, payment gateway or production environment is included.
Open an image to inspect its full size.</p>
<div class="grid">{cards}</div></main></body></html>"""
    (OUTPUT / "index.html").write_text(gallery, encoding="utf-8")
    manifest = {
        "purpose": "client UI acceptance of local Django demonstration only",
        "production": False,
        "payment_processing": False,
        "screenshots": [fn for _, _, fn in shots],
        "issues": failures,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8",
    )
    (OUTPUT / "README.txt").write_text(
        "SCS Gyan client UI review pack\n"
        "Open index.html in a browser; screenshots work offline.\n"
        "Prices and content are fictional samples. No staging URL is deployed.\n"
        "Review desktop, tablet, mobile, and 320px layouts before sign-off.\n",
        encoding="utf-8",
    )
    print(f"Captured {len(shots)} pages, with {len(failures)} issue(s).")
    if failures:
        raise AssertionError("\n".join(failures))


if __name__ == "__main__":
    capture()
