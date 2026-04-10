import requests

test_url = "https://www.amazon.in"

with open("proxies.txt") as f:
    proxies = [p.strip() for p in f]

working = []

for proxy in proxies:

    proxy_dict = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }

    try:
        r = requests.get(
            test_url,
            proxies=proxy_dict,
            timeout=8
        )

        if r.status_code == 200:
            print("WORKING:", proxy)
            working.append(proxy)
        else:
            print("BLOCKED:", proxy)

    except:
        print("FAILED:", proxy)


print("\nWorking proxies:")

for p in working:
    print(p)