"""Build seminars.json, archive.json and jams.ics for the Oxford SIAM Student Chapter website.

Scrapes the Junior Applied Mathematics Seminar (series 650) listings on the
Mathematical Institute website and merges in the slides listed in slides.json.
"""
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = "https://www.maths.ox.ac.uk"
UPCOMING_URL = f"{BASE}/events/list/650"
PAST_URL = f"{BASE}/events/past/650"
LONDON = ZoneInfo("Europe/London")
ROOT = Path(__file__).resolve().parent.parent


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "siamsc-jams-feed/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def text(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def field(block, name):
    m = re.search(rf'field--name-field-{name}[^>]*>(.*?)</div>', block, re.S)
    return text(m.group(1)) if m else ""


def parse(page):
    events = []
    for block in page.split('<article class="event">')[1:]:
        block = block.split("</article>")[0]
        link = re.search(r'<h3><a href="([^"]+)"[^>]*>(.*?)</a></h3>', block, re.S)
        date = re.search(r"\w{3}, (\d{2} \w{3} \d{4})", block)
        if not (link and date):
            continue
        times = re.findall(r"\b(\d{1,2}:\d{2})\b", block.split("field-location")[0])
        day = datetime.strptime(date.group(1), "%d %b %Y")

        def at(hhmm):
            h, m = map(int, hhmm.split(":"))
            local = day.replace(hour=h, minute=m, tzinfo=LONDON)
            return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        start = at(times[0]) if times else at("12:30")
        end = at(times[1]) if len(times) > 1 else None
        href = link.group(1)
        events.append({
            "id": href.rstrip("/").split("/")[-1],
            "title": text(link.group(2)),
            "url": href if href.startswith("http") else BASE + href,
            "speaker": field(block, "speaker"),
            "affiliation": field(block, "university").strip("() "),
            "room": field(block, "location"),
            "start": start,
            "end": end,
        })
    return events


def fetch_past():
    """All past talks, following the department's pagination (?page=0, 1, ...)."""
    events = []
    for page in range(30):
        found = parse(fetch(f"{PAST_URL}?page={page}"))
        if not found:
            break
        events += found
    return events


def write_json(path, data):
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def main():
    upcoming = parse(fetch(UPCOMING_URL))
    past = fetch_past()
    if not upcoming and not past:
        sys.exit("No events parsed: the department page layout may have changed.")

    # Manual corrections (e.g. a room change not yet on the department site) win.
    overrides_path = ROOT / "overrides.json"
    overrides = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path.exists() else []
    fixes = {str(o["id"]): {k: v for k, v in o.items() if k not in ("id", "note")} for o in overrides}
    for e in upcoming + past:
        e.update(fixes.get(e["id"], {}))

    # Keep every talk we have ever seen, even if the department later drops it.
    archive_path = ROOT / "archive.json"
    known = {}
    if archive_path.exists():
        known = {e["id"]: e for e in json.loads(archive_path.read_text(encoding="utf-8"))["seminars"]}
    upcoming_ids = {e["id"] for e in upcoming}
    known = {i: e for i, e in known.items() if i not in upcoming_ids}
    known.update({e["id"]: e for e in past})
    past = sorted(known.values(), key=lambda e: e["start"], reverse=True)

    slides = json.loads((ROOT / "slides.json").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in past + upcoming}
    talks_with_slides = []
    for s in slides:
        event = dict(by_id.get(str(s.get("id")), {}))
        event.update({k: v for k, v in s.items() if v})
        if event.get("title"):
            talks_with_slides.append(event)
    for e in past + upcoming:
        e.pop("slides", None)
        match = next((s for s in slides if str(s.get("id")) == e["id"]), None)
        if match:
            e["slides"] = match["slides"]

    talks_with_slides.sort(key=lambda e: e.get("start", ""), reverse=True)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {
        "source": UPCOMING_URL,
        "updated": updated,
        "upcoming": sorted(upcoming, key=lambda e: e["start"]),
        "past": past[:12],
        "slides": talks_with_slides,
    }
    write_json(ROOT / "seminars.json", out)
    write_json(archive_path, {"source": PAST_URL, "updated": updated, "seminars": past})
    calendar = sorted(out["upcoming"] + out["past"], key=lambda e: e["start"])
    (ROOT / "jams.ics").write_bytes(ics(calendar).encode("utf-8"))
    print(f"{len(out['upcoming'])} upcoming, {len(past)} past, {len(talks_with_slides)} with slides")


def ics_escape(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """Fold a content line at 75 octets, as RFC 5545 requires."""
    data, parts = line.encode("utf-8"), []
    while len(data) > 75:
        cut = 75 if not parts else 74
        while (data[cut] & 0xC0) == 0x80:  # don't split a UTF-8 character
            cut -= 1
        parts.append(data[:cut].decode("utf-8"))
        data = data[cut:]
    parts.append(data.decode("utf-8"))
    return "\r\n ".join(parts)


def ics(events):
    def stamp(iso):
        return iso.replace("-", "").replace(":", "")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Oxford SIAM Student Chapter//JAMS//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:JAMS – Junior Applied Mathematics Seminar",
        "X-WR-CALDESC:Junior Applied Mathematics Seminar\\, Mathematical Institute\\, University of Oxford",
        "X-WR-TIMEZONE:Europe/London",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]
    for e in events:
        start = stamp(e["start"])
        end = stamp(e["end"]) if e.get("end") else None
        who = e["speaker"] + (f" ({e['affiliation']})" if e.get("affiliation") else "")
        lines += [
            "BEGIN:VEVENT",
            f"UID:jams-{e['id']}@siamsc.maths.ox.ac.uk",
            f"DTSTAMP:{start}",  # deterministic, so unchanged events don't create commits
            f"DTSTART:{start}",
            f"DTEND:{end}" if end else "DURATION:PT30M",
            "SUMMARY:" + ics_escape(f"JAMS: {e['title']} – {e['speaker']}"),
            "DESCRIPTION:" + ics_escape(f"Speaker: {who}\nDetails: {e['url']}"
                                        + (f"\nSlides: {e['slides']}" if e.get("slides") else "")),
            "LOCATION:" + ics_escape(f"{e['room']}, Mathematical Institute, University of Oxford" if e.get("room")
                                     else "Mathematical Institute, University of Oxford"),
            f"URL:{e['url']}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


if __name__ == "__main__":
    main()
