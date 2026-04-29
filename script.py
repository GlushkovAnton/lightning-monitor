import os
import requests
import math
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ======================
# TELEGRAM (из Secrets)
# ======================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


# ======================
# LOCATION
# ======================
MY_LAT = 65.0121
MY_LON = 25.4651
RADIUS_KM = 50


# ======================
# DISTANCE
# ======================
def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)

    return 2 * R * math.asin(math.sqrt(a))


# ======================
# FMI API
# ======================
URL = (
    "https://opendata.fmi.fi/wfs"
    "?service=WFS"
    "&version=2.0.0"
    "&request=getFeature"
    "&storedquery_id=fmi::observations::lightning::simple"
)


def fetch():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    return r.text


# ======================
# PARSER
# ======================
def parse(xml):
    root = ET.fromstring(xml)

    ns = {
        "wfs": "http://www.opengis.net/wfs/2.0",
        "gml": "http://www.opengis.net/gml/3.2",
        "BsWfs": "http://xml.fmi.fi/schema/wfs/2.0"
    }

    events = []

    for m in root.findall(".//wfs:member", ns):
        try:
            pos = m.find(".//gml:pos", ns)
            time_el = m.find(".//BsWfs:Time", ns)

            if not pos or not time_el:
                continue

            lat, lon = map(float, pos.text.split())
            t = time_el.text

            events.append((lat, lon, t))
        except:
            continue

    return events


# ======================
# MAIN LOGIC (1 RUN)
# ======================
def main():
    xml = fetch()
    events = parse(xml)

    msg = f"⚡ FMI Lightning check\n\nНайдено: {len(events)}\n\n"

    nearest = None
    min_d = 999999

    for lat, lon, t in events:
        d = distance(MY_LAT, MY_LON, lat, lon)

        if d <= RADIUS_KM:
            msg += f"⚡ {lat:.3f}, {lon:.3f} | {t} | {d:.1f} km\n"

        if d < min_d:
            min_d = d
            nearest = (lat, lon, t, d)

    if nearest:
        msg += f"\n--- БЛИЖАЙШАЯ ---\n{nearest[0]:.3f}, {nearest[1]:.3f}\n{nearest[2]}\n{nearest[3]:.1f} km"

    send_message(msg)


if __name__ == "__main__":
    main()
