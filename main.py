import requests



# Base URL for WFM API v2
BASE_URL = "https://api.warframe.market/v2"

def login():
    # 1. Open and read the full token (remove the 0)
    with open("settings.conf", "r") as file:
        jwt_token = file.readline().strip()
        
    session = requests.Session()
    
    # 2. Update headers globally with your valid browser token
    session.headers.update({
        "User-Agent": "WarframeUtilityApp/1.0.0 (Python requests)",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}",
        "platform": "pc",
        "language": "en",
        "Origin": "https://warframe.market",
        "Referer": "https://warframe.market/"
    })
    
    print("Attempting profile lookup with manual token...")
    
    profile_response = session.get(f"{BASE_URL}/me")
    
    if profile_response.status_code == 200:
        print("Success! Authenticated via settings.conf token.")
        print(profile_response.json())
        return session # Return the active authenticated session to use elsewhere
    else:
        print(f"Failed to access profile. Status Code: {profile_response.status_code}")
        print(profile_response.text)
        return None


def fetch_lowest_price_online(item_slug):
    response = requests.get(f"{BASE_URL}/orders/item/{item_slug}/top")
    if response.status_code == 200:
        data = response.json()["data"]["sell"][0]
        return data['platinum']
    else:
        print(f"Error fetching orders for {item_slug}: {response.status_code}")
        return None

def post_offers_for_all_slugs(session, item_slug_list, quantity=1):
    for slug in item_slug_list:
        slug_lowest_price = fetch_lowest_price_online(slug)
        post_price = slug_lowest_price - 1
        print(f"Lowest price for {slug}: {slug_lowest_price} platinum. Posting offer at {post_price} platinum.")
        post_offer(session, slug, post_price, quantity, 0)

def get_item_id_from_slug(item_slug):
    response = requests.get(f"{BASE_URL}/items/{item_slug}")
    if response.status_code == 200:
          data = response.json()
          print(f"Item ID for {item_slug}: {data['data']['id']}")
          return data["data"]["id"]

def post_offer(session, item_slug, platinum, quantity, rank):
    item_id = get_item_id_from_slug(item_slug)
    offer_data = {
        "itemId": item_id,
        "type": "sell",
        "platinum": int(platinum),
        "quantity": int(quantity),
        "rank": int(rank),
        "visible": True
    }

    print(f"Posting {item_slug} (Rank {rank}) for {platinum}p...")
    response = session.post(f"{BASE_URL}/order", json=offer_data)

    if response.status_code in [200, 201]:
        print("Success! Order posted live to the market ledger.")
        order_info = response.json().get("data", {})
        print(f"Created Order ID: {order_info.get('id')}")
        return order_info
    else:
        print(f"Failed to post order. Error Code: {response.status_code}")
        print(f"Server message: {response.text}")
        return None

if __name__ == "__main__":
    session = login()
    # post_offers_for_all_slugs(session, )
    # get_item_id_from_slug("fireball_frenzy")
    # post_offer(session, "fireball_frenzy", 10, 1, 0)
    