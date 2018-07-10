#!/usr/bin/env pythonA

import googlemaps
import json
import time
import traceback
import math
from math import radians, cos, sin, asin, sqrt, fabs
from random import uniform as urand

GMAPS = None

def init(api_key):
    global GMAPS
    GMAPS = googlemaps.Client(key=api_key)

def bearing(lat1, lon1, lat2, lon2):
    startLat = math.radians(lat1)
    startLong = math.radians(lon1)
    endLat = math.radians(lat2)
    endLong = math.radians(lon2)

    dLong = endLong - startLong

    dPhi = math.log(math.tan(endLat/2.0+math.pi/4.0)/math.tan(startLat/2.0+math.pi/4.0))
    if abs(dLong) > math.pi:
        if dLong > 0.0:
            dLong = -(2.0 * math.pi - dLong)
        else:
            dLong = (2.0 * math.pi + dLong)

    bearing = (math.degrees(math.atan2(dLong, dPhi)) + 360.0) % 360.0;

    return bearing

def haversine(lat1, lon1, lat2, lon2):
    # https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def points_along_line(num_points, lat1, lon1, lat2, lon2):
    if num_points <= 0:
        return []
    if num_points == 1:
        return [(((lat1+lat2)/2),((lon1+lon2)/2))]
    if num_points == 2:
        return [(lat1,lon1), (lat2,lon2)]
    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1
    points = [(lat1 + i * (lat_diff/(num_points-1)), (lon1 + i * (lon_diff/(num_points-1)))) for i in range(0, num_points)]
    return points

def bounds(lat, lon, radius_km=1):
    # Yeah, this generates a rectangle, not a circle.  I'm lazy.
    nelat = lat * 1.001
    nelon = lon * 1.001
    swlat = lat * .999
    swlon = lon * .999
    nedistance = haversine(lat, lon, nelat, nelon)
    while fabs(1 - nedistance / radius_km) > .1:
        if nedistance > radius_km:
            nelat = nelat - (nelat - lat) / 2
            nelon = nelon - (nelon - lon) / 2
        else:
            nelat = nelat + (nelat - lat) / 10
            nelon = nelon + (nelon - lon) / 10
        nedistance = haversine(lat, lon, nelat, nelon)

    swdistance = haversine(lat, lon, swlat, swlon)
    while fabs(1 - swdistance / radius_km) > .1:
        if swdistance > radius_km:
            swlat = swlat - (swlat - lat) / 2
            swlon = swlon - (swlon - lon) / 2
        else:
            swlat = swlat + (swlat - lat) / 10
            swlon = swlon + (swlon - lon) / 10
        swdistance = haversine(lat, lon, swlat, swlon)
    return (nelat,nelon), (swlat,swlon)

def get_random_house(bundle, radius_km = 1):
    lat = bundle["lat"]
    lon = bundle["lon"]
    ne_pt, sw_pt = bounds(lat, lon, radius_km)
    lat_range = (min(ne_pt[0], sw_pt[0]), max(ne_pt[0], sw_pt[0]))
    lon_range = (min(ne_pt[1], sw_pt[1]), max(ne_pt[1], sw_pt[1]))
    new_lat = urand(*lat_range)
    new_lon = urand(*lon_range)
    result = GMAPS.reverse_geocode((new_lat, new_lon))[0]
    addr_gps = coordinates_from_result(result)
    address_point_distance = haversine(new_lat, new_lon, addr_gps[0], addr_gps[1])
    if result["geometry"]["location_type"] == "ROOFTOP" and address_point_distance < .05:
        # Isn't obviously not a house or other dwelling.
        rbundle = bundle_result(result)
        business_info = business_summary(rbundle["address"])
        if business_info:
            # Likely a business.  Small chance it's a business run out of a home, but it's tough to avoid that without a zoning API.
            return get_random_house(bundle, radius_km)
        else:
            return rbundle
    else:
        time.sleep(0.5)
        return get_random_house(bundle, radius_km)

def bundle_result(result):
    return {"address":result.get("formatted_address", "<unknown>").split(",")[0], "lat":result["geometry"]["location"]["lat"], "lon":result["geometry"]["location"]["lng"], "full_address":result.get("formatted_address","<unknown>")}

def bundle_address(address):
    return bundle_result(GMAPS.geocode(address)[0])

def coordinates_from_result(result):
    gps = result["geometry"]["location"]
    return (gps["lat"], gps["lng"])

def address_parts_from_result(result, short=False):
    return {"/".join(c["types"]):c["short_name" if short else "long_name"] for c in result.get("address_components",[])}

def canonical_address(result):
    if "vicinity" in result:
        return result["vicinity"]
    addr_parts = address_parts_from_result(result)
    if addr_parts:
        addr = ""
        if "street_number" in addr_parts:
            addr += addr_parts["street_number"] + " "
        if "route" in addr_parts:
            addr += addr_parts["route"] + ", "
        if "locality/political" in addr_parts:
            addr += addr_parts["locality/political"]
        return addr
    return None

def coordinates_at_address(address):
    geocode_result = GMAPS.geocode(address)[0]
    latlon = coordinates_from_result(geocode_result)
    return latlon

def place_at_address(address):
    # print("Looking up address: {}".format(address))
    geocode_result = GMAPS.geocode(address)[0]
    latlon = coordinates_from_result(geocode_result)
    canonical_addr = canonical_address(geocode_result)
    # print("Canonical address: {}".format(canonical_addr))
    places_result = GMAPS.places_nearby(location=latlon, radius=50)["results"]
    print(json.dumps(places_result, indent=2, sort_keys=True))
    for place in places_result:
        place_addr = canonical_address(place)
        # print("Comparing to address {}".format(place_addr))
        if place_addr == canonical_addr:
            return place

def business_summary(address):
    place = place_at_address(address)
    if place:
        try:
            return "Name: {}, Type: {}".format(place.get("name","<name unknown>"), ", ".join(place.get("types", ["unknown"])))
        except:
            traceback.print_exc()
            return "UNKNOWN"
    return None
