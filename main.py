import requests

# Base URL for WFM API v2
BASE_URL = "https://api.warframe.market/v2"
headers = {
    "Platform": "pc",
    "Language": "en"
}


def fetch_lowest_price(item_slug):
        response = requests.get(f"{BASE_URL}/orders/item/{item_slug}/top", headers=headers)
        if response.status_code == 200:
            data = response.json()["data"]["sell"][0]
            return data['platinum']
        else:
            print(f"Error fetching orders for {item_slug}: {response.status_code}")
            return None


item_slug = "chroma_prime_systems"
data = fetch_lowest_price(item_slug)
print(f"lowest price for {item_slug}: {data}")

