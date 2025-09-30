from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def fetch_matches(team_id=957):
    import re
    url = f"https://www.brsz.hu/csapatok.php?csapat_id={team_id}"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")

    matches = []
    rows = soup.find_all("tr")
    print(f"Found {len(rows)} rows in table.")
    current_year = datetime.now().year

    date_pattern = re.compile(r"^(0[1-9]|1[0-2]|[1-9])/([0-2][0-9]|3[01]|[1-9])")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue
        # Only process rows where the third <td> is a dash
        if cols[2].get_text(strip=True) != "-":
            continue

        # Extract date and time from first <td>
        date_time_html = str(cols[0])
        date_time_soup = BeautifulSoup(date_time_html, 'html.parser')
        date_time_text = date_time_soup.get_text().strip()

        date = date_time_text.split(',')[0].strip()
        sup = date_time_soup.find('sup')
        if sup and sup.previous_sibling:
            # previous_sibling may include extra chars, so extract only the last number before <sup>
            import re
            hour_match = re.search(r'(\d{1,2})\s*$', sup.previous_sibling)
            hour = hour_match.group(1) if hour_match else "??"
            minute = sup.get_text(strip=True)
        else:
            hour = "??"
            minute = "??"

        # Extract teams and venue
        home_team = cols[1].get_text(strip=True)
        away_team = cols[3].get_text(strip=True)
        venue = cols[4].get_text(strip=True)

        print(f"Date: {date}")
        print(f"Time: {hour}:{minute}")
        print(f"Home team: {home_team}")
        print(f"Away team: {away_team}")
        print(f"Venue: {venue}")

        # If you want to keep generating the .ics file, convert hour/minute to int and build datetime
        try:
            month, day = map(int, date.split("/"))
            hour_int = int(hour)
            minute_int = int(minute)
            if hour_int < 0 or hour_int > 23 or minute_int < 0 or minute_int > 59:
                continue
            start = datetime(current_year, month, day, hour_int, minute_int)
            end = start + timedelta(hours=1, minutes=30)
        except Exception:
            continue
        match_info = {
            "start": start,
            "end": end,
            "home": home_team,
            "away": away_team,
            "venue": venue
        }
        matches.append(match_info)

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
