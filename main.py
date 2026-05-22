import time
from math import floor

import requests
import syndicate_mods
import items_sold_helper

BASE_URL = "https://api.warframe.market/v2"

def login():
    with open("settings.conf", "r") as file:
        jwt_token = file.readline().strip()
        
    session = requests.Session()
    
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

def list_available_syndicate_mods(syndicate_list, syndicate_rank):

    available_slugs = []
    
    
    for rank_level, slugs in syndicate_list.items():
        if rank_level == "cost":
            continue
        if rank_level <= int(syndicate_rank):
            available_slugs.extend(slugs)
            
    return available_slugs

def post_offers_for_all_slugs(session, syndicate_slug_list, standing=0, syndicate_rank=0):
    quantity = floor(standing/syndicate_slug_list["cost"]) # some syndicates have 20k mods while others 25k, so we calculate quantity based on the cost of the mods
                                                           # for that syndicate
    item_slug_list = list_available_syndicate_mods(syndicate_slug_list, syndicate_rank)
    if quantity > 0:
        for slug in item_slug_list:
            slug_lowest_price = fetch_lowest_price_online(slug)
            post_price = slug_lowest_price - 1
            print(f"Lowest price for {slug}: {slug_lowest_price} platinum. Posting offer at {post_price} platinum.")
            post_offer(session, slug, post_price, quantity, 0)
            time.sleep(0.1)  # Sleep to avoid hitting rate limits
    else:
        print(f"Not enough standing to post offers. Required: {syndicate_slug_list['cost']}, Available: {standing}")

def check_current_offers(session):
    response = session.get(f"{BASE_URL}/orders/my")
    if response.status_code == 200:
        orders = response.json().get("data", [])
        print(f"Current active orders: {len(orders)}")
        for order in orders:
            print(f"Order ID: {order['id']}, Price: {order['platinum']}p, Quantity: {order['quantity']}")
    else:
        print(f"Failed to fetch current offers. Status Code: {response.status_code}")
        print(response.text)
    return response.json().get("data", [])




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
    currently_posted = check_current_offers(session)

    #post_offers_for_all_slugs(session, syndicate_mods.steel_meridian_mods, standing=52000, syndicate_rank=5)
    # get_item_id_from_slug("fireball_frenzy")
    # post_offer(session, "fireball_frenzy", 10, 1, 0)
    