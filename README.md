# 🛡️ Tenno Syndicate Automator

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

## 🔑 How to Get your Authentication Cookie

To publish offers or log sales automatically, you must authenticate the core engine with your `warframe.market` account. Your token resides strictly on your local machine.

1.  Open **https://warframe.market** in your browser and log in to your account.
2.  Press **F12** (or right-click anywhere and select **Inspect**) to open Developer Tools.
3.  Go to the **Application** tab (on Chrome, Edge, Brave) or **Storage** tab (on Firefox).
4.  Expand the **Cookies** section on the left sidebar and click on `https://warframe.market`.
5.  Locate the cookie named **`JWT`** in the table list.
6.  Double-click its **Value**, copy the entire string, and paste it into the **Tenno Verification Wizard** in the application!

---

## 🛡️ How to Operate the Automator

Once authenticated, the application takes you to the main control room:

1.  **Sync standing:** Adjust the sliders for each represented faction to match your in-game standing values. Standing caps are automatically recalculated if you adjust your faction rank dropdown.
2.  **Publish offerings:** Click **"Publish Offerings"** for a faction. The Rust engine queries the lowest active prices for that faction's mods, undercuts them by `1 Platinum`, and posts/updates live sell orders on your behalf.
3.  **Log sales:** Select a sold mod from the dropdown list, enter the quantity, and click **"Log Completed Sale"**.
4.  **Resolve conflicts (Attribution Modal):** If the sold mod belongs to multiple active factions you represent, an elegant frosted-glass modal overlay will prompt you to select which syndicate's pool to deduct the standing from. The backend will automatically adjust standings and cascade update all your active market listings!
