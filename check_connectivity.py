#!/usr/bin/env python3
"""
Run this FIRST, before setup.sh — no project dependencies required, just
the standard library. It checks whether each host this project needs is
actually reachable from your current network, which matters behind Cisco
Secure Access / similar SSE tools that can flag AI/ML platforms
specifically (Cisco calls this "AI Access" / shadow-AI blocking),
separately from ordinary developer traffic like GitHub or PyPI.

    python3 check_connectivity.py

IMPORTANT CAVEAT: a response (even an error code) proves the network path
is open, but some corporate proxies intercept a blocked domain and hand
back their OWN 403/redirect page instead of a connection failure. If a
host below shows "RESPONDED (403)" and you're not sure whether that's the
real site or a block page, open the URL in a normal browser once and
look — a block page usually says so in big letters.
"""

import socket
import ssl
import urllib.request
import urllib.error

TIMEOUT = 6

CHECKS = [
    ("pypi.org", "https://pypi.org", "pip installs — required"),
    ("files.pythonhosted.org", "https://files.pythonhosted.org", "pip package downloads — required"),
    ("github.com", "https://github.com", "Allosaurus model download page — required (default phoneme backend)"),
    # Note: Allosaurus's model actually downloads via a redirect from github.com
    # to release-assets.githubusercontent.com with a signed, expiring URL.
    # That CDN host has no root page to test generically (always 404s there
    # regardless of blocking), so it's not included as its own check — if
    # github.com is reachable, the redirect target is rarely blocked
    # separately. The real test is running setup.sh and seeing if the
    # ~40MB download actually completes.
    ("registry.ollama.ai", "https://registry.ollama.ai", "Ollama model pulls — required for coaching tips"),
    ("huggingface.co", "https://huggingface.co", "ONLY needed for the optional Piper neural voice / wav2vec2 backend"),
]


def check(host, url):
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0 (connectivity-check)"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return "REACHABLE", f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        # Connection worked, but got an error status — could be the real
        # site (some reject HEAD/bots) or a corporate block page. Ambiguous
        # on purpose; see caveat above.
        return f"RESPONDED ({e.code})", "ambiguous — see caveat above if unexpected"
    except ssl.SSLError as e:
        return "TLS ERROR", f"handshake failed, often a proxy doing cert inspection ({e})"
    except (socket.timeout, TimeoutError):
        return "TIMEOUT", "no response — likely dropped by a filter"
    except socket.gaierror as e:
        return "DNS FAILURE", f"couldn't resolve hostname — likely blocked at DNS layer ({e})"
    except urllib.error.URLError as e:
        return "BLOCKED", str(e.reason)
    except Exception as e:
        return "ERROR", str(e)


def main():
    print(f"{'HOST':32} {'STATUS':18} NOTE")
    print("-" * 95)
    results = {}
    for host, url, note in CHECKS:
        status, detail = check(host, url)
        results[host] = status
        print(f"{host:32} {status:18} {note}")
        print(f"{'':32} {'':18} -> {detail}")

    print()
    if results.get("github.com", "").startswith("REACHABLE"):
        print("github.com reachable -> Allosaurus (default phoneme backend) should be able to "
              "download its model. If setup.sh still fails on that step, the redirect target "
              "(release-assets.githubusercontent.com) is the specific thing to ask IT about.")
    else:
        print("! github.com itself isn't cleanly reachable. That would block a lot more than "
              "just this app — worth checking with IT directly.")

    if not results.get("huggingface.co", "").startswith("REACHABLE"):
        print("huggingface.co not cleanly reachable — expected on many corporate networks. "
              "No problem: defaults (Allosaurus + espeak-ng TTS) don't need it. Just don't "
              "set PHONEME_BACKEND=wav2vec2 or TTS_BACKEND=piper here.")

    if not results.get("registry.ollama.ai", "").startswith("REACHABLE"):
        print("registry.ollama.ai not cleanly reachable — new `ollama pull` may fail on this "
              "network. Models already pulled elsewhere will still run fine locally.")


if __name__ == "__main__":
    main()
