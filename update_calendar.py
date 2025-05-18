import requests
from datetime import datetime, timedelta
from pathlib import Path

# Fetch the official 2025 PGA Tour schedule
url = "https://statdata.pgatour.com/r/2025/schedule-v2.json"
response = requests.get(url)
schedule = response.json()

events = []

for tournament in schedule.get("tournaments", []):
    try:
        name = tournament["name"]
        location = tournament["venue"]["longName"]
        start = tournament["startDate"][:10]
        end = tournament["endDate"][:10]

        events.append({
            "name": name,
            "start": start,
            "end": end,
            "location": location
        })
    except KeyError:
        continue

# Build the ICS calendar content
ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nCALSCALE:GREGORIAN\n"

for event in events:
    start_date = datetime.strptime(event["start"], "%Y-%m-%d")
    end_date = datetime.strptime(event["end"], "%Y-%m-%d")
    
    for i in range((end_date - start_date).days + 1):
        round_date = start_date + timedelta(days=i)
        start_dt = round_date.strftime("%Y%m%dT130000Z")
        end_dt = round_date.strftime("%Y%m%dT190000Z")
        uid = f"{event['name'].replace(' ', '')}-Round{i+1}@pga.com"

        ics_content += (
            "BEGIN:VEVENT\n"
            f"UID:{uid}\n"
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n"
            f"DTSTART:{start_dt}\n"
            f"DTEND:{end_dt}\n"
            f"SUMMARY:{event['name']} – Round {i+1}\n"
            f"LOCATION:{event['location']}\n"
            "END:VEVENT\n"
        )

ics_content += "END:VCALENDAR\n"

Path("pga_tour_2025.ics").write_text(ics_content)
