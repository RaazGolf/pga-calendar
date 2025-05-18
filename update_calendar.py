from datetime import datetime, timedelta
from pathlib import Path

events = [
    {"name": "The Masters", "start": "2025-04-10", "end": "2025-04-13", "location": "Augusta National GC"},
    {"name": "PGA Championship", "start": "2025-05-15", "end": "2025-05-18", "location": "Quail Hollow Club"},
    {"name": "U.S. Open", "start": "2025-06-12", "end": "2025-06-15", "location": "Oakmont Country Club"},
    {"name": "The Open Championship", "start": "2025-07-17", "end": "2025-07-20", "location": "Royal Troon"},
]

ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nCALSCALE:GREGORIAN\n"

for event in events:
    start_date = datetime.strptime(event["start"], "%Y-%m-%d")
    end_date = datetime.strptime(event["end"], "%Y-%m-%d")

    for i in range((end_date - start_date).days + 1):
        event_date = start_date + timedelta(days=i)
        start_dt = event_date.strftime("%Y%m%dT130000Z")
        end_dt = event_date.strftime("%Y%m%dT190000Z")
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
