import time
from math import floor

import requests
import syndicate_mods
import order_post_helpers as oph



session = oph.login()
currently_posted = oph.check_current_offers(session)
    
#oph.post_offers_for_all_slugs(session, syndicate_mods.test_mods, standing=50000, syndicate_rank=0)
#time.sleep(2)  # Wait a moment to ensure offers are posted before checking again
#oph.linked_item_sold(session, "surging_dash", original_quantity=2, sold_quantity=1)

#post_offers_for_all_slugs(session, syndicate_mods.steel_meridian_mods, standing=52000, syndicate_rank=5)
# get_item_id_from_slug("fireball_frenzy")
# post_offer(session, "fireball_frenzy", 10, 1, 0)
    