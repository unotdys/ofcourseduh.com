#!/usr/bin/env python3
"""Builds stores.json for the Downtown Palo Alto timeline map.
Edit STORES below, then run: python3 build_data.py
Geocodes addresses with OpenStreetMap Nominatim (cached in geocache.json).
approx=True means the open/close years are estimates and need checking."""
import json, os, time, urllib.parse, urllib.request

CUR = 2026  # "end": None means still open
STORES = [
  # name, address, start, end, category, approx, note
  ("Palo Alto Furniture Co.", "300 University Ave", 1900, 1923, "retail", True, "First big tenant of the corner building at University & Bryant, which opened in 1900."),
  ("J.C. Penney", "300 University Ave", 1924, 1972, "retail", True, "Penney's opened here in 1924 and was run for two decades by Merrill Vanderpool."),
  ("Walgreens (and Subway)", "300 University Ave", 1973, 2007, "retail", False, "Walgreens from 1973; the 1900 building burned in an arson fire in July 2007 and was demolished."),
  ("Varsity Theatre (original)", "263 University Ave", 1912, 1927, "entertainment", False, "Palo Alto's first Varsity, opened March 1912, showing stage shows and films."),
  ("Stanford Theatre", "221 University Ave", 1925, None, "entertainment", False, "Opened June 9, 1925. Restored by the Packard family (1987-89); still shows classic films."),
  ("Varsity Theatre", "456 University Ave", 1927, 1994, "entertainment", False, "Reid Brothers movie palace. Revival house and music venue in the 1970s."),
  ("Borders Books", "456 University Ave", 1995, 2011, "retail", True, "Bookstore in the converted Varsity Theatre; closed when Borders liquidated in 2011."),
  ("HanaHaus & Blue Bottle Coffee", "456 University Ave", 2015, 2024, "food", False, "Co-working cafe in the old Varsity; closure announced Sept 2024."),
  ("Liddicoat's Market", "340 University Ave", 1924, 1977, "food", True, "Grocery and lunch market; building dates to 1923-24."),
  ("Z Gallerie", "340 University Ave", 1980, 2010, "retail", True, "Home furnishings store in the old Liddicoat's building."),
  ("Apple Store (current)", "340 University Ave", 2012, None, "retail", False, "Opened Oct 27, 2012 as a prototype glass-front store."),
  ("Swain's Music", "451 University Ave", 1950, 2000, "retail", True, "Music store; locals say Jerry Garcia rented instruments here."),
  ("Apple Store (first)", "451 University Ave", 2001, 2012, "retail", False, "Opened Oct 2001, one of Apple's first stores and Steve Jobs's local store."),
  ("Shoe Palace", "451 University Ave", 2013, None, "retail", True, "Took over the original Apple Store space."),
  ("Chimaera Books & Music", "165 University Ave", 1980, 2000, "retail", True, "Ground-floor bookstore in the 'lucky building' until 2000."),
  ("Google (first office)", "165 University Ave", 1999, 1999, "tech", False, "Google's first real office, 1999, after Logitech. Later tenants: PayPal, Danger, Milo."),
  ("PayPal", "165 University Ave", 1999, 2000, "tech", True, "Early PayPal offices upstairs in the 'lucky building'."),
  ("Facebook (first office)", "471 Emerson St", 2004, 2005, "tech", True, "Facebook's first Palo Alto office."),
  ("Facebook", "156 University Ave", 2005, 2009, "tech", True, "Facebook's downtown HQ before moving to the Stanford Research Park."),
  ("Peninsula Creamery", "566 Emerson St", 1923, None, "food", False, "Diner and soda fountain since 1923."),
  ("Bell's Books", "536 Emerson St", 1935, None, "retail", False, "New and used bookstore, family-run since 1935."),
  ("University Art", "267 Hamilton Ave", 1964, 2017, "retail", True, "Art supply and framing store."),
  ("Palo Alto Sport Shop & Toy World", "526 Waverley St", 1930, 2015, "retail", True, "Sporting goods and toys from 1930."),
  ("Gotham Shop", "520 Ramona St", 1925, 1940, "retail", True, "First building of the Ramona Street architectural district (Pedro de Lemos, 1925)."),
  ("Cardinal Hotel", "235 Hamilton Ave", 1924, None, "hotel", True, "Palo Alto's first non-frame hotel."),
  ("Hotel President", "488 University Ave", 1929, None, "hotel", True, "1929 hotel, long used as apartments, now a hotel again."),
  ("Shady Lane", "441 University Ave", 1975, 2015, "retail", True, "Craft store, gallery and gift shop; moved to Menlo Park in 2015."),
  ("St. Michael's Alley", "436 University Ave", 1959, 1977, "food", True, "Early coffeehouse and folk venue; later moved."),
  ("Coupa Cafe", "538 Ramona St", 2004, None, "food", True, "Venezuelan cafe, a startup meeting spot."),
  ("Il Fornaio", "520 Cowper St", 1987, None, "food", True, "In the Garden Court Hotel."),
  ("Evvia Estiatorio", "420 Emerson St", 1995, None, "food", True, "Greek restaurant."),
  ("Pizza A Go-Go", "220 University Ave", 1988, 2007, "food", True, "Pizza by the slice, open late on weekends. Business records give 1988 as its start; it later moved to 335 University Ave."),
  ("Copeland's Sports", "375 University Ave", 1990, 2002, "retail", True, "Sporting goods store at University & Waverley, remembered open in the early 1990s. The Cheesecake Factory replaced it after a 2003 renovation."),
  ("The Cheesecake Factory", "375 University Ave", 2003, 2018, "food", False, "Opened in late 2003 in the former Copeland's building; closed May 26, 2018."),
  ("Roger's Deli", "Ramona St near University Ave", 1990, 1995, "food", True, "Deli on Ramona, around the corner from Peninsula Beauty Supply, remembered open in the early 1990s. Exact address and years unknown; pin placement approximate."),
  ("Palo Alto Post Office", "380 Hamilton Ave", 1932, None, "landmark", True, "Birge Clark's Spanish Colonial post office."),
  ("Palo Alto Depot", "95 University Ave", 1941, None, "landmark", True, "Streamline Moderne train station (Southern Pacific, now Caltrain)."),
]

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geocache.json")
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def geocode(addr):
    if addr in cache: return cache[addr]
    q = urllib.parse.urlencode({"q": f"{addr}, Palo Alto, CA 94301", "format": "json", "limit": 1})
    req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + q,
                                 headers={"User-Agent": "ofcourseduh-downtownpaloalto/1.0"})
    res = json.load(urllib.request.urlopen(req, timeout=20)); time.sleep(1.1)
    cache[addr] = [float(res[0]["lat"]), float(res[0]["lon"])] if res else None
    json.dump(cache, open(CACHE, "w"), indent=1)
    return cache[addr]

out, missing = [], []
for name, addr, s, e, cat, approx, note in STORES:
    ll = geocode(addr)
    if not ll: missing.append(addr); continue
    out.append({"name": name, "address": addr, "start": s, "end": e, "category": cat,
                "approx": approx, "note": note, "lat": ll[0], "lng": ll[1]})
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stores.json"), "w"), indent=1)
print(f"{len(out)} entries written; not geocoded: {missing}")
