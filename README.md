DISCLAIMER: this is a learning experience more than it is an actual project (in short i have no idea of what i'm doing), and as such, there is more than a little use of AI in it.
I have no idea if this is allowed or not by the terms of service of warframe.market, and this project is in no way associated with them.
Use at your own peril. 


When ready this program will allow you to set the standing for all your syndicates (need to be done manually, as i don't think warframe has APIs to visualize that info) and from that automatically post sell orders for every mod that the sydicate has available depending on your rank and standing balance: example:

You have steel meridian rank 5 and 100000 standing: 100000/25000 = 4 (25000 cost of a mod) instances of every mod that the seller sells will be created, at a price of the lowest at the moment online - 1 platinum, so that you improve your odds of converting your standing in sweet sweet platinum faster.

Possibly implement a routine that periodically checks if you're being undercut, and updates the price accordingly.

When you sell a copy of a mod, set a new quantity of all the "linked" mods (the ones from the same syndicate) available (in this example 3 as you now have only 75000 standing).

At the moment the program doesn't do any of that, and i have no estimates for when it will be in ay way ready.
