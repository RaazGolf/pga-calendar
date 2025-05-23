import requests
import json
import os
from datetime import datetime, timedelta
from ics import Calendar, Event
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://statdata.pgatour.com/r/2025"
CALENDAR_FILE = "pga_tour_2025.ics"

def fetch_schedule_json():
    url = f"{BASE_URL}/schedule-v2.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def scrape_official_schedule():
    url = "https://www.pgatour.com/schedule"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for card in soup.select(".EventCard"):
        try:
            name = card.select_one(".EventCard-name").get_text(strip=True)
            location = card.select_one(".EventCard-courseName").get_text(strip=True)
            date_text = card.select_one(".EventCard-dates").get_text(strip=True)
            # Parse start and end date
            dates = date_text.replace(",", "").split("–")
            if len(dates) == 2:
                start_date = datetime.strptime(dates[0].strip() + " 2025", "%b %d %Y")
                end_date = datetime.strptime(dates[1].strip() + " 2025", "%b %d %Y")
            else:
                start_date = end_date = datetime.strptime(dates[0].strip() + " 2025", "%b %d %Y")
            events.append({
                "name": name,
                "location": location,
                "start_date": start_date,
                "end_date": end_date
            })
        except Exception:
            continue
    return events

def get_tee_times(permalink):
    try:
        url = f"https://statdata.pgatour.com/r/2025/{permalink}/tournament.json"
        response = requests.get(url)
        data = response.json()
        rounds = data.get("Rounds", [])
        tee_times = []
        for rnd in rounds:
            times = rnd.get("TeeTimes", [])
            if times:
                tee_times.extend(times)
        if tee_times:
            times = sorted(datetime.strptime(t["TeeTime"], "%H:%M") for t in tee_times)
            return times[0].time(), times[-1].time()
    except Exception:
        pass
    return datetime.strptime("08:00", "%H:%M").time(), datetime.strptime("18:00", "%H:%M").time()

def create_calendar(events):
    cal = Calendar()
    for event in events:
        for day_offset in range((event["end_date"] - event["start_date"]).days + 1):
            day = event["start_date"] + timedelta(days=day_offset)
            e = Event()
            e.name = event["name"]
            e.begin = datetime.combine(day, event["start_time"])
            e.end = datetime.combine(day, event["end_time"])
            e.location = event["location"]
            e.description = f"{event['name']} - {event['location']}"
            cal.events.add(e)
    return cal

def merge_events(api_events, scraped_events):
    events = []
    used_names = set()

    for tourney in api_events.get("Tournament", []):
        name = tourney["Name"]
        location = tourney["Venue"]
        permalink = tourney.get("Permalink")
        start_date = datetime.strptime(tourney["StartDate"], "%Y-%m-%d")
        end_date = datetime.strptime(tourney["EndDate"], "%Y-%m-%d")
        start_time, end_time = get_tee_times(permalink)
        events.append({
            "name": name,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "start_time": start_time,
            "end_time": end_time
        })
        used_names.add(name)

    for e in scraped_events:
        if e["name"] not in used_names:
            e["start_time"] = datetime.strptime("08:00", "%H:%M").time()
            e["end_time"] = datetime.strptime("18:00", "%H:%M").time()
            events.append(e)

    return events

def main():
    print("Fetching official PGA Tour schedule and verifying completeness...")
    api_schedule = fetch_schedule_json()
    scraped_schedule = scrape_official_schedule()
    all_events = merge_events(api_schedule, scraped_schedule)
    cal = create_calendar(all_events)

    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal)
    print(f"Calendar saved as {CALENDAR_FILE}")

if __name__ == "__main__":
    main()
