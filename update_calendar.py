import requests
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Calendar config
calendar_timezone = "Europe/Berlin"
tz = pytz.timezone(calendar_timezone)

# Fetch full PGA Tour 2025 schedule
schedule_url = "https://statdata.pgatour.com/r/2025/schedule-v2.json"
schedule = requests.get(schedule_url).json()

# Generate placeholder rounds for all events
ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    f"X-WR-TIMEZONE:{calendar_timezone}"
]

# For simplicity we only simulate each round with placeholder times
for tournament in schedule.get("tournaments", []):
    try:
        name = tournament["name"]
        location = tournament["venue"]["longName"]
        start = tournament["startDate"][:10]
        end = tournament["endDate"][:10]
    except KeyError:
        continue

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    num_days = (end_date - start_date).days + 1

    for i in range(num_days):
        day = start_date + timedelta(days=i)
        start_dt = tz.localize(datetime.combine(day, datetime.strptime("08:00", "%H:%M").time()))
        end_dt = start_dt + timedelta(hours=10)

        ics.append("BEGIN:VEVENT")
        ics.append(f"UID:{name.replace(' ', '')}-R{i+1}@pga.com")
        ics.append(f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
        ics.append(f"DTSTART;TZID={calendar_timezone}:{start_dt.strftime('%Y%m%dT%H%M%S')}")
        ics.append(f"DTEND;TZID={calendar_timezone}:{end_dt.strftime('%Y%m%dT%H%M%S')}")
        ics.append(f"SUMMARY:{name} – Round {i+1} ⛳")
        ics.append(f"LOCATION:{location}")
        ics.append("DESCRIPTION:Auto-updating PGA Tour round with placeholder times")
        ics.append("END:VEVENT")

ics.append("END:VCALENDAR")

Path("pga_tour_2025.ics").write_text("\n".join(ics))