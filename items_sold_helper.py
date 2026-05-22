import json
import math
import time

from main import list_available_syndicate_mods
from main import post_offers_for_all_slugs
from main import check_current_offers
from main import get_item_id_from_slug
from main import post_offer
from main import BASE_URL
import requests 
import syndicate_mods

STATUS_FILE = "syndicate_status.json"

def load_status():
    with open(STATUS_FILE, "r") as f:
        return json.load(f)

def save_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def linked_item_sold(session, item_slug, sold_quantity=1):
    """
    Handles a sale by finding valid factions, letting you choose 
    which pool to spend from, and updating your live offerings.
    """
    status_data = load_status()
    valid_factions = []
    
    print(f"\n--- Sale Logged: {sold_quantity}x {item_slug} ---")
    
    # 1. Scan your status file to find which factions can afford this sale
    for faction_name, info in status_data.items():
        faction_dict = syndicate_mods.syndicates[faction_name]
        cost = faction_dict["cost"]
        
        # Check if you have the rank unlocked AND enough standing to afford the purchase
        available_mods = list_available_syndicate_mods(faction_dict, info["rank"])
        if item_slug in available_mods and info["standing"] >= (cost * sold_quantity):
            valid_factions.append(faction_name)
            
    # 2. Handle the deduction logic based on how many factions match
    if not valid_factions:
        print(f"Error: No factions found with enough standing/rank to sell {item_slug}.")
        return
        
    elif len(valid_factions) == 1:
        chosen_faction = valid_factions[0]
        print(f"Automatically attributing sale to the only capable faction: {chosen_faction}")
        
    else:
        # Overlap found (e.g., both Suda and Perrin have the mod and have enough standing)
        print("This mod is available from multiple factions you possess standing with:")
        for i, faction in enumerate(valid_factions):
            current_standing = status_data[faction]["standing"]
            print(f"  [{i}] {faction} (Current Standing: {current_standing})")
            
        # Prompt user to choose the source faction safely
        while True:
            try:
                choice = int(input(f"Select which faction to subtract standing from (0-{len(valid_factions)-1}): "))
                if 0 <= choice < len(valid_factions):
                    chosen_faction = valid_factions[choice]
                    break
            except ValueError:
                pass
            print("Invalid selection. Please choose a number from the list.")

    # 3. Calculate standing cost and deduct it from your local tracking profile
    cost_per_mod = syndicate_mods.syndicates[chosen_faction]["cost"]
    total_cost = cost_per_mod * sold_quantity
    
    status_data[chosen_faction]["standing"] -= total_cost
    save_status(status_data)
    print(f"Deducted {total_cost} standing from {chosen_faction}. New balance: {status_data[chosen_faction]['standing']}")
    
    # 4. Refresh the live market matching your newly modified balance window!
    print(f"\nUpdating live offers for {chosen_faction}...")
    post_offers_for_all_slugs(
        session=session,
        syndicate_slug_list=syndicate_mods.syndicates[chosen_faction], # Uses your existing function syntax
        standing=status_data[chosen_faction]["standing"],
        syndicate_rank=status_data[chosen_faction]["rank"]
    )


if __name__ == "__main__":
    print(f"Loaded status: {load_status()}")