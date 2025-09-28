#!/usr/bin/env python3
"""
Default behavior:
  - Performs GET to https://zoo0.pages.dev using User-Agent "Dart/3.8 (dart:io)"
  - Reads response headers and combines: x-request-id + x-payload + authorization + x-data
  - Base64-decodes + XOR-decrypts using key "k6kW8r#Tz3f;" to extract JSON -> baseUrl
  - Calls baseUrl/api/v1/auth/generate?server=1 and routes to appropriate handler

Domain-based routing:
  - If keyUrl contains "nanolinks", uses the nano handler
  - If keyUrl contains "arolinks", uses the aro handler
  - If keyUrl contains "lksfy", uses the lksfy handler

Flags:
  --ssl-bypass    : Disable SSL verification (requests.verify=False). Handy for Termux/testing.
  --debug         : Show debug/background traces.

If you want to target a different URL, set environment variable TARGET_URL (no CLI flags needed).
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import hashlib
from urllib.parse import urlparse, parse_qs, quote

try:
    import requests
except Exception:
    print("ERROR: missing dependency 'requests'. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from Crypto.Cipher import AES
except Exception:
    print("WARNING: missing dependency 'pycryptodome'. Install: pip install pycryptodome", file=sys.stderr)
    print("         AES decryption for lksfy links will not work", file=sys.stderr)

# Colors (fallback gracefully)
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except Exception:
    class _C:
        RESET = ""; RED = ""; GREEN = ""; YELLOW = ""; CYAN = ""; MAGENTA = ""
    Fore = type("F", (), {"RED": _C.RED, "GREEN": _C.GREEN, "YELLOW": _C.YELLOW, "CYAN": _C.CYAN, "MAGENTA": _C.MAGENTA})
    Style = type("S", (), {"BRIGHT": "", "NORMAL": ""})

def err(msg): print(f"{Fore.RED}[ERROR]{Style.NORMAL} {msg}", file=sys.stderr)
def info(msg): print(f"{Fore.CYAN}[INFO]{Style.NORMAL} {msg}")
def ok(msg): print(f"{Fore.GREEN}[OK]{Style.NORMAL} {msg}")
def dbg(msg, on): 
    if on:
        print(f"{Fore.MAGENTA}[DEBUG]{Style.NORMAL} {msg}")

# default target host 
DEFAULT_TARGET = "https://zoo0.pages.dev"
DEFAULT_USER_AGENT = "Dart/3.8 (dart:io)"
KEY = "k6kW8r#Tz3f;"

HEADER_NAMES = ("x-request-id", "x-payload", "authorization", "x-data")
def get_initial_response_headers(target_url, user_agent, verify, debug):
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    dbg(f"GET {target_url} (verify={verify})", debug)
    try:
        resp = session.get(target_url, timeout=25, verify=verify, allow_redirects=True)
        dbg(f"Status {resp.status_code}", debug)
    except Exception as e:
        raise RuntimeError(f"Initial GET failed: {e}")
    return resp.headers, resp

def build_combined(headers, debug):
    parts = []
    missing = []
    for hn in HEADER_NAMES:
        val = None
        # headers is case-insensitive in requests but iterate for safety
        for k, v in headers.items():
            if k.lower() == hn.lower():
                val = v.strip()
                break
        if val is None:
            missing.append(hn)
            parts.append("")  # preserve order
        else:
            dbg(f"Found header {hn} (len={len(val)})", debug)
            parts.append(val)
    combined = "".join(parts)
    dbg(f"Combined length: {len(combined)}", debug)
    return combined, missing

def decode_b64_xor(combined_b64: str, xor_key: bytes, debug: bool=False) -> str:
    if not combined_b64:
        raise ValueError("Combined base64 string empty")
    try:
        raw = base64.b64decode(combined_b64)
    except Exception as e:
        raise ValueError(f"Base64 decode failed: {e}")
    dbg(f"Decoded bytes: {len(raw)}", debug)
    if not xor_key:
        raise ValueError("XOR key empty")
    out = bytearray(len(raw))
    for i, b in enumerate(raw):
        out[i] = b ^ xor_key[i % len(xor_key)]
    # try utf-8
    try:
        text = out.decode("utf-8")
        dbg("Decoded to UTF-8", debug)
        return text
    except UnicodeDecodeError:
        dbg("UTF-8 failed; trying to extract JSON substring", debug)
        txt = out.decode("latin1", errors="ignore")
        start = txt.find("{")
        end = txt.rfind("}")
        if start != -1 and end != -1 and end > start:
            return txt[start:end+1]
        raise ValueError("Decoded bytes not valid UTF-8 and no JSON substring found")

def extract_baseurl(decoded_text: str, debug: bool=False) -> str:
    dbg(f"Decoded preview: {decoded_text[:400]}", debug)
    try:
        obj = json.loads(decoded_text)
    except Exception as e:
        dbg("JSON parse failed; extracting block", debug)
        start = decoded_text.find("{")
        end = decoded_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"JSON parse failed: {e}")
        obj = json.loads(decoded_text[start:end+1])
    if not isinstance(obj, dict):
        raise ValueError("Decoded JSON not an object")
    for k in ("baseUrl", "baseurl", "base_url"):
        if k in obj:
            return obj[k]
    raise ValueError("'baseUrl' not found in decoded JSON")

def fetch_key_flow(baseurl: str, verify: bool, debug: bool, user_agent: str = None) -> tuple:
    session = requests.Session()
    if user_agent:
        session.headers.update({"User-Agent": user_agent})
    else:
        session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; Python script)"})

    url1 = baseurl.rstrip("/") + "/api/v1/auth/generate?server=1"
    dbg(f"Request1 -> {url1}", debug)
    try:
        r1 = session.get(url1, timeout=30, verify=verify)
        dbg(f"Request1 status: {r1.status_code}", debug)
        r1.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Request 1 failed: {e}")

    try:
        json1 = r1.json()
        dbg(f"JSON1 preview: {json.dumps(json1)[:800]}", debug)
    except Exception as e:
        raise RuntimeError(f"Response1 not JSON: {e}")

    try:
        key_url = json1["data"]["keyUrl"]
       # key_url = "https://lksfy.com/8TRBMLM29A"
    except Exception as e:
        raise RuntimeError(f"keyUrl missing in response1 JSON: {e}")

    info(f"keyUrl: {key_url}")
    
    # Domain-based routing logic
    if "nanolinks" in key_url:
        info("Detected nanolinks domain, using nano handler")
        return handle_nano_links(key_url, session, verify, debug)
    elif "arolinks" in key_url:
        info("Detected arolinks domain, using aro handler")
        return handle_aro_links(key_url, session, verify, debug)
    elif "lksfy" in key_url:
        info("Detected lksfy domain, using lksfy handler")
        return handle_lksfy(key_url, session, verify, debug)
    else:
        # Fallback to nano handler as default
        info("Unknown domain, using nano handler as fallback")
        return handle_nano_links(key_url, session, verify, debug)


def handle_nano_links(key_url, session, verify, debug):
    """
    Handler for nanolinks.in URLs
    Process:
    1. Extract ID from the URL
    2. Make GET request to https://nano.tackledsoul.com/includes/open.php?id={extracted_id} with cookies
    3. Follow redirect to http://sharedisklinks.com/{new_id} and extract new ID
    4. Make request to https://vi-music.app/includes/open.php?id={new_id} with cookies
    5. Follow redirect to https://generateed.pages.dev/?key={key} and extract key
    """
    info("Using nanolinks handler...")
    
    # Extract ID from the URL
    parsed = urlparse(key_url)
    extracted_id = parsed.path.strip("/").split("/")[-1]
    info(f"Extracted ID from URL: {extracted_id}")
    
    # First request with extracted ID
    first_url = f"https://nano.tackledsoul.com/includes/open.php?id={extracted_id}"
    cookies = {
        "tp": extracted_id,
        "open": extracted_id
    }
    
    dbg(f"Nanolinks request 1 -> {first_url}", debug)
    try:
        # Don't follow redirects automatically so we can capture the redirect URL
        r1 = session.get(first_url, cookies=cookies, timeout=30, verify=verify, allow_redirects=False)
        dbg(f"Nanolinks request 1 status: {r1.status_code}", debug)
        
        if r1.status_code in (301, 302, 303, 307, 308):
            redirect_url = r1.headers.get('Location')
            dbg(f"Redirect URL: {redirect_url}", debug)
            
            # Extract new ID from redirect URL
            parsed = urlparse(redirect_url)
            new_id = parsed.path.strip("/").split("/")[-1]
            info(f"Extracted new ID: {new_id}")
            
            # Second request with new ID
            second_url = f"https://vi-music.app/includes/open.php?id={new_id}"
            new_cookies = {
                "tp": new_id,
                "open": new_id
            }
            
            dbg(f"Nanolinks request 2 -> {second_url}", debug)
            r2 = session.get(second_url, cookies=new_cookies, timeout=30, verify=verify, allow_redirects=False)
            dbg(f"Nanolinks request 2 status: {r2.status_code}", debug)
            
            if r2.status_code in (301, 302, 303, 307, 308):
                final_redirect = r2.headers.get('Location')
                dbg(f"Final redirect URL: {final_redirect}", debug)
                
                # Extract key from final redirect URL
                parsed = urlparse(final_redirect)
                key = parse_qs(parsed.query).get("key", [None])[0]
                
                if key:
                    ok(f"Extracted key from nanolinks: {key}")
                    return key, None, None
                else:
                    return None, key_url, RuntimeError("Could not extract 'key' parameter from final redirect URL")
            else:
                return None, key_url, RuntimeError(f"Second request did not redirect as expected: {r2.status_code}")
        else:
            return None, key_url, RuntimeError(f"First request did not redirect as expected: {r1.status_code}")
    except Exception as e:
        return None, key_url, RuntimeError(f"Nanolinks handler failed: {e}")

def handle_aro_links(key_url, session, verify, debug):
    """
    Handler for arolinks.com URLs
    """
    info("Using arolinks handler...")
    
    # Extract the identifier from the URL
    parsed = urlparse(key_url)
    identifier = parsed.path.strip("/").split("/")[-1]
    info(f"Extracted identifier: {identifier}")
    
    # Make initial request
    dbg(f"Arolinks request 1 -> {key_url}", debug)
    try:
        response = session.get(key_url, timeout=30, verify=verify)
        dbg(f"Arolinks request 1 status: {response.status_code}", debug)
        
        if response.status_code == 200:
            # Extract the redirect URL from the response
            redirect_url_match = re.search(r'window\.location\.href = "([^"]+)"', response.text)
            
            if not redirect_url_match:
                # Try to find it in the <a> tag
                redirect_url_match = re.search(r'<a href="([^"]+)"', response.text)
            
            if redirect_url_match:
                redirect_url = redirect_url_match.group(1)
                dbg(f"Found redirect URL: {redirect_url}", debug)
                
                # Update headers for the second request
                updated_headers = {
                    "cookie": f"gt_uc_={identifier}",
                    "referer": redirect_url
                }
                
                # Make the second request
                dbg(f"Arolinks request 2 -> {key_url} with updated headers", debug)
                second_response = session.get(key_url, headers=updated_headers, timeout=30, verify=verify)
                dbg(f"Arolinks request 2 status: {second_response.status_code}", debug)
                
                if second_response.status_code == 200:
                    # Extract the final URL with the key
                    final_url_match = re.search(r'nofollow noopener noreferrer" href="(https?://[^"]+key=[^"&]+[^"]*)"', second_response.text)
                    final_url_match2 = re.search(r'nofollow noopener noreferrer" href="(https?://[^"]+code=[^"&]+[^"]*)"', second_response.text)

                    if final_url_match:
                        final_url = final_url_match.group(1)
                        dbg(f"Found final URL: {final_url}", debug)
                        key_match = re.search(r'key=([^&"]+)', final_url)
                        if key_match:
                            key = key_match.group(1)
                            ok(f"Extracted key: {key}")
                            return key, None, None
                    elif final_url_match2:
                        final_url = final_url_match2.group(1)
                        code_match = re.search(r'code=([^&"]+)', final_url)
                        if code_match:
                            key = code_match.group(1)
                            ok(f"Extracted code as key: {key}")
                            return key, None, None
                    
                    return None, key_url, RuntimeError("Final URL with key/code not found in the second response")
                else:
                    return None, key_url, RuntimeError(f"Second request failed with status code: {second_response.status_code}")
            else:
                return None, key_url, RuntimeError("Redirect URL not found in the initial response")
        else:
            return None, key_url, RuntimeError(f"Initial request failed with status code: {response.status_code}")
    except Exception as e:
        return None, key_url, RuntimeError(f"Arolinks handler failed: {e}")


def decrypt(chipertext: str, alias: str, debug: bool=False) -> str:
    try:
        key_source = "sDye71jNq5" + alias
        iv_source = "7M9u8DG4X" + alias
        key_hash = hashlib.sha256(key_source.encode("utf-8")).hexdigest()
        iv_hash = hashlib.sha256(iv_source.encode("utf-8")).hexdigest()
        key_bytes = key_hash[:32].encode("utf-8")  # 32 bytes -> AES-256
        iv_bytes = iv_hash[:16].encode("utf-8")    # 16 bytes -> IV
        ciphertext = base64.b64decode(base64.b64decode(chipertext)) # Decoding base64 twice
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv_bytes)
        decrypted = cipher.decrypt(ciphertext)
        return decrypted.decode("utf-8")
    except Exception as e:
        dbg(f"Decryption error: {e}", debug)
        return None

def extract_form_data(html_content):
    # Extract _csrfToken
    csrf_token_match = re.search(r'name="_csrfToken"[^>]*value="([^"]+)"', html_content)
    csrf_token = csrf_token_match.group(1) if csrf_token_match else ""
    
    # Extract ad_form_data
    ad_form_data_match = re.search(r'name="ad_form_data"[^>]*value="([^"]+)"', html_content)
    ad_form_data = ad_form_data_match.group(1) if ad_form_data_match else ""
    
    # Extract Token fields
    token_fields_match = re.search(r'name="_Token\[fields\]"[^>]*value="([^"]+)"', html_content)
    token_fields = token_fields_match.group(1) if token_fields_match else ""
    
    # Extract Token unlocked
    token_unlocked_match = re.search(r'name="_Token\[unlocked\]"[^>]*value="([^"]+)"', html_content)
    token_unlocked = token_unlocked_match.group(1) if token_unlocked_match else ""
    
    # Extract form action
    action_match = re.search(r'action="([^"]+)"', html_content)
    action = action_match.group(1) if action_match else ""
    
    return {
        "csrf_token": csrf_token,
        "ad_form_data": ad_form_data,
        "token_fields": token_fields,
        "token_unlocked": token_unlocked,
        "action": action
    }

def handle_lksfy(key_url, session, verify, debug):
    """
    Handler for lksfy.com URLs
    """
    info("Using lksfy handler...")
    
    # Extract the alias from the URL
    parsed = urlparse(key_url)
    alias = parsed.path.strip("/").split("/")[-1]
    info(f"Extracted alias: {alias}")
    
    # Make initial request
    dbg(f"Lksfy request 1 -> {key_url}", debug)
    try:
        # First get the redirect
        response = session.get(key_url, headers={"referer": key_url}, timeout=30, verify=verify, allow_redirects=False)
        dbg(f"Lksfy request 1 status: {response.status_code}", debug)
        
        if response.status_code in (301, 302, 303, 307, 308):
            redirect_url = response.headers.get('Location')
            dbg(f"Redirect URL: {redirect_url}", debug)
            
            # Now make the second request with referer
            headers = {"referer": redirect_url}
            dbg(f"Lksfy request 2 -> {key_url} with referer", debug)
            second_response = session.get(key_url, headers=headers, timeout=30, verify=verify)
            dbg(f"Lksfy request 2 status: {second_response.status_code}", debug)
            
            if second_response.status_code == 200:
                # Extract the base64 value from HTML
                base64_match = re.search(r'var base64 = \'([^\']+)\'', second_response.text)
                if base64_match:
                    base64_value = base64_match.group(1)
                    dbg(f"Found base64 value: {base64_value[:20]}...", debug)
                    
                    # Decrypt the base64 value
                    decrypted_html = decrypt(base64_value, alias, debug)
                    if decrypted_html:
                        dbg("Successfully decrypted HTML form data", debug)
                        
                        # Extract form data
                        form_data = extract_form_data(decrypted_html)
                        
                        # Prepare POST request
                        post_url = f"https://lksfy.com{form_data['action']}"
                        
                        post_headers = {
                            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                            "referer": "https://lksfy.com/",
                            "cookie": f"csrfToken={form_data['csrf_token']}",
                            "x-requested-with": "XMLHttpRequest"
                        }
                        
                        # Manually build the POST body with individually URL-encoded values
                        post_body = (
                            f"_method=POST"
                            f"&_csrfToken={quote(form_data['csrf_token'])}"
                            f"&ad_form_data={quote(form_data['ad_form_data'])}"
                            f"&_Token%5Bfields%5D={form_data['token_fields']}"
                            f"&_Token%5Bunlocked%5D={quote(form_data['token_unlocked'])}"
                        )
                        
                        dbg(f"POST body: {post_body[:100]}...", debug)
                        
                        # Wait to prevent rate limiting
                        info("Waiting for 5 seconds to prevent bad request error")
                        time.sleep(5)

                        dbg(f"Lksfy request 3 -> {post_url} (POST)", debug)
                        post_response = session.post(post_url, headers=post_headers, data=post_body, timeout=30, verify=verify)
                        dbg(f"Lksfy request 3 status: {post_response.status_code}", debug)
                        
                        if post_response.status_code == 200:
                            try:
                                json_response = post_response.json()
                                if json_response.get("status") == "success":
                                    encrypted_url = json_response.get("url")
                                    dbg(f"Got encrypted URL: {encrypted_url[:20]}...", debug)
                                    
                                    # Decrypt the URL
                                    decrypted_url = decrypt(encrypted_url, alias, debug)
                                    if decrypted_url:
                                        dbg(f"Final URL: {decrypted_url}", debug)
                                        
                                        # Extract the key
                                        key_match = re.search(r'key=([^&]+)', decrypted_url)
                                        if key_match:
                                            key = key_match.group(1)
                                            ok(f"Extracted key: {key}")
                                            return key, None, None
                                        else:
                                            return None, key_url, RuntimeError("Key not found in the URL")
                                    else:
                                        return None, key_url, RuntimeError("Failed to decrypt the URL")
                                else:
                                    return None, key_url, RuntimeError(f"Error in response: {json_response.get('message')}")
                            except Exception as e:
                                return None, key_url, RuntimeError(f"Error parsing JSON response: {e}")
                        else:
                            return None, key_url, RuntimeError(f"POST request failed with status code: {post_response.status_code}")
                    else:
                        return None, key_url, RuntimeError("Failed to decrypt the base64 value")
                else:
                    return None, key_url, RuntimeError("Base64 value not found in the HTML")
            else:
                return None, key_url, RuntimeError(f"Second GET request failed with status code: {second_response.status_code}")
        else:
            return None, key_url, RuntimeError(f"First request did not redirect as expected: {response.status_code}")
    except Exception as e:
        return None, key_url, RuntimeError(f"Lksfy handler failed: {e}")




def main():
    parser = argparse.ArgumentParser(description="Auto extract gt key (defaults to zoo0.pages.dev).")
    parser.add_argument("--ssl-bypass", action="store_true", help="Disable SSL verification (requests.verify=False).")
    parser.add_argument("--debug", action="store_true", help="Show debug/background traces.")
    args = parser.parse_args()

    # Determine target URL: env TARGET_URL or default
    target_url = os.environ.get("TARGET_URL", DEFAULT_TARGET)
    user_agent = DEFAULT_USER_AGENT
    debug = args.debug
    verify = not args.ssl_bypass

    if args.ssl_bypass:
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            dbg("Disabled InsecureRequestWarning", debug)
        except Exception:
            dbg("Could not import urllib3 to suppress warnings", debug)

    try:
        # Try default method first
        try:
            headers, resp = get_initial_response_headers(target_url, user_agent, verify, debug)
            
            for hn in HEADER_NAMES:
                val = None
                for k, v in headers.items():
                    if k.lower() == hn.lower():
                        val = v
                        break
                if val is not None:
                    val
                else:
                    err(f"{hn} not present in response headers")

            combined, missing = build_combined(headers, debug)
            if all(not ch for ch in combined):
                raise ValueError("Combined payload empty — server didn't return required headers.")

            xor_key_bytes = KEY.encode("utf-8")
            dbg(f"Using XOR key (len={len(xor_key_bytes)}): {KEY}", debug)
            decoded = decode_b64_xor(combined, xor_key_bytes, debug)
            dbg(f"Decoded payload preview: {decoded[:800]}", debug)

            baseurl = extract_baseurl(decoded, debug)
            ok(f"baseUrl: {baseurl}")

            # Modified to return the key_url if it fails
            key, failed_url, error = fetch_key_flow(baseurl, verify=verify, debug=debug, user_agent=user_agent)
            
            if key:
                ok(f"Final key: {key}")
            else:
                raise RuntimeError("Failed to get key")
            
        except Exception as e:
            err(f"All methods failed: {e}")
            if debug:
                raise
            sys.exit(2)

    except KeyboardInterrupt:
        err("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        err(str(e))
        if debug:
            raise
        sys.exit(2)

if __name__ == "__main__":
    main()
