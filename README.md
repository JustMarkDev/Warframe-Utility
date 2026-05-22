# Warframe Market Syndicate Automator

An experimental automation tool designed to dynamically manage and scale Syndicate offerings on `warframe.market`.

---

> [!CAUTION]
> **Disclaimer:** This project is a personal learning experience built with extensive use of AI assistance. It is completely independent and not affiliated with `warframe.market`. Automating platform interactions may violate their Terms of Service. **Use at your own risk.**

---

## 📌 Project Overview

This utility automates the process of converting in-game Syndicate standing into Platinum. Instead of manually listing individual mods and updating prices, the script acts as an automated manager that scales item quantities based on your real-time faction balance.

[ Standing Balance ] ──> [ Calculate Inventory ] ──> [ Live Market Ledger ]
(e.g., 100,000)          (100k / 25k = 4 units)         ( Cheaper by 1p )

---

## 🛠️ Planned Features & Logic

### 1. Manual Ledger Sync
Since Warframe does not provide public APIs for player standing, you manually input your current rank and standing balances into a local config file, which the program uses as its source of truth.

### 2. Automated Undercutting
The engine automatically scans active online sellers for each mod and sets your price to:

$$\text{Your Price} = \text{Cheapest Online Price} - 1\text{p}$$

### 3. Dynamic Quantity Scaling
Your listing quantities are directly tied to your available standing. When you log a sale, the script recalculates your balance and updates all linked mods in that syndicate:

* **Before Sale:** **100,000 standing** with *Steel Meridian* = Lists **4 copies** of every mod.
* **After Sale:** You sell 1 mod, dropping you to **75,000 standing** = Automatically updates all remaining listings to **3 copies**.

### 4. Price Monitor *(Planned)*
A background routine to periodically check if you are being undercut and adjust your active prices to keep your listings competitive.

---

## 📅 Project Status

This utility is currently in early prototyping. The core logic is undergoing testing, and **there is no current timeline for a stable release.**

What Works For Now:

1) post offer via script
2) post all mods purchaseable via one syndicate (only the six that sell augments for now) in quantity compatible with your standing availability
3) update or delete listing if you sell some or all the mods respectively

## TODO

1) Web/Gtk interface for ease of use