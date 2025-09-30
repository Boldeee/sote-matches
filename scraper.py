import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def fetch_matches(team_id=957):
    url = f"https://www.brsz.hu/csapatok.php?csapat_id={team_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    matches = []
    rows = soup.find_all("tr")
    current_year = datetime.now().year

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        raw_date = cols[0].get_text(strip=True)  # "10/21, , 19"
        if not raw_date:
            continue

        # --- Parse date and time ---
        try:
            # Extract date (MM/DD) and time (HH, <sup>MM</sup>)
            date_part = raw_date.split(",")[0].strip()  # "10/21"
            time_hour = raw_date.split(",")[-1].strip()  # "19" (hour)
            sup = cols[0].find("sup")
            time_minute = sup.get_text(strip=True) if sup else "00"

            month, day = map(int, date_part.split("/"))
            hour = int(time_hour)
            minute = int(time_minute)

            start = datetime(current_year, month, day, hour, minute)
            end = start + timedelta(hours=1, minutes=30)  # assume 90 min game
        except Exception:
            continue

        # --- Extract teams and venue ---
        home_team = cols[1].get_text(strip=True)
        away_team = cols[3].get_text(strip=True)
        venue = cols[4].get_text(strip=True)

        matches.append({
            "start": start,
            "end": end,
            "home": home_team,
            "away": away_team,
            "venue": venue
        })

    return matches


def generate_ics(matches):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//brsz.hu scraper//EN"
    ]

    for match in matches:
        uid = f"{match['start'].strftime('%Y%m%dT%H%M%S')}@brsz.hu"
        dtstart = match["start"].strftime("%Y%m%dT%H%M%S")
        dtend = match["end"].strftime("%Y%m%dT%H%M%S")
        summary = f"{match['home']} vs {match['away']}"
        location = match["venue"]

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{summary}",
            f"LOCATION:{location}",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    return "\n".join(lines)


if __name__ == "__main__":
    matches = fetch_matches(957)
    ics_content = generate_ics(matches)
    with open("matches.ics", "w", encoding="utf-8") as f:
        f.write(ics_content)
    print("✅ matches.ics generated")
