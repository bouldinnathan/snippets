#!/usr/bin/env python3
import os
import shutil
import subprocess
import traceback
from time import sleep

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# ---------- Helpers ----------
def realpath(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        return out
    except Exception:
        return None

def pick_firefox_binary():
    # Prefer native installs; avoid snap wrapper when possible
    candidates = [
        "/usr/lib/firefox-esr/firefox-esr",
        "/usr/lib/firefox/firefox",
        "/opt/firefox/firefox",
    ]
    # Whatever 'firefox' resolves to
    w = realpath('readlink -f "$(which firefox)"')
    if w:
        candidates.append(w)
    for p in candidates:
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None

def pick_geckodriver():
    # Use a local geckodriver if you’ve placed one, else PATH
    local = "/home/golem/geckodriver"
    if os.path.isfile(local) and os.access(local, os.X_OK):
        return local
    w = shutil.which("geckodriver")
    return w

def pick_chromium_binary():
    # Try common names/paths
    for name in ("chromium-browser", "chromium", "google-chrome", "chrome"):
        w = shutil.which(name)
        if w:
            # resolve wrapper
            w = realpath(f'readlink -f "{w}"') or w
            if os.path.isfile(w) and os.access(w, os.X_OK):
                return w
    # Some distros place it here
    for p in ("/usr/bin/chromium-browser", "/usr/bin/chromium", "/snap/bin/chromium"):
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None

def pick_chromedriver():
    # Prefer PATH
    w = shutil.which("chromedriver")
    if w:
        return w
    # common manual locations
    for p in (
        "/usr/local/bin/chromedriver",
        "/usr/bin/chromedriver",
        "/home/golem/chromedriver",
        "/home/golem/chromedriver-linux64/chromedriver",
    ):
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None

def no_gui():
    return not os.environ.get("DISPLAY")

# ---------- Try Firefox first ----------
def pick_driver(defualt=0):
    driver=None
    if defualt:
        ff_opts = FirefoxOptions()
        # Headless when there’s no GUI (xvfb-run sets DISPLAY, but headless also works fine)
        if no_gui():
            ff_opts.add_argument("--headless")

        ff_bin = pick_firefox_binary()
        if ff_bin:
            ff_opts.binary_location = ff_bin

        gecko_path = pick_geckodriver()
        if not gecko_path:
            raise SystemExit("No geckodriver found. Install geckodriver 0.36.0+ or place it at /home/golem/geckodriver")

        print(f"[Firefox] binary={ff_bin}  geckodriver={gecko_path}  headless={no_gui()}")

        driver = None
        try:
            ff_service = FirefoxService(executable_path=gecko_path, log_output="/tmp/gecko.log")
            driver = webdriver.Firefox(service=ff_service, options=ff_opts)
        except Exception:
            print("\n[Firefox] Failed to start. Traceback:")
            traceback.print_exc()
            print("\nCheck /tmp/gecko.log for details. Trying Chromium fallback...\n")

    # ---------- Chromium fallback (only if Firefox failed) ----------
    if driver is None:
        chrome_bin = pick_chromium_binary()
        chrome_drv = pick_chromedriver()

        if not chrome_bin or not chrome_drv:
            raise SystemExit(f"Chromium fallback unavailable. chrome_bin={chrome_bin}, chromedriver={chrome_drv}")

        ch_opts = ChromeOptions()
        ch_opts.add_argument("--disable-extensions")
        ch_opts.add_argument("--incognito")
        ch_opts.add_argument("--disable-plugins-discovery")
        ch_opts.add_argument("--start-maximized")
        # headless if no GUI (or keep it headless to be consistent)
        if no_gui():
            ch_opts.add_argument("--headless=new")
        ch_opts.binary_location = chrome_bin

        print(f"[Chromium] binary={chrome_bin}  chromedriver={chrome_drv}  headless={no_gui()}")

        ch_service = ChromeService(executable_path=chrome_drv)
        driver = webdriver.Chrome(service=ch_service, options=ch_opts)
    return driver
# ---------- Do the work ----------



##
#
#
# Flask API
#
#
#
#
##



from flask import Flask, request, jsonify
from urllib.parse import urlparse
from time import perf_counter
import logging
from markdownify import markdownify as md
from bs4 import BeautifulSoup, Comment
import re

app = Flask(__name__)

JUNK_RE = re.compile(
    r"(cookie|consent|banner|modal|subscribe|signup|newsletter|promo|advert|ads?"
    r"|share|social|overlay|backdrop|popover|tooltip|sidebar|nav|header|footer|"
    r"breadcrumb|pagination|related|recommend|outbrain|taboola)",
    re.I
)


def clean_html(html: str) -> str:
    # lxml parser handles malformed HTML better; falls back if not installed
    soup = BeautifulSoup(html, "lxml")

    # 1) Remove script/style-like elements entirely
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()

    # 2) Remove HTML comments
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()

    # 3) Remove common junk by class/id
    for el in soup.find_all(attrs={"class": JUNK_RE}):
        el.decompose()
    for el in soup.find_all(attrs={"id": JUNK_RE}):
        el.decompose()

    # 4) Strip inline event handlers (onclick, onload, etc.)
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith("on"):
                del tag.attrs[attr]

    return str(soup)


def to_markdown(html,keep_links=False, keep_images=False):
    stage0=clean_html(html)

    convert_tags = ['table', 'thead', 'tbody', 'th', 'td', 'tr', 'pre', 'code']
    if keep_links:convert_tags.append('a')
    if keep_images:convert_tags.append('img')



    stage1 = md(
        stage0,
        #strip=['script', 'style', 'noscript'],
        heading_style="ATX",
        bullets="-",
        strong_em_symbol="*",
        autolinks=True,
        keep_inline_images=True,
        convert=convert_tags
    )

    return md(
        stage1,
        strip=['script', 'style', 'noscript'],
        heading_style="ATX",
        bullets="-",
        strong_em_symbol="*",
        autolinks=True,
        keep_inline_images=True #,
        #convert=['img', 'a', 'table', 'thead', 'tbody', 'th', 'td', 'tr', 'pre', 'code']
    )

def run_on_this_url(url: str,markdown=True,keep_links=False, keep_images=False):
    """
    Your long-running function goes here.
    Must return something JSON-serializable (dict/list/str/number/bool/None),
    OR an object you convert to a JSON-serializable type below.
    """
    def waiter(driver):
        #waits for browser thinks the page is done
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # wait for visible content
        WebDriverWait(driver, 30).until(
            lambda d: len(d.find_elements(By.XPATH, "//*")) > 0
        )


    try:
        driver=pick_driver(defualt=0)
        driver.get(url)
        title=driver.title
        #print(title)
        waiter(driver)
        if markdown:source = to_markdown(driver.page_source,keep_links=False, keep_images=False)
        else:source = driver.page_source
        #print(source[:1000])  # don’t spam the whole page
        driver.quit()
    except Exception as e:
        return jsonify({"error": e, "input_url": url}),500


    # Example placeholder result:
    return {"url_source": source,"title":title}
# ----------------------------------------------------


def _validate_url(u: str) -> bool:
    try:
        p = urlparse(u)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


@app.route("/api", methods=["POST"])
def run():
    """
    POST /api
    Accepts JSON: { "url": "https://example.com" }
    Also accepts query param: /run?url=...
    Returns: { "ok": true, "url": "...", "data": <your function's result>, "duration_ms": 1234 }
    """
    # Accept both JSON and querystring for convenience
    url = None
    if request.is_json:
        body = request.get_json(silent=True) or {}
        url = body.get("url")
        markdown = body.get("markdown") or True
        keep_links = body.get("keep_links") or False
        keep_images = body.get("keep_images") or False
    if url is None:
        url = request.args.get("url")
        markdown = request.args.get("markdown") or True
        keep_links = request.args.get("keep_links") or False
        keep_images = request.args.get("keep_images") or False

    if not url or not isinstance(url, str) or not _validate_url(url):
        return jsonify({
            "ok": False,
            "error": "Invalid or missing 'url'. Provide http(s) URL in JSON body or as ?url=."
        }), 400

    started = perf_counter()
    try:
        # defaults are markdown = True, keep_links = False, keep_images = False
        data = run_on_this_url(url, markdown = markdown, keep_links = keep_links, keep_images = keep_images)

        # If your function returns something not JSON-serializable, convert it here.
        # Example: if it returns a dataclass or custom object, map it to dict.

        duration_ms = int((perf_counter() - started) * 1000)
        return jsonify({
            "ok": True,
            "url": url,
            "data": str(data),
            "duration_ms": duration_ms
        }), 200

    except Exception as e:
        logging.exception("Processing failed")
        return jsonify({
            "ok": False,
            "url": url,
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "up"}), 200

@app.route("/", methods=["GET"])
def help():
    help_data='''# JSON body
curl -s -X POST http://localhost:8000/run \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}' | jq
todo:descripe this markdown = True, keep_links = False, keep_images = False
# Query string (also works)
curl -s -X POST 'http://localhost:8000/run?url=https://example.com' | jq
'''


    return help_data,200


if __name__ == "__main__":
    # For local dev only. Use gunicorn in production (see below).
    # This will handle a single long-running request fine.
    app.run(host="0.0.0.0", port=8000, debug=False)

















driver=pick_driver(defualt=0)
driver.get("https://google.com")
print(driver.title)
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))
print(driver.page_source[:1000])  # don’t spam the whole page
driver.quit()
