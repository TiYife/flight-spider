import json
import re
import requests
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
    #print(response.text)


def get_airlines():
    token = get_token()
    response = requests.get("https://zh.flightaware.com/ajax/ignoreall/vicinity_aircraft.rvt?&minLon=67.5&minLat=4.54833984375&maxLon=100.56884765625&maxLat=26.3671875&token="+token)
    response.enconding = "utf-8"
    print(response.text)

if __name__ == "__main__":
    #token = get_token()
    get_airports()
    get_airlines()

