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
        soup = BeautifulSoup(date_time_html, 'html.parser')
        date_time_text = soup.get_text().strip()
        # Date is before first comma
        date_part = date_time_text.split(',')[0].strip()
        # Time: hour is the last number before <sup>, minute is <sup> or '00'
        sup = soup.find('sup')
        if sup and sup.previous_sibling:
            hour_text = sup.previous_sibling.strip()
            minute_text = sup.get_text(strip=True)
        else:
            # If no <sup>, try to get last number after last comma
            time_candidates = [p.strip() for p in date_time_text.split(',') if p.strip() and '/' not in p]
            time_str = time_candidates[-1] if time_candidates else ''
            if len(time_str) == 4 and time_str.isdigit():
                hour_text = time_str[:2]
                minute_text = time_str[2:]
            elif len(time_str) == 2 and time_str.isdigit():
                hour_text = time_str
                minute_text = '00'
            else:
                continue
        # Validate date and time
        if not date_part or not hour_text.isdigit() or not minute_text.isdigit():
            continue
        try:
            month, day = map(int, date_part.split("/"))
            hour = int(hour_text)
            minute = int(minute_text)
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                continue
            start = datetime(current_year, month, day, hour, minute)
            end = start + timedelta(hours=1, minutes=30)
        except Exception:
            continue

        # Extract teams and venue
        home_team = cols[1].get_text(strip=True)
        away_team = cols[3].get_text(strip=True)
        venue = cols[4].get_text(strip=True)

        print(f"Extracted: date={date_part}, time={hour:02d}:{minute:02d}, home='{home_team}', away='{away_team}', venue='{venue}'")
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
