"""Read-only NEAR JSON-RPC helper. Standard library only: no key, no account, no install.

Every figure in this project comes from a view call or a block header fetched through here,
always at an explicit block height, so the same call returns the same answer for anyone, forever.
"""
import base64
import json
import os
import threading
import time
import urllib.error
import urllib.request

# Archival nodes keep old state. Override with ARCHIVAL_RPC to check the numbers against another provider.
ENDPOINTS = [u for u in os.environ.get(
    "ARCHIVAL_RPC",
    "https://archival-rpc.mainnet.fastnear.com",
).split(",") if u]

LEDGER = "intents.near"
# The account that holds, on public NEAR, everything the private chain owes its users.
# Source: docs.near-intents.org, "Confidential Intents" (PRIVATE_TREASURY_ACCOUNT_ID, "production
# constants shared by all solver operators"). Recorded with how it was checked in docs/SOURCES.md.
TREASURY = "51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe"


# Public nodes rate-limit by address. Stay under it: at most RPC_RATE requests a second, all threads together.
_RATE = float(os.environ.get("RPC_RATE", "3"))
_lock = threading.Lock()
_next = [0.0]


def _wait_turn():
    with _lock:
        now = time.monotonic()
        at = max(now, _next[0])
        _next[0] = at + 1.0 / _RATE
    if at > now:
        time.sleep(at - now)


class RpcError(Exception):
    pass


class UnknownBlock(RpcError):
    pass


def call(method, params, tries=14):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for attempt in range(tries):
        url = ENDPOINTS[attempt % len(ENDPOINTS)]
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "User-Agent": "waterline/1"})
        _wait_turn()
        try:
            with urllib.request.urlopen(req, timeout=45) as res:
                out = json.load(res)
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:  # told to slow down: back off for everyone, not just this thread
                with _lock:
                    _next[0] = max(_next[0], time.monotonic() + min(20, 2 * (attempt + 1)))
            else:
                time.sleep(min(8, 0.6 * 2 ** attempt))
            continue
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
            last = e
            time.sleep(min(8, 0.6 * 2 ** attempt))
            continue
        if "error" in out:
            text = json.dumps(out["error"])
            if "UNKNOWN_BLOCK" in text or "DB Not Found" in text:
                raise UnknownBlock(text[:200])
            if "TIMEOUT" in text or "Too Many" in text or "rate" in text.lower():
                last = RpcError(text[:200])
                time.sleep(min(8, 0.6 * 2 ** attempt))
                continue
            raise RpcError(text[:300])
        return out["result"]
    raise RpcError(f"gave up after {tries} tries: {last}")


def header(block_id):
    """Block header at a height, or the latest final block when block_id is None."""
    params = {"finality": "final"} if block_id is None else {"block_id": block_id}
    return call("block", params)["header"]


def view(height, contract, method, args):
    """A contract view call at an exact height. Returns the decoded JSON, or None when the contract
    has no such method or no such state at that height (a failed read is 'unknown', never 0)."""
    try:
        res = call("query", {
            "request_type": "call_function", "block_id": height, "account_id": contract,
            "method_name": method,
            "args_base64": base64.b64encode(json.dumps(args).encode()).decode()})
    except UnknownBlock:
        raise
    except RpcError as e:
        if any(k in str(e) for k in ("MethodNotFound", "does not exist", "CodeDoesNotExist",
                                      "UNKNOWN_ACCOUNT", "NO_CONTRACT_CODE", "wasm execution failed")):
            return None
        raise
    if "error" in res:
        return None
    return json.loads(bytes(res["result"]).decode())
