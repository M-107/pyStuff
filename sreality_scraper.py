import re
import requests
import pandas as pd

url = "https://www.sreality.cz/api/cs/v2/estates"


def get_number_of_items():
    querystring = {
        "category_main_cb": "1",
        "category_type_cb": "2",
        "page": "1",
        "per_page": "60",
        "tms": '1662884381711" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0" -H "Accept: application/json, text/plain, */*" -H "Accept-Language: cs,sk;q=0.8,en-US;q=0.5,en;q=0.3" -H "Accept-Encoding: gzip, deflate, br" -H "Connection: keep-alive" -H "Referer: https://www.sreality.cz/hledani/pronajem/byty?strana=2" -H "Cookie: lps=eyJfZnJlc2giOmZhbHNlLCJfcGVybWFuZW50Ijp0cnVlfQ.Yx2ZzA.m7A2-_WUqK_zx5wcxhuluGuJdWk; per_page=60" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-origin" -H "DNT: 1" -H "Sec-GPC: 1" -H "TE: trailers',
    }

    response = requests.request("GET", url, params=querystring)
    output = response.json()
    total_items = output["result_size"]
    pages_needed = int(total_items / 60) + (total_items % 60 > 0)
    return pages_needed


def get_listings(p):
    querystring = {
        "category_main_cb": "1",
        "category_type_cb": "2",
        "page": f"{p}",
        "per_page": "60",
        "tms": '1662884381711" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0" -H "Accept: application/json, text/plain, */*" -H "Accept-Language: cs,sk;q=0.8,en-US;q=0.5,en;q=0.3" -H "Accept-Encoding: gzip, deflate, br" -H "Connection: keep-alive" -H "Referer: https://www.sreality.cz/hledani/pronajem/byty?strana=2" -H "Cookie: lps=eyJfZnJlc2giOmZhbHNlLCJfcGVybWFuZW50Ijp0cnVlfQ.Yx2ZzA.m7A2-_WUqK_zx5wcxhuluGuJdWk; per_page=60" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-origin" -H "DNT: 1" -H "Sec-GPC: 1" -H "TE: trailers',
    }

    response = requests.request("GET", url, params=querystring)
    estates = response.json()["_embedded"]["estates"][1:]
    results = []
    for i in estates:
        name = re.sub("[\(\[].*?[\)\]]", "", i["name"]).strip()
        name = name.replace("Pronájem bytu ", "").replace("\xa0m²", "").split()
        rooms = " ".join(name[:-1])
        size = name[-1]
        price = i["price"]
        location_name = i["locality"]
        gps_lat = i["gps"]["lat"]
        gps_lon = i["gps"]["lon"]
        features_in = i["labelsAll"][0]
        features_around = i["labelsAll"][1]
        estate = {
            "Rooms": rooms,
            "Size": size,
            "Price": price,
            "Location": location_name,
            "lattitude": gps_lat,
            "longtitude": gps_lon,
            "Features in": features_in,
            "Features around": features_around,
        }
        results.append(estate)
    return results


pages = get_number_of_items()
all_results = []
for page in range(1, pages + 1):
    print(f"Page {page:>2}/{pages}")
    listings = get_listings(page)
    all_results.append(listings)

results_to_dict = []
for i in all_results:
    for j in i:
        results_to_dict.append(j)

df = pd.DataFrame.from_dict(results_to_dict)
df.to_csv(r"sreality_cz.csv", index=False, header=True)
