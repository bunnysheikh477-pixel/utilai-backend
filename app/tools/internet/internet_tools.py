from typing import Any
from urllib.parse import (
    urlparse,
    urlencode,
    parse_qs,
    urlunparse,
    quote,
    unquote,
)
import socket
import ssl
import re

import requests
import dns.resolver


# =========================================================
# COMMON HELPERS
# =========================================================

def normalize_url(url: str) -> str:
    """Add https:// if the user didn't provide a scheme."""

    url = url.strip()

    if not url:
        raise ValueError("URL cannot be empty.")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def validate_url(url: str) -> bool:
    """Check whether a URL has a valid HTTP/HTTPS structure."""

    try:
        parsed = urlparse(normalize_url(url))

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )

    except Exception:
        return False


# =========================================================
# 1. URL ENCODER
# =========================================================

def url_encoder(text: str) -> dict[str, Any]:
    """Encode text for use inside a URL."""

    return {
        "success": True,
        "result": quote(text, safe="")
    }


# =========================================================
# 2. URL DECODER
# =========================================================

def url_decoder(text: str) -> dict[str, Any]:
    """Decode URL-encoded text."""

    return {
        "success": True,
        "result": unquote(text)
    }


# =========================================================
# 3. URL VALIDATOR
# =========================================================

def url_validator(url: str) -> dict[str, Any]:

    valid = validate_url(url)

    return {
        "success": True,
        "url": url,
        "valid": valid
    }


# =========================================================
# 4. URL PARSER
# =========================================================

def url_parser(url: str) -> dict[str, Any]:

    try:
        url = normalize_url(url)
        parsed = urlparse(url)

        return {
            "success": True,
            "scheme": parsed.scheme,
            "domain": parsed.netloc,
            "path": parsed.path,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "port": parsed.port,
            "username": parsed.username,
            "password": parsed.password,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 5. URL QUERY PARSER
# =========================================================

def query_parser(url: str) -> dict[str, Any]:

    try:
        parsed = urlparse(normalize_url(url))

        query = parse_qs(parsed.query)

        return {
            "success": True,
            "parameters": query
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 6. URL QUERY BUILDER
# =========================================================

def query_builder(
    base_url: str,
    parameters: dict[str, Any]
) -> dict[str, Any]:

    try:
        separator = "&" if "?" in base_url else "?"

        query = urlencode(
            parameters,
            doseq=True
        )

        return {
            "success": True,
            "url": base_url + separator + query
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 7. REDIRECT CHECKER
# =========================================================

def redirect_checker(url: str) -> dict[str, Any]:

    try:
        url = normalize_url(url)

        response = requests.get(
            url,
            allow_redirects=True,
            timeout=10
        )

        history = []

        for item in response.history:
            history.append({
                "url": item.url,
                "status_code": item.status_code,
                "location": item.headers.get("Location")
            })

        return {
            "success": True,
            "original_url": url,
            "final_url": response.url,
            "redirect_count": len(response.history),
            "redirects": history,
            "status_code": response.status_code
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 8. HTTP STATUS CHECKER
# =========================================================

def http_status_checker(url: str) -> dict[str, Any]:

    try:
        url = normalize_url(url)

        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True
        )

        return {
            "success": True,
            "url": response.url,
            "status_code": response.status_code,
            "status": response.reason
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 9. HTTP HEADERS CHECKER
# =========================================================

def http_header_checker(url: str) -> dict[str, Any]:

    try:
        url = normalize_url(url)

        response = requests.get(
            url,
            timeout=10
        )

        return {
            "success": True,
            "url": response.url,
            "headers": dict(response.headers)
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 10. WEBSITE RESPONSE TIME
# =========================================================

def website_response_time(url: str) -> dict[str, Any]:

    import time

    try:
        url = normalize_url(url)

        start = time.perf_counter()

        response = requests.get(
            url,
            timeout=15
        )

        end = time.perf_counter()

        response_time_ms = round(
            (end - start) * 1000,
            2
        )

        return {
            "success": True,
            "url": url,
            "status_code": response.status_code,
            "response_time_ms": response_time_ms
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 11. WEBSITE METADATA
# =========================================================

def website_metadata(url: str) -> dict[str, Any]:

    try:
        url = normalize_url(url)

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        html = response.text

        title_match = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            re.IGNORECASE | re.DOTALL
        )

        description_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
            html,
            re.IGNORECASE | re.DOTALL
        )

        title = (
            title_match.group(1).strip()
            if title_match
            else None
        )

        description = (
            description_match.group(1).strip()
            if description_match
            else None
        )

        return {
            "success": True,
            "url": response.url,
            "title": title,
            "description": description,
            "status_code": response.status_code
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 12. WEBSITE TEXT EXTRACTOR
# =========================================================

def website_text_extractor(url: str) -> dict[str, Any]:

    try:
        url = normalize_url(url)

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        html = response.text

        # Remove scripts and styles
        html = re.sub(
            r"<script.*?</script>",
            "",
            html,
            flags=re.IGNORECASE | re.DOTALL
        )

        html = re.sub(
            r"<style.*?</style>",
            "",
            html,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Remove HTML tags
        text = re.sub(
            r"<[^>]+>",
            " ",
            html
        )

        # Clean whitespace
        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        return {
            "success": True,
            "url": response.url,
            "text": text
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 13. DNS LOOKUP
# =========================================================

def dns_lookup(
    domain: str,
    record_type: str = "A"
) -> dict[str, Any]:

    try:

        domain = domain.strip()

        answers = dns.resolver.resolve(
            domain,
            record_type
        )

        records = [
            answer.to_text()
            for answer in answers
        ]

        return {
            "success": True,
            "domain": domain,
            "record_type": record_type,
            "records": records
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 14. A RECORD LOOKUP
# =========================================================

def a_record_lookup(domain: str):

    return dns_lookup(
        domain,
        "A"
    )


# =========================================================
# 15. AAAA RECORD LOOKUP
# =========================================================

def aaaa_record_lookup(domain: str):

    return dns_lookup(
        domain,
        "AAAA"
    )


# =========================================================
# 16. MX RECORD LOOKUP
# =========================================================

def mx_record_lookup(domain: str):

    return dns_lookup(
        domain,
        "MX"
    )


# =========================================================
# 17. TXT RECORD LOOKUP
# =========================================================

def txt_record_lookup(domain: str):

    return dns_lookup(
        domain,
        "TXT"
    )


# =========================================================
# 18. NS RECORD LOOKUP
# =========================================================

def ns_record_lookup(domain: str):

    return dns_lookup(
        domain,
        "NS"
    )


# =========================================================
# 19. CNAME RECORD LOOKUP
# =========================================================

def cname_record_lookup(domain: str):

    return dns_lookup(
        domain,
        "CNAME"
    )


# =========================================================
# 20. IP ADDRESS LOOKUP
# =========================================================

def ip_lookup(domain: str):

    try:

        domain = domain.strip()

        ip_address = socket.gethostbyname(
            domain
        )

        return {
            "success": True,
            "domain": domain,
            "ip_address": ip_address
        }

    except socket.gaierror as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 21. REVERSE DNS LOOKUP
# =========================================================

def reverse_dns_lookup(ip: str):

    try:

        hostname = socket.gethostbyaddr(ip)

        return {
            "success": True,
            "ip": ip,
            "hostname": hostname[0],
            "aliases": hostname[1]
        }

    except socket.herror as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 22. PING / CONNECTIVITY CHECK
# =========================================================

def ping_check(domain: str):

    try:

        domain = domain.replace(
            "https://", ""
        ).replace(
            "http://", ""
        ).split("/")[0]

        socket.create_connection(
            (domain, 80),
            timeout=5
        )

        return {
            "success": True,
            "domain": domain,
            "reachable": True
        }

    except Exception as e:

        return {
            "success": True,
            "domain": domain,
            "reachable": False,
            "message": str(e)
        }


# =========================================================
# 23. SSL CERTIFICATE CHECKER
# =========================================================

def ssl_checker(domain: str):

    try:

        domain = domain.replace(
            "https://", ""
        ).replace(
            "http://", ""
        ).split("/")[0]

        context = ssl.create_default_context()

        with socket.create_connection(
            (domain, 443),
            timeout=10
        ) as sock:

            with context.wrap_socket(
                sock,
                server_hostname=domain
            ) as secure_socket:

                certificate = secure_socket.getpeercert()

        return {
            "success": True,
            "domain": domain,
            "subject": certificate.get(
                "subject"
            ),
            "issuer": certificate.get(
                "issuer"
            ),
            "version": certificate.get(
                "version"
            ),
            "serial_number": certificate.get(
                "serialNumber"
            ),
            "valid_from": certificate.get(
                "notBefore"
            ),
            "valid_until": certificate.get(
                "notAfter"
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 24. ROBOTS.TXT CHECKER
# =========================================================

def robots_txt_checker(url: str):

    try:

        url = normalize_url(url)

        parsed = urlparse(url)

        robots_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            "/robots.txt",
            "",
            "",
            ""
        ))

        response = requests.get(
            robots_url,
            timeout=10
        )

        return {
            "success": True,
            "url": robots_url,
            "status_code": response.status_code,
            "exists": response.status_code == 200,
            "content": response.text
        }

    except requests.RequestException as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 25. SITEMAP CHECKER
# =========================================================

def sitemap_checker(url: str):

    try:

        url = normalize_url(url)

        parsed = urlparse(url)

        sitemap_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            "/sitemap.xml",
            "",
            "",
            ""
        ))

        response = requests.get(
            sitemap_url,
            timeout=10
        )

        return {
            "success": True,
            "url": sitemap_url,
            "status_code": response.status_code,
            "exists": response.status_code == 200,
            "content": response.text
        }

    except requests.RequestException as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 26. LINK EXTRACTOR
# =========================================================

def link_extractor(url: str):

    try:

        url = normalize_url(url)

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        links = re.findall(
            r'href=["\'](.*?)["\']',
            response.text,
            re.IGNORECASE
        )

        return {
            "success": True,
            "url": url,
            "count": len(links),
            "links": links
        }

    except requests.RequestException as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# 27. EMAIL EXTRACTOR
# =========================================================

def email_extractor(text: str):

    pattern = r'[\w\.-]+@[\w\.-]+\.\w+'

    emails = list(
        set(re.findall(pattern, text))
    )

    return {
        "success": True,
        "count": len(emails),
        "emails": emails
    }


# =========================================================
# 28. WEBSITE WORD COUNTER
# =========================================================

def website_word_counter(url: str):

    result = website_text_extractor(url)

    if not result["success"]:
        return result

    text = result["text"]

    words = text.split()

    return {
        "success": True,
        "url": url,
        "words": len(words),
        "characters": len(text)
    }


# =========================================================
# 29. USER AGENT PARSER
# =========================================================

def user_agent_parser(user_agent: str):

    browser = "Unknown"
    operating_system = "Unknown"

    if "Chrome" in user_agent:
        browser = "Chrome"

    elif "Firefox" in user_agent:
        browser = "Firefox"

    elif "Safari" in user_agent:
        browser = "Safari"

    elif "Edge" in user_agent:
        browser = "Edge"

    if "Windows" in user_agent:
        operating_system = "Windows"

    elif "Mac OS" in user_agent:
        operating_system = "macOS"

    elif "Linux" in user_agent:
        operating_system = "Linux"

    elif "Android" in user_agent:
        operating_system = "Android"

    elif "iPhone" in user_agent:
        operating_system = "iOS"

    return {
        "success": True,
        "browser": browser,
        "operating_system": operating_system,
        "user_agent": user_agent
    }


# =========================================================
# 30. DOMAIN TO IP
# =========================================================

def domain_to_ip(domain: str):

    return ip_lookup(domain)