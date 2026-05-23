# 🛡️ Tenno Syndicate Automator

> [!WARNING]
> This project is a personal learning experience built with extensive use of AI assistance. It is completely independent and not affiliated with warframe.market. Automating platform interactions may violate their Terms of Service. Use at your own risk.

A lightweight, high-performance native desktop application designed for **Warframe** players to seamlessly track and manage their Syndicate standing, calculate listable offerings, automate undercutting calculations, and publish sell listings directly to the **warframe.market** HTTP REST APIs.

Built with a safe, asynchronous **native Rust backend** (Tauri v2) and a reactive **Vite + React (TypeScript) + Vanilla CSS** dark-mode glassmorphic frontend.

---

## 🚀 Easy Steps to Run & Develop

Follow these simple steps to spin up the application on your system:

### 1. Prerequisites
Ensure you have the following installed:
*   [Node.js](https://nodejs.org/) (v18+)
*   [Rust & Cargo](https://www.rust-lang.org/tools/install) (v1.75+)

### 2. Startup Commands
Open your terminal inside the project directory and run:
```bash
# Install npm dependencies
npm install

# Launch the desktop client in development mode
npm run tauri dev
```
Tauri will automatically compile the Rust backend, bind the IPC handlers, and open the desktop application window.

---

## 🛡️ How to Operate the Automator

Once authenticated, the application takes you to the main control room:

1.  **Sync standing:** Adjust the sliders for each represented faction to match your in-game standing values. Standing caps are automatically recalculated if you adjust your faction rank dropdown.
2.  **Publish offerings:** Click **"Publish Offerings"** for a faction. The Rust engine queries the lowest active prices for that faction's mods, undercuts them by `1 Platinum`, and posts/updates live sell orders on your behalf.
3.  **Log sales:** Select a sold mod from the dropdown list, enter the quantity, and click **"Log Completed Sale"**.
4.  **Resolve conflicts (Attribution Modal):** If the sold mod belongs to multiple active factions you represent, an elegant frosted-glass modal overlay will prompt you to select which syndicate's pool to deduct the standing from. The backend will automatically adjust standings and cascade update all your active market listings!

---

## 🔮 Planned Improvements & TODOs

We are constantly looking to expand the capabilities of the Tenno Syndicate Automator. Here is our current roadmap:

- [ ] **Real-Time Price Monitoring & Re-undercutting:** A background worker in the Rust backend to monitor competitor price shifts and automatically prompt adjustments or dynamically underbid to keep listings active.
- [ ] **Customizable Pricing Strategy:** Allow users to set their own undercutting margins (e.g., matching lowest price instead of undercutting, or setting custom Platinum values) and establish a "price floor" to avoid selling rare mods too cheap.
- [ ] **Advanced Profit & Sales Analytics:** A dashboard view showing historical sales logs, total Platinum earned, and standing-to-platinum efficiency metrics per syndicate.
- [ ] **Multi-Profile Support:** Capability to manage and switch between multiple `warframe.market` user accounts or game platform profiles (PC, PlayStation, Xbox, Switch).
- [ ] **Intelligent Offering Planner:** Recommend the most optimal mods/offerings to sell based on current daily market demand and standing conversion efficiency.
- [ ] **Automatic Session Token Refresh:** Detection of expired JWT tokens and seamless automated re-authentication via the in-app login window.

