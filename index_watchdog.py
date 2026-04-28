"""
Car Jury — Index Watchdog
Checks every URL in the site's sitemaps for signals that could cause Google deindexing.
Tracks state across runs; reports new issues and recoveries.

Checks per URL:
  - HTTP status code (non-200 = warning)
  - <meta name="robots" content="noindex"> in HTML
  - X-Robots-Tag: noindex in response headers
  - Canonical tag pointing away from the expected URL
  - Redirects (3xx) to different page
"""

from __future__ import annotations
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests as _req
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

SITEMAPS = [
    "sitemap-core.xml",
    "sitemap-reviews.xml",
    "sitemap-compare.xml",
    "sitemap-influencers.xml",
]

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

_NOINDEX_META = re.compile(
    r'<meta[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_CANONICAL_HREF = re.compile(r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', re.IGNORECASE)
_CANONICAL_REL  = re.compile(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)


def _sitemap_urls(carjury_dir: Path) -> list[str]:
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls: list[str] = []
    for sm in SITEMAPS:
        f = carjury_dir / sm
        if not f.exists():
            continue
        try:
            tree = ET.parse(f)
            urls.extend(e.text for e in tree.findall("sm:url/sm:loc", ns) if e.text)
        except Exception:
            pass
    return urls


def _check_url(url: str) -> dict:
    result: dict = {"url": url, "http_status": None, "issues": []}
    if not _REQUESTS_OK:
        result["issues"].append("requests_not_installed")
        return result
    try:
        r = _req.get(
            url,
            timeout=15,
            headers={"User-Agent": _UA},
            allow_redirects=True,
        )
        result["http_status"] = r.status_code
        final_url = r.url.rstrip("/")
        expected = url.rstrip("/")

        if r.status_code != 200:
            result["issues"].append(f"http_{r.status_code}")
            return result

        # Redirect to different page
        if final_url != expected and not final_url.startswith(expected):
            result["issues"].append(f"redirected_to:{final_url}")

        # X-Robots-Tag header
        x_robots = r.headers.get("X-Robots-Tag", "").lower()
        if "noindex" in x_robots:
            result["issues"].append("noindex_header")

        html = r.text[:50_000]  # first 50KB is enough for <head>

        # Meta robots noindex
        m = _NOINDEX_META.search(html)
        if m and "noindex" in m.group(1).lower():
            result["issues"].append("noindex_meta")

        # Canonical pointing away — handle both attribute orderings
        c = _CANONICAL_HREF.search(html) or _CANONICAL_REL.search(html)
        if c:
            canon = c.group(1).rstrip("/")
            if canon != expected and not canon.startswith(expected):
                result["issues"].append(f"canonical_mismatch:{canon}")
        else:
            result["issues"].append("missing_canonical")

    except _req.exceptions.Timeout:
        result["issues"].append("timeout")
    except Exception as e:
        result["issues"].append(f"error:{str(e)[:80]}")

    return result


def run_index_watchdog(carjury_dir: Path, state_dir: Path) -> dict:
    """
    Check all sitemap URLs. Returns:
      total, ok, all_issues, new_issues, recovered
    """
    state_file = state_dir / "index_watchdog_state.json"
    prev: dict = {}
    if state_file.exists():
        try:
            prev = json.loads(state_file.read_text())
        except Exception:
            pass

    urls = _sitemap_urls(carjury_dir)
    current: dict = {}
    for url in urls:
        current[url] = _check_url(url)
        time.sleep(0.3)

    # Persist new state
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(current, indent=2))

    prev_bad = {u for u, d in prev.items() if d.get("issues")}
    curr_bad = {u for u, d in current.items() if d.get("issues")}

    return {
        "total": len(urls),
        "ok": sum(1 for d in current.values() if not d.get("issues")),
        "all_issues": [
            {"url": u, "issues": current[u]["issues"]}
            for u in curr_bad
        ],
        "new_issues": [
            {"url": u, "issues": current[u]["issues"]}
            for u in (curr_bad - prev_bad)
        ],
        "recovered": sorted(prev_bad - curr_bad),
    }
