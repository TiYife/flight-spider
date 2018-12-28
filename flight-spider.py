import json
import os
import re
import datetime
import time

import requests
import codecs

import schedule as schedule
from bs4 import BeautifulSoup

flights = []
airports = []
statistics= []


def get_token():
    print("get token...")
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
    print("get airports...")
    response = requests.get("https://zh.flightaware.com/ajax/ignoreall/vicinity_airports.rvt")
    response.enconding = "utf-8"

    web_text = response.text
    airports_json = json.loads(web_text)

    airports_text = json.dumps(airports_json, indent=4)
    airports_file = open("ori-data/airports_ori.json", "w")
    airports_file.write(airports_text)
    airports_file.close()

    iata_text = open("ref-data/airports-info.json", encoding="utf-8-sig")
    iata_json = json.load(iata_text)
    iata_text.close()

    country_json = json.load(codecs.open('ref-data/country_code.json', 'r', 'utf-8-sig'))
    airports.clear()
    features = airports_json['features']

    for feature in features:
        iata = feature["properties"]["iata"]
        icao = feature["properties"]["icao"]
        for detail in iata_json:
            if icao == detail["icao"] or iata == detail["iata"]:
                coordinates = feature["geometry"]["coordinates"]
                name = detail["name"]
                city = detail["city"]
                state = detail["state"]
                country = detail["country"]
                for code in country_json:
                    if country == code["code"]:
                        country = [code["en"], code["cn"]]
                        airport = {"iata": iata, "icao": icao, "coordinates": coordinates,
                                   "name": name, "city": city, "state": state, "country": country}
                        airports.append(airport)

    text = json.dumps(airports, indent=4, ensure_ascii=False)
    airports_file = open("airports.json", "w", encoding="utf-8")
    airports_file.write(text)
    airports_file.close()
    return airports


def get_flight():
    print("get flight...")
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

    i = 0
    num = 0
    flights.clear()
    for grid in grids:
        response = requests.get(
            "https://zh.flightaware.com/ajax/ignoreall/vicinity_aircraft.rvt?&minLon=" + str(
                grid[0]) + "&minLat=" + str(grid[1]) + "&maxLon=" + str(grid[2]) + "&maxLat=" + str(
                grid[3]) + "&token=" + token)
        response.enconding = "utf-8"

        text = response.text
        flight_json = json.loads(text)

        # text = json.dumps(flight_json, indent=4)
        # flight_file = open("flight_ori" + str(i) + ".json", "w")
        # i = i + 1
        # flight_file.write(text)

        features = flight_json['features']
        for feature in features:
            flight_id = feature["properties"]["flight_id"]
            coordinates = feature["geometry"]["coordinates"]
            direction = feature["properties"]["direction"]
            origin = {"iata": feature["properties"]["origin"]["iata"], "icao": feature["properties"]["origin"]["icao"]}
            destination = {"iata": feature["properties"]["destination"]["iata"],
                           "icao": feature["properties"]["destination"]["icao"]}

            flight = {"flight_id": flight_id, "coordinates": coordinates, "direction": direction,
                      "origin": origin, "destination": destination}
            flights.append(flight)
            num += 1
        print(num)

    text = json.dumps(flights, indent=4)
    flights_file = open("ori-data/flight_ori.json", "w")
    flights_file.write(text)
    flights_file.close()
    return flights


def clear_flight():
    print("clear flights...")
    for flight in flights[:]:
        ori = flight["origin"]
        dst = flight["destination"]

        ori_exist = False
        dst_exist = False
        exist = False
        for airport in airports:
            if ori_exist is False and ori["iata"] == airport["iata"]:
                ori_exist = True
                ori_airport = airport
            elif dst_exist is False and dst["icao"] == airport["icao"]:
                dst_exist = True
                dst_airport = airport

            if ori_exist is True and dst_exist is True:
                if ori_airport["country"] == dst_airport["country"]:
                    exist = False
                else:
                    exist = True
                break

        if exist is False:
            flights.remove(flight)

    text = json.dumps(flights, indent=4)
    flights_file = open("flight/flight-" + time.strftime("%H%M%S", time.localtime()) + ".json", "w")
    flights_file.write(text)
    flights_file.close()
    return flights


def get_airlines(fs):
    print("get airlines...")
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
    airlines_file.close()


def statistic(fs):
    print("statistic data...")
    '''
    if os.path.isfile("sta-data/statistics.json") and os.path.getsize("sta-data/statistics.json") != 0:
        statistics_text = open("sta-data/statistics.json", encoding="utf-8-sig")
        statistics = json.load(statistics_text)
        statistics_text.close()

        text = json.dumps(statistics, indent=4)
        old_statistics_file = open("sta-data/statistics-" + time.strftime("%H%M%S", time.localtime()) + ".json", "w")
        old_statistics_file.write(text)
        old_statistics_file.close()
    else:
    '''


    for f in fs:
        origin = f["origin"]
        destination = f["destination"]
        bool_in = False
        bool_out = False

        for s in statistics:
            if s["airport"] == origin:
                if s["flights_in"].count(f["flight_id"]) == 0:
                    s["flights_in"].append(f["flight_id"])
                    s["count_in"] += 1
                    bool_in = True
            if s["airport"] == destination:
                if s["flights_out"].count(f["flight_id"]) == 0:
                    s["flights_out"].append(f["flight_id"])
                    s["count_out"] += 1
                    bool_out = True
        if not bool_in:
            flights_in = [f["flight_id"]]
            flights_out = []
            airport = {"airport": origin,
                       "flights_in": flights_in,
                       "flights_out": flights_out,
                       "count_in": 1,
                       "count_out": 0}
            statistics.append(airport)

        if not bool_out:
            flights_in = []
            flights_out = [f["flight_id"]]
            airport = {"airport": destination,
                       "flights_in": flights_in,
                       "flights_out": flights_out,
                       "count_in": 0,
                       "count_out": 1}
            statistics.append(airport)

    text = json.dumps(statistics, indent=4)
    statistics_file = open("sta-data/statistics-" + time.strftime("%H%M%S", time.localtime()) + ".json", "w")
    statistics_file.write(text)
    statistics_file.close()


def job():
    print("-----------------------------------------------------------------------------")
    print(time.strftime("%H:%M:%S", time.localtime()))
    get_flight()
    flights = clear_flight()
    get_airlines(flights)
    statistic(flights)


def rank_airports():
    statistics_file = open("sta-data/statistics.json", "r")
    statistics = json.load(statistics_file)
    statistics_file.close()

    ranked = sorted(statistics, key=lambda st: st["count_in"] + st["count_out"], reverse=True)
    num = 0
    front = -1
    rank = 1
    ranks = []
    for r in ranked:
        if r["count_in"] + r["count_out"] == front:
            num += 1
        else:
            rank += num
            num = 1
        front = r["count_in"] + r["count_out"]
        airport = {"iata": r["airport"]["iata"],
                   "icao": r["airport"]["icao"],
                   "count_in": r["count_in"],
                   "count_out": r["count_out"],
                   "count_total": r["count_in"] + r["count_out"],
                   "rank": rank
                   }
        ranks.append(airport)

    text = json.dumps(ranks, indent=4, ensure_ascii=False)
    show_file = open("rank.json", "w", encoding="utf-8")
    show_file.write(text)
    show_file.close()

    all_airports_with_rank = json.load(open('airports.json', 'r'))

    for ap in all_airports_with_rank:
        for r in ranks:
            if ap["iata"] == r["iata"] and ap["icao"] == r["icao"]:
                ap["count_in"] = r["count_in"]
                ap["count_out"] = r["count_out"]
                ap["count_total"] = r["count_total"]
                ap["rank"] = r["rank"]
                break

    text = json.dumps(airports, indent=4, ensure_ascii=False)
    show_file = open("all_airports_with_rank.json", "w", encoding="utf-8")
    show_file.write(text)
    show_file.close()

    airports_with_rank = []
    for ap in all_airports_with_rank:
        if "rank" in ap:
            airports_with_rank.append(ap)

    text = json.dumps(airports_with_rank, indent=4, ensure_ascii=False)
    show_file = open("airports_with_rank.json", "w", encoding="utf-8")
    show_file.write(text)
    show_file.close()


if __name__ == "__main__":
    print(time.strftime("%H:%M:%S", time.localtime()))

    get_airports()
    get_flight()
    flights = clear_flight()
    get_airlines(flights)
    statistic(flights)

    schedule.every(2).minutes.do(job)

    while 0:
        schedule.run_pending()
        time.sleep(1)

    rank_airports()
