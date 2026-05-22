import json
import math
import time
from math import floor
import requests
import syndicate_mods
import streamlit as st

BASE_URL = "https://api.warframe.market/v2"
STATUS_FILE = "syndicate_status.json"

def load_status():
    with open(STATUS_FILE, "r") as f:
        return json.load(f)
    
def save_status_from_state():
    """Extracts data values from the live UI and saves them to disk."""
    status_data = load_status()
    
    for faction_key in syndicate_mods.syndicates.keys():
        # Read the explicit tracked state dictionary keys
        live_rank = st.session_state.get(f"rank_{faction_key}")
        live_standing = st.session_state.get(f"slide_{faction_key}")
        
        if live_rank is not None and live_standing is not None:
            status_data[faction_key]["rank"] = int(live_rank)
            status_data[faction_key]["standing"] = int(live_standing)
            
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f, indent=4)

def save_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=4)

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
    quantity = floor(standing/syndicate_slug_list["cost"])
    item_slug_list = list_available_syndicate_mods(syndicate_slug_list, syndicate_rank)
    if quantity > 0:
        for slug in item_slug_list:
            slug_lowest_price = fetch_lowest_price_online(slug)
            post_price = slug_lowest_price - 1
            print(f"Lowest price for {slug}: {slug_lowest_price} platinum. Posting offer at {post_price} platinum.")
            post_offer(session, slug, post_price, quantity, 0)
            st.toast(f"Posted {quantity} {slug}s")
            time.sleep(0.3)
    else:
        print(f"Not enough standing to post offers. Required: {syndicate_slug_list['cost']}, Available: {standing}")
"""
def process_faction_deduction(session, chosen_faction, sold_quantity, original_quantity):
    # Updates the JSON file ledger and synchronously reduces active live listings on site.
    status_data = load_status()
    cost_per_mod = syndicate_mods.syndicates[chosen_faction]["cost"]
    total_cost = cost_per_mod * sold_quantity
    
    # 1. Update persistent file database
    status_data[chosen_faction]["standing"] -= total_cost
    save_status(status_data)
    
    st.toast(f"Deducted {total_cost} standing from {chosen_faction}! Syncing market...")
    
    # 2. FIXED: Map and update live market listings via warframe.market API
    # Extract every mod available at our current faction tier ranking level
    current_rank = int(status_data[chosen_faction]["rank"])
    to_update = list_available_syndicate_mods(syndicate_mods.syndicates[chosen_faction], current_rank)
    
    new_quantity = max(0, original_quantity - sold_quantity)
    
    for slug in to_update:
        try:
            # Call your live framework script function
            update_order(session, slug, new_quantity=new_quantity)
            print(f"Successfully reduced live offer for {slug} to x{new_quantity}")
        except Exception as e:
            print(f"Failed to update market asset {slug}: {e}")
"""
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

def linked_item_sold(session, item_slug, original_quantity, sold_quantity=1, chosen_faction=None):
    status_data = load_status()
    valid_factions = []
    
    print(f"\n--- Sale Logged: {sold_quantity}x {item_slug} ---")
    
    for faction_name, info in status_data.items():
        faction_dict = syndicate_mods.syndicates[faction_name]
        cost = faction_dict["cost"]
        available_mods = list_available_syndicate_mods(faction_dict, info["rank"])
        
        if item_slug in available_mods and info["standing"] >= (cost * sold_quantity):
            valid_factions.append(faction_name)
            
    if not valid_factions:
        print(f"Error: No factions found with enough standing/rank to sell {item_slug}.")
        return False
        
    elif len(valid_factions) == 1:
        chosen_faction = valid_factions[0]
        print(f"Automatically attributing sale to the only capable faction: {chosen_faction}")
        
    else:
        # If the web UI hasn't passed us a pre-selected faction choice yet, 
        # return the valid list to show the popup selection tool.
        if chosen_faction is None:
            print("Multiple factions detected. Waiting for user input via Streamlit Pop-up...")
            return valid_factions

    # --- REST OF YOUR ORIGINAL FUNCTION CONTINUES EXECUTING UNCHANGED ---
    cost_per_mod = syndicate_mods.syndicates[chosen_faction]["cost"]
    total_cost = cost_per_mod * sold_quantity
    
    status_data[chosen_faction]["standing"] -= total_cost
    save_status(status_data)
    print(f"Deducted {total_cost} standing from {chosen_faction}. New balance: {status_data[chosen_faction]['standing']}")
    
    print(f"\nUpdating live offers for {chosen_faction}...")
    
    to_update = list_available_syndicate_mods(syndicate_mods.syndicates[chosen_faction], status_data[chosen_faction]["rank"])
    for order in to_update:
        update_order(session, order, new_quantity=original_quantity - sold_quantity)
        time.sleep(0.4)  # Brief pause to respect API rate limits
        print(f"Updated offer for {order} to reflect new quantity: {original_quantity - sold_quantity}")
            
    return True

def get_orders_from_slug(session, item_slug):
    # 1. Retrieve the unique internal itemId string for this slug
    target_item_id = get_item_id_from_slug(item_slug)
    if not target_item_id:
        return None

    # 2. Query your live personal order book configuration
    response = session.get(f"{BASE_URL}/orders/my")
    
    if response.status_code == 200:
        orders = response.json().get("data", [])
        
        # 3. Match against the verified itemId field key
        matching_orders = [order for order in orders if order.get("itemId") == target_item_id]
        
        if matching_orders:
            return matching_orders[0]["id"]
        else:
            print(f"No active profile listing found matching itemId: {target_item_id} ({item_slug})")
            return None
    else:
        print(f"Failed to fetch profile orders. Status Code: {response.status_code}")
        print(response.text)
        return None

def update_order(session, item_slug, new_price=None, new_quantity=None):
    order_id = get_orders_from_slug(session, item_slug)
    if not order_id:
        print(f"Order for item {item_slug} not found.")
        return None

    update_data = {}

    if new_price is not None:
        update_data["platinum"] = int(new_price)
    if new_quantity is not None:
        update_data["quantity"] = int(new_quantity)

    if not update_data:
        print("No updates provided. Please specify a new price and/or quantity.")
        return

    print(f"Updating Order ID {order_id} with data: {update_data}")
    if new_quantity > 0:
        response = session.patch(f"{BASE_URL}/order/{order_id}", json=update_data)
    else:
        response = session.delete(f"{BASE_URL}/order/{order_id}")
    
    if response.status_code == 200:
        print("Order updated successfully.")
        return response.json().get("data", {})
    else:
        print(f"Failed to update order. Status Code: {response.status_code}")
        print(response.text)
        return None
    
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
        profile_data = profile_response.json().get("data", {})
        session.accountName = profile_data.get("slug", "Unknown Tenno")
        return session # Return the active authenticated session to use elsewhere
    else:
        print(f"Failed to access profile. Status Code: {profile_response.status_code}")
        print(profile_response.text)
        return None

    
if __name__ == "__main__":
    session = login()
    orders = check_current_offers(session)
    print(orders)
    print(f"Order ID for scattered_justice: {get_orders_from_slug(session, 'scattered_justice')}")
    linked_item_sold(session, "scattered_justice", original_quantity=5, sold_quantity=1)
    # print(get_orders_from_slug(session, "surging_dash"))