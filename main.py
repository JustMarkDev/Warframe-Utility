from math import floor

import syndicate_mods
import order_post_helpers as oph
import streamlit as st

st.title("Automatic warframe.market Utility")

if "initial_load" not in st.session_state:
    st.session_state.status_cache = oph.load_status()
    st.session_state.initial_load = True

session = oph.login()

if session is None:
    st.warning("⚠️ **Authentication Required:** Streamlit is currently unable to connect to your `warframe.market` account.")
    
    st.markdown("""
    This utility needs a **JWT Session Token** to communicate with `warframe.market` on your behalf.
    Because of browser security policies, we cannot automatically read this from your browser. 
    However, you can set it up in **under 20 seconds** by following the simple steps below:
    """)
    
    with st.container(border=True):
        st.markdown("### 🔑 Guided Setup Wizard")
        
        st.markdown("""
        **Step 1: Log In to Warframe Market**  
        Ensure you are logged in to your account. Click the button below to open the website in a new tab:
        """)
        st.link_button("🌐 Open warframe.market", "https://warframe.market", use_container_width=True)
        
        st.markdown("""
        **Step 2: Retrieve the JWT Cookie**  
        * Open your browser's Developer Tools (press **F12** or **Ctrl+Shift+I**).
        * Go to the **Application** tab (Chrome/Edge) or **Storage** tab (Firefox).
        * In the left sidebar, expand **Cookies** and select `https://warframe.market`.
        * Find the cookie named **`JWT`** (all capitals).
        * Double-click the **Value** column of the `JWT` row and copy it.
        """)
        
        st.info("💡 **Tip:** The token is a long, randomized string of letters and numbers.")
        
        input_token = st.text_input("Paste your JWT Token here:", type="password", help="Your token is kept strictly local and is only used to make requests directly to warframe.market APIs.")
        
        if st.button("🔑 Authenticate and Save", type="primary", use_container_width=True):
            if input_token:
                with st.spinner("Validating token with warframe.market..."):
                    test_session = oph.save_token(input_token)
                    if test_session:
                        st.success(f"Successfully logged in as **{test_session.accountName}**!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid JWT token. Please make sure you copied the entire value exactly.")
            else:
                st.warning("Please paste a token before submitting.")
                
    st.stop()  # Stop rendering the rest of the application


@st.dialog("Resolve Syndicate Overlap")
def show_faction_choice_modal(valid_factions, sold_qty, original_qty):
    st.write("This item belongs to multiple syndicates you represent. Which pool should spend the standing?")
    chosen = st.radio("Select Source Faction:", valid_factions)
    if st.button("Confirm Choice", type="primary"):
        oph.linked_item_sold(session, chosen, sold_qty, original_qty)
        st.rerun()

def sync_slider_to_input(faction_key):
    """Fires when the slider moves -> updates the numeric text box."""
    st.session_state[f"input_{faction_key}"] = st.session_state[f"slide_{faction_key}"]
    oph.save_status_from_state()

def sync_input_to_slider(faction_key, max_val):
    """Fires when values are typed -> clamps the number and moves the slider."""
    typed_val = st.session_state[f"input_{faction_key}"]
    # Keep the manually typed value within safe current rank limits
    clamped_val = min(max(0, typed_val), max_val)
    
    st.session_state[f"slide_{faction_key}"] = clamped_val
    st.session_state[f"input_{faction_key}"] = clamped_val
    oph.save_status_from_state()

with st.sidebar:
    st.header("Account Profile")
    if session:
        st.success(f"Logged in as: **{session.accountName}**")
    else:
        st.error("Not Authenticated")
        
    st.divider()
    st.info("Set your standing in the main window to update your active market offers.")

for faction_key, faction_info in syndicate_mods.syndicates.items():
    saved_data = st.session_state.status_cache.get(faction_key, {"standing": 0, "rank": 5})
    mod_cost = faction_info.get("cost", 25000)
    
    with st.container(border=True):
        clean_name = faction_key.replace("_", " ").title()
        st.markdown(f"### 🛡️ {clean_name}")
        
        col_rank, col_standing, col_controls = st.columns([1, 2, 1.2])
        
        rank_key = f"rank_{faction_key}"
        slide_key = f"slide_{faction_key}"
        input_key = f"input_{faction_key}"
        
        # 1. Rank Node
        with col_rank:
            if rank_key not in st.session_state:
                st.session_state[rank_key] = int(saved_data["rank"])
            chosen_rank = st.selectbox("Rank", options=[0, 1, 2, 3, 4, 5], key=rank_key, on_change=oph.save_status_from_state)
            
        max_standing_allowed = syndicate_mods.RANK_STANDING_LIMITS[chosen_rank]
        max_mods_listable = max_standing_allowed // mod_cost
        
        if slide_key not in st.session_state:
            st.session_state[slide_key] = int(saved_data["standing"])
        if input_key not in st.session_state:
            st.session_state[input_key] = int(saved_data["standing"])
            
        if st.session_state[slide_key] > max_standing_allowed:
            st.session_state[slide_key] = max_standing_allowed
            st.session_state[input_key] = max_standing_allowed
            oph.save_status_from_state()

        # 2. Main Tracking Slider
        with col_standing:
            st.slider("Available Standing", min_value=0, max_value=max_standing_allowed, key=slide_key, step=1000, on_change=sync_slider_to_input, args=(faction_key,))
            
        # 3. Operations Panel
        with col_controls:
            # Step A: Max listable limit constraint layout input
            target_listable_qty = st.number_input(
                "Quantity to List/Sell",
                min_value=1,
                max_value=max(1, max_mods_listable),
                value=max(1, st.session_state[slide_key] // mod_cost),
                key=f"limit_{faction_key}"
            )
            
            # Step B: Value Input Configuration
            st.number_input("Exact Standing", min_value=0, max_value=max_standing_allowed, key=input_key, step=1000, on_change=sync_input_to_slider, args=(faction_key, max_standing_allowed))
            
            # Step C: Execution Buttons Grouping
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                if st.button("Publish", key=f"pub_{faction_key}", use_container_width=True):
                    # Pull current state parameters safely
                    curr_standing = st.session_state[slide_key]
                    curr_rank = st.session_state[rank_key]
                    
                    oph.post_offers_for_all_slugs(
                        session=session,
                        syndicate_slug_list=faction_info,
                        standing=curr_standing,
                        syndicate_rank=curr_rank
                    )
            
            with btn_col2:
                if st.button("Sold", key=f"sold_{faction_key}", type="secondary", use_container_width=True):
                    # Dynamically collect items available at current rank to process selection
                    available_mods = oph.list_available_syndicate_mods(faction_info, st.session_state[rank_key])
                    
                    if available_mods:
                        # Grab the first available mod as a placeholder item slug for validation
                        sample_slug = available_mods[0] 
                        
                        # Find which factions can afford the deduction
                        status_data = oph.load_status()
                        valid_factions = []
                        
                        for f_name, info in status_data.items():
                            f_dict = syndicate_mods.syndicates[f_name]
                            f_mods = oph.list_available_syndicate_mods(f_dict, info["rank"])
                            if sample_slug in f_mods and info["standing"] >= f_dict["cost"]:
                                valid_factions.append(f_name)
                        
                        if len(valid_factions) > 1:
                            # Trigger our modal popup window if multiple factions qualify
                            show_faction_choice_modal(valid_factions, sold_qty=1, original_qty=target_listable_qty)
                        elif len(valid_factions) == 1:
                            oph.linked_item_sold(session, available_mods[0], sold_quantity=1, original_quantity=target_listable_qty)
                        else:
                            st.error("No factions possess enough standing to process this sale transaction.")
                    else:
                        st.warning("No item listings available at this rank level to mark as sold.")



# currently_posted = oph.check_current_offers(session)

#oph.post_offers_for_all_slugs(session, syndicate_mods.test_mods, standing=50000, syndicate_rank=0)
#time.sleep(2)  # Wait a moment to ensure offers are posted before checking again
#oph.linked_item_sold(session, "surging_dash", original_quantity=2, sold_quantity=1)

#post_offers_for_all_slugs(session, syndicate_mods.steel_meridian_mods, standing=52000, syndicate_rank=5)
# get_item_id_from_slug("fireball_frenzy")
# post_offer(session, "fireball_frenzy", 10, 1, 0)
    