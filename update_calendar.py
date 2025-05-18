import requests
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import time

calendar_timezone = "Europe/Berlin"
tz = pytz.timezone(calendar_timezone)

def fetch_with_retries(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"HTTP Error {response.status_code} on attempt {attempt+1}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1} failed: {e}")
        time.sleep(delay)
    raise ConnectionError(f"Failed to fetch URL after {retries} attempts: {url}")

# Fetch full PGA Tour 2025 schedule with retries
schedule_url = "https://statdata.pgatour.com/r/2025/schedule-v2.json"
schedule = fetch_with_retries(schedule_url)

# Prepare calendar structure
ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    f"X-WR-TIMEZONE:{calendar_timezone}"
]

# Helper function to get real tee times with retries
def get_real_tee_window(event_id):
    try:
        event_data = fetch_with_retries(f"https://statdata.pgatour.com/r/{event_id}/tournament.json")
        rounds = event_data.get("rounds", [])
        tee_times = []

        for rnd in rounds:
            for group in rnd.get("groups", []):
                t_str = group.get("teeTime")
                if t_str:
                    dt = datetime.strptime(t_str, "%Y-%m-%dT%H:%M:%SZ")
                    tee_times.append(dt)

        if tee_times:
            tee_times.sort()
            start = tee_times[0]
            end = tee_times[-1] + timedelta(hours=5)
            return start, end
    except:
        return None, None
    return None, None

# Loop through tournaments
for tournament in schedule.get("tournaments", []):
    try:
        event_id = tournament["permalink"]
        name = tournament["name"]
        location = tournament["venue"]["longName"]
        start = tournament["startDate"][:10]
        end = tournament["endDate"][:10]
    except KeyError:
        continue

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    num_days = (end_date - start_date).days + 1

    # Try to get real tee times
    real_start, real_end = get_real_tee_window(event_id)

    for i in range(num_days):
        day = start_date + timedelta(days=i)
        if real_start and real_start.date() == day.date():
            local_start = real_start.astimezone(tz)
            local_end = real_end.astimezone(tz)
        else:
            local_start = tz.localize(datetime.combine(day, datetime.strptime("08:00", "%H:%M").time()))
            local_end = local_start + timedelta(hours=10)

        ics.append("BEGIN:VEVENT")
        ics.append(f"UID:{name.replace(' ', '')}-R{i+1}@pga.com")
        ics.append(f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
        ics.append(f"DTSTART;TZID={calendar_timezone}:{local_start.strftime('%Y%m%dT%H%M%S')}")
        ics.append(f"DTEND;TZID={calendar_timezone}:{local_end.strftime('%Y%m%dT%H%M%S')}")
        ics.append(f"SUMMARY:{name} – Round {i+1} ⛳")
        ics.append(f"LOCATION:{location}")
        ics.append("DESCRIPTION:Live or placeholder round times")
        ics.append("END:VEVENT")

ics.append("END:VCALENDAR")

Path("pga_tour_2025.ics").write_text("\n".join(ics))