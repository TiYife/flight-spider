import json
import re
import requests
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup


def get_token():
    response = requests.get("https://zh.flightaware.com/live/map")
    response.enconding = "utf-8"
    text = response.text
    soup = BeautifulSoup(text, "html.parser")
    # print(soup.prettify)

    pattern = re.compile(r"var mapGlobals = .*?", re.MULTILINE | re.DOTALL)
    script = soup.find("script", text=pattern)
    # print(script)

    if script:
        pattern = re.compile(r"\"VICINITY_TOKEN\":\"(((\d)|[a-z])*)\"", re.MULTILINE | re.DOTALL)
        match = pattern.search(script.text)
        if match:
            # print(match.group(1))
            return match.group(1)
    return None


def get_airports():
    response = requests.get("https://zh.flightaware.com/ajax/ignoreall/vicinity_airports.rvt")
    response.enconding = "utf-8"

    text = response.text
    airports_json = json.loads(text)

    text = json.dumps(airports_json, indent=4)
    airports_file = open("airports_ori.json", "w")
    airports_file.write(text)

    features = airports_json['features']
    airports = []
    geolocator = Nominatim(user_agent="baidu", timeout=5)
    for feature in features:
        icao = feature["properties"]["icao"]
        iata = feature["properties"]["iata"]
        coordinates = feature["geometry"]["coordinates"]
        # location = geolocator.reverse(str(coordinates[1])+ ","+str(coordinates[0])).address.rsplit(',')[0]
        airport = {"icao": icao, "iata": iata, "coordinates": coordinates, "location": ""}
        airports.append(airport)

    text = json.dumps(airports, indent=4)
    airports_file = open("airports.json", "w")
    airports_file.write(text)

    return airports


def get_flight():
    token = get_token()
    grids = [[-180, -90, -79.9643325805664, 29.019527435302734],
             [-180, 29.019527435302734, -90.90573370456696, 36.03515625],
             [-90.90573370456696, 29.019527435302734, -79.9643325805664, 36.03515625],
             [-180, 36.03515625, -99.11178454756737, 90],
             [-99.11178454756737, 36.03515625, -79.9643325805664, 41.22611045837402],
             [-99.11178454756737, 41.22611045837402, -79.9643325805664, 90],
             [-79.9643325805664, -90, 4.5703125, 18.194046020507812],
             [-79.9643325805664, 18.194046020507812, -75.42389754205942, 40.6494140625],
             [-75.42389754205942, 18.194046020507812, 4.5703125, 40.6494140625],
             [-79.9643325805664, 40.6494140625, -42.9804253578186, 90],
             [-42.9804253578186, 40.6494140625, 4.5703125, 51.27617597579956],
             [-42.9804253578186, 51.27617597579956, 4.5703125, 90],
             [4.5703125, -90, 106.8471908569336, 13.734283447265625],
             [4.5703125, 13.734283447265625, 77.08302117884159, 31.81640625],
             [77.08302117884159, 13.734283447265625, 106.8471908569336, 31.81640625],
             [106.8471908569336, -90, 180, 19.920272827148438],
             [106.8471908569336, 19.920272827148438, 114.84827935695648, 31.81640625],
             [114.84827935695648, 19.920272827148438, 180, 31.81640625],
             [4.5703125, 31.81640625, 31.981201171875, 45.68046569824219],
             [4.5703125, 45.68046569824219, 31.981201171875, 51.393530666828156],
             [4.5703125, 51.393530666828156, 31.981201171875, 90],
             [31.981201171875, 31.81640625, 64.36031341552734, 90],
             [64.36031341552734, 31.81640625, 116.57603615429252, 90],
             [116.57603615429252, 31.81640625, 180, 90]]

    flights = []
    i = 0
    num = 0
    for grid in grids:
        response = requests.get(
            "https://zh.flightaware.com/ajax/ignoreall/vicinity_aircraft.rvt?&minLon=" + str(
                grid[0]) + "&minLat=" + str(grid[1]) + "&maxLon=" + str(grid[2]) + "&maxLat=" + str(
                grid[3]) + "&token=" + token)
        response.enconding = "utf-8"

        text = response.text
        flight_json = json.loads(text)

        text = json.dumps(flight_json, indent=4)
        flight_file = open("flight_ori" + str(i) + ".json", "w")
        i = i + 1
        flight_file.write(text)

        features = flight_json['features']
        for feature in features:
            flight_id = feature["properties"]["flight_id"]
            coordinates = feature["geometry"]["coordinates"]
            direction = feature["properties"]["direction"]
            origin = feature["properties"]["origin"]["iata"]
            destination = feature["properties"]["destination"]["iata"]

            flight = {"flight_id": flight_id, "coordinates": coordinates, "direction": direction, "origin": origin,
                      "destination": destination}
            flights.append(flight)
            num += 1
        print(num)

    text = json.dumps(flights, indent=4)
    flights_file = open("flight.json", "w")
    flights_file.write(text)

    return flights


def get_airlines(fs):
    airlines = []
    directions = []
    counts = []
    index = -1
    for f in fs:
        origin = f["origin"]
        destination = f["destination"]
        direction = {"origin": origin, "destination": destination}
        if directions.count(direction) == 0:
            directions.append(direction)
            index = index + 1
            counts.append(1)
        else:
            counts[index] += 1

    for i in range(0, index):
        d = directions[i]
        airline = {"direction": d, "num": counts[i]}
        airlines.append(airline)

    text = json.dumps(airlines, indent=4)
    airlines_file = open("airlines.json", "w")
    airlines_file.write(text)


if __name__ == "__main__":
    get_airports()
    flights = get_flight()
    # get_airlines(flights)
