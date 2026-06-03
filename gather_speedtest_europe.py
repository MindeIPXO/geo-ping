#!/usr/bin/env python3

import json
import re
import time
from typing import Any, Dict, List, Optional

import requests


API_URL = "https://www.speedtest.net/api/js/config-sdk"
SPEEDTEST_HOME_URL = "https://www.speedtest.net/"

OUTPUT_JSON = "europe-speedtest-servers.json"
OUTPUT_JS = "europe-speedtest-servers.js"

REQUEST_LIMIT = 100
REQUEST_DELAY_SECONDS = 0.5


EUROPE_COUNTRIES = [
    # "New York",
    # "Los Angeles",
    "United States",
    # "Houston",
    # "Miami",
    # "Seattle",
    # "San Francisco",
    # "Washington DC",
    # "Boston",
    # "Philadelphia",
    # "San Diego",
    # "San Jose",
    # "Austin",
    # "Columbus",
    # "Fort Worth",
    # "Charlotte",
    # "Indianapolis",
    # "Jacksonville",
    # "San Antonio",
    # "San Francisco",
    # "Seattle",
    # "Washington DC",
    # "Boston",
    # "Philadelphia",
    # "San Diego",
    # "San Jose",
    # "Austin",
    # "Columbus",
    # "Fort Worth",
    # "Charlotte",
    # "Indianapolis",
    # "Jacksonville",
    # "San Antonio",
    # "San Francisco",
    # "Seattle",
    # "Washington DC",
    # "Boston",
    # "Philadelphia",
    # "San Diego",
    # "San Jose",
    # "Austin",
    # "Columbus",
    # "Fort Worth",
    # "Charlotte",
    # "Indianapolis",
    # "Jacksonville",
    # "San Antonio",
    # "San Francisco",
    # "Seattle",
    # "Washington DC",
    # "Boston",
    # "Philadelphia",
    # "San Diego",
    # "San Jose",
    # "Austin",
    # "Columbus",
    # "Fort Worth",
    # "Albania",
    # "Andorra",
    # "Austria",
    # "Belarus",
    # "Belgium",
    # "Bosnia and Herzegovina",
    # "Bulgaria",
    # "Croatia",
    # "Cyprus",
    # "Czechia",
    # "Denmark",
    # "Estonia",
    # "Finland",
    # "France",
    # "Germany",
    # "Greece",
    # "Hungary",
    # "Iceland",
    # "Ireland",
    # "Italy",
    # "Kosovo",
    # "Latvia",
    # "Liechtenstein",
    # "Lithuania",
    # "Luxembourg",
    # "Malta",
    # "Moldova",
    # "Monaco",
    # "Montenegro",
    # "Netherlands",
    # "North Macedonia",
    # "Norway",
    # "Poland",
    # "Portugal",
    # "Romania",
    # "San Marino",
    # "Serbia",
    # "Slovakia",
    # "Slovenia",
    # "Spain",
    # "Sweden",
    # "Switzerland",
    # "Ukraine",
    # "United Kingdom",
    # "Vatican City",
]


def create_browser_session() -> requests.Session:
    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.speedtest.net/",
            "Origin": "https://www.speedtest.net",
            "Connection": "keep-alive",
            "DNT": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-CH-UA": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
        }
    )

    return session


def warm_up_session(session: requests.Session) -> None:
    """
    Opens the Speedtest homepage once so the session receives cookies,
    similar to what a normal browser would do before calling the API.
    """
    try:
        response = session.get(SPEEDTEST_HOME_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Warning: homepage warm-up failed: {exc}")


def slugify(value: Optional[str]) -> str:
    if not value:
        return ""

    value = value.lower().strip()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)

    return value.strip("-")


def escape_js_string(value: Any) -> str:
    """
    Escapes strings for simple JS object output.
    """
    text = str(value)
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    return text


def build_entry_id(server: Dict[str, Any]) -> str:
    country_code = server.get("cc") or server.get("country") or ""
    region = server.get("name") or ""
    sponsor = server.get("sponsor") or ""

    parts = [
        slugify(country_code),
        slugify(region),
        slugify(sponsor),
    ]

    return "-".join(part for part in parts if part)


def build_speedtest_url(server: Dict[str, Any]) -> str:
    """
    Prefer `host`, because it usually points to the production Ookla host.

    Example input:
      host: speedtest.fra.plusnet.de.prod.hosts.ooklaserver.net:8080

    Output:
      http://speedtest.fra.plusnet.de.prod.hosts.ooklaserver.net:8080/hello?nocache
    """
    host = server.get("host")

    if host:
        return f"http://{host}/hello?nocache"

    raw_url = server.get("url", "")

    if raw_url:
        return raw_url.replace("/speedtest/upload.php", "/hello?nocache")

    return ""


def normalize_server(server: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    required_fields = ["id", "country", "name", "lat", "lon"]

    for field in required_fields:
        if not server.get(field):
            return None

    return {
        "id": build_entry_id(server),
        "country": server["country"].strip(),
        "continent": "North America",
        "region": server["name"].strip(),
        "lat": float(server["lat"]),
        "lon": float(server["lon"]),
        "url": build_speedtest_url(server),
        "ookla_server_id": str(server["id"]),
        "sponsor": server.get("sponsor", "").strip(),
    }


def fetch_country_servers(
    session: requests.Session,
    country: str,
    limit: int = REQUEST_LIMIT,
) -> List[Dict[str, Any]]:
    params = {
        "engine": "js",
        "search": country,
        "https_functional": "true",
        "limit": limit,
    }

    response = session.get(
        API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    return data.get("servers", [])


def to_js_object(entry: Dict[str, Any], include_extra_fields: bool = False) -> str:
    fields = [
        f'id: "{escape_js_string(entry["id"])}"',
        f'country: "{escape_js_string(entry["country"])}"',
        f'continent: "{escape_js_string(entry["continent"])}"',
        f'region: "{escape_js_string(entry["region"])}"',
        f'lat: {entry["lat"]}',
        f'lon: {entry["lon"]}',
        f'url: "{escape_js_string(entry["url"])}"',
    ]

    if include_extra_fields:
        fields.extend(
            [
                f'ookla_server_id: "{escape_js_string(entry["ookla_server_id"])}"',
                f'sponsor: "{escape_js_string(entry["sponsor"])}"',
            ]
        )

    return "{ " + ", ".join(fields) + " }"


def write_json(entries: List[Dict[str, Any]], output_path: str) -> None:
    # Keep JSON clean and only include your requested fields.
    clean_entries = [
        {
            "id": entry["id"],
            "country": entry["country"],
            "continent": entry["continent"],
            "region": entry["region"],
            "lat": entry["lat"],
            "lon": entry["lon"],
            "url": entry["url"],
        }
        for entry in entries
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(clean_entries, f, indent=2, ensure_ascii=False)


def write_js(entries: List[Dict[str, Any]], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("[\n")

        for index, entry in enumerate(entries):
            comma = "," if index < len(entries) - 1 else ""
            f.write(f"  {to_js_object(entry)}{comma}\n")

        f.write("]\n")


def gather_europe_servers() -> List[Dict[str, Any]]:
    session = create_browser_session()
    warm_up_session(session)

    entries: List[Dict[str, Any]] = []
    seen_ookla_server_ids = set()
    seen_entry_ids = set()

    for country in EUROPE_COUNTRIES:
        print(f"Fetching {country}...", flush=True)

        try:
            servers = fetch_country_servers(session, country)
        except requests.RequestException as exc:
            print(f"  Failed to fetch {country}: {exc}", flush=True)
            continue
        except json.JSONDecodeError as exc:
            print(f"  Failed to parse JSON for {country}: {exc}", flush=True)
            continue

        added_for_country = 0

        for server in servers:
            ookla_server_id = str(server.get("id", "")).strip()

            if not ookla_server_id:
                continue

            if ookla_server_id in seen_ookla_server_ids:
                continue

            # The API can sometimes return loosely matched nearby results.
            # Keep only exact country matches.
            if server.get("country") != country:
                continue

            normalized = normalize_server(server)

            if not normalized:
                continue

            entry_id = normalized["id"]

            # If two servers produce the same slug, append the Ookla server ID.
            if entry_id in seen_entry_ids:
                normalized["id"] = f"{entry_id}-{ookla_server_id}"

            seen_ookla_server_ids.add(ookla_server_id)
            seen_entry_ids.add(normalized["id"])

            entries.append(normalized)
            added_for_country += 1

        print(f"  Added {added_for_country} servers", flush=True)

        time.sleep(REQUEST_DELAY_SECONDS)

    entries.sort(
        key=lambda entry: (
            entry["country"].lower(),
            entry["region"].lower(),
            entry["id"].lower(),
        )
    )

    return entries


def main() -> None:
    entries = gather_europe_servers()

    write_json(entries, OUTPUT_JSON)
    write_js(entries, OUTPUT_JS)

    print()
    print(f"Done. Wrote {len(entries)} servers.")
    print(f"- {OUTPUT_JSON}")
    print(f"- {OUTPUT_JS}")


if __name__ == "__main__":
    main()