import React, { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { check, type Update } from "@tauri-apps/plugin-updater";
import "./App.css";

interface SyndicateState {
  faction_key: string;
  standing: i32;
  rank: i32;
}

type i32 = number;

interface InitData {
  standings: SyndicateState[];
  authenticated: boolean;
  account_name: string | null;
}

interface LogEntry {
  timestamp: string;
  message: string;
  type: "success" | "error" | "info";
}

function App() {
  const [loading, setLoading] = useState(true);
  const debounceTimeouts = useRef<Record<string, any>>({});
  const [authenticated, setAuthenticated] = useState(false);
  const [accountName, setAccountName] = useState<string | null>(null);
  const [standings, setStandings] = useState<SyndicateState[]>([]);

  // Auth inputs
  const [tokenInput, setTokenInput] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [showInstructions, setShowInstructions] = useState(false);

  // Publish tracking
  const [publishingFactions, setPublishingFactions] = useState<Set<string>>(new Set());

  // Publish preview modal state
  const [publishPreview, setPublishPreview] = useState<{
    factionKey: string;
    quantity: number;
    mods: string[];
  } | null>(null);

  // Sale form & catalog state
  const [allMods, setAllMods] = useState<string[]>([]);
  const [saleItem, setSaleItem] = useState("");
  const [saleQty, setSaleQty] = useState(1);
  const [saleLoading, setSaleLoading] = useState(false);

  // Overlap resolution modal state
  const [overlapData, setOverlapData] = useState<{
    itemSlug: string;
    eligibleFactions: string[];
    quantity: number;
  } | null>(null);

  // Logging
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Available update from GitHub Releases (null = up to date)
  const [availableUpdate, setAvailableUpdate] = useState<Update | null>(null);
  const [updateInstalling, setUpdateInstalling] = useState(false);

  // Mod catalog preview states
  const [factionMods, setFactionMods] = useState<Record<string, string[]>>({});
  const [expandedFactions, setExpandedFactions] = useState<Set<string>>(new Set());

  const fetchModsForFaction = async (factionKey: string, rank: number) => {
    try {
      const list = await invoke<string[]>("get_faction_mods", { factionKey, rank });
      setFactionMods((prev) => ({ ...prev, [factionKey]: list }));
    } catch (e) {
      console.error(`Failed to fetch mods for ${factionKey}:`, e);
    }
  };

  const toggleFactionExpand = (factionKey: string) => {
    setExpandedFactions((prev) => {
      const next = new Set(prev);
      if (next.has(factionKey)) {
        next.delete(factionKey);
      } else {
        next.add(factionKey);
      }
      return next;
    });
  };

  const addLog = (message: string, type: "success" | "error" | "info" = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [{ timestamp, message, type }, ...prev].slice(0, 50));
  };

  const loadData = async () => {
    try {
      const data: InitData = await invoke("load_syndicates");
      setStandings(data.standings);
      setAuthenticated(data.authenticated);
      setAccountName(data.account_name);
      
      // Load mods for all active factions on mount
      for (const s of data.standings) {
        await fetchModsForFaction(s.faction_key, s.rank);
      }
      
      addLog("Successfully synced standing ledgers with disk data.", "success");
      if (data.authenticated && data.account_name) {
        addLog(`Authenticated with Warframe Market as: ${data.account_name}`, "info");
      }
    } catch (e: any) {
      addLog(`Failed to load system data: ${JSON.stringify(e)}`, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      await loadData();

      // Load the full mod list from the backend (single source of truth)
      try {
        const mods = await invoke<string[]>("get_all_mods");
        setAllMods(mods);
        if (mods.length > 0) setSaleItem(mods[0]);
      } catch (e) {
        console.error("Failed to load mod catalog:", e);
      }

      // Silently check for updates — non-blocking, never throws to the user
      try {
        const update = await check();
        if (update) setAvailableUpdate(update);
      } catch {
        // Network unavailable or updater not configured — safe to ignore
      }
    };
    init();
  }, []);

  const handleSaveToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput.trim()) return;

    setAuthLoading(true);
    setAuthError(null);
    addLog("Sending authorization handshake to warframe.market...", "info");

    try {
      const slug = await invoke<string>("save_token", { token: tokenInput.trim() });
      setAccountName(slug);
      setAuthenticated(true);
      addLog(`Handshake completed. Welcome back, Tenno ${slug}!`, "success");
      await loadData();
    } catch (e: any) {
      const errStr = e.data || e.toString();
      setAuthError(errStr);
      addLog(`Authentication failed: ${errStr}`, "error");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleStandingChange = (factionKey: string, standing: number) => {
    // Immediate reactive local update
    setStandings((prev) =>
      prev.map((s) => (s.faction_key === factionKey ? { ...s, standing } : s))
    );

    if (debounceTimeouts.current[factionKey]) {
      clearTimeout(debounceTimeouts.current[factionKey]);
    }

    debounceTimeouts.current[factionKey] = setTimeout(async () => {
      try {
        await invoke("update_standing", { factionKey, standing, rank: null });
      } catch (e: any) {
        addLog(`Sync error for ${factionKey}: ${JSON.stringify(e)}`, "error");
      }
    }, 150);
  };

  const handleRankChange = async (factionKey: string, rank: number) => {
    // Immediate reactive local update
    setStandings((prev) =>
      prev.map((s) => (s.faction_key === factionKey ? { ...s, rank } : s))
    );
    addLog(`Faction rank updated: ${formatFactionName(factionKey)} to Rank ${rank}.`, "info");
    
    // Fetch updated list of mods matching the new rank level
    await fetchModsForFaction(factionKey, rank);

    try {
      const updated: SyndicateState = await invoke("update_standing", {
        factionKey,
        standing: standings.find((s) => s.faction_key === factionKey)?.standing || 0,
        rank,
      });
      // Sync corrected standing capacity if adjusted
      setStandings((prev) =>
        prev.map((s) => (s.faction_key === factionKey ? updated : s))
      );
    } catch (e: any) {
      addLog(`Failed to update rank for ${factionKey}: ${JSON.stringify(e)}`, "error");
    }
  };

  const handlePublish = async (factionKey: string) => {
    setPublishPreview(null);
    setPublishingFactions((prev) => {
      const next = new Set(prev);
      next.add(factionKey);
      return next;
    });
    addLog(`Publishing active sell orders for ${formatFactionName(factionKey)}...`, "info");

    try {
      const mods: string[] = await invoke("publish_syndicate", { factionKey });
      addLog(`Successfully published/undercut ${mods.length} listings for ${formatFactionName(factionKey)}!`, "success");
    } catch (e: any) {
      const errStr = e.data || JSON.stringify(e);
      addLog(`Publish failed for ${formatFactionName(factionKey)}: ${errStr}`, "error");
    } finally {
      setPublishingFactions((prev) => {
        const next = new Set(prev);
        next.delete(factionKey);
        return next;
      });
    }
  };

  const handleRecordSale = async (factionChoice: string | null = null) => {
    setSaleLoading(true);
    addLog(`Recording sale: ${saleQty}x ${saleItem}...`, "info");

    try {
      const choice = factionChoice || null;
      const attributed: string = await invoke("record_sale", {
        itemSlug: saleItem,
        quantity: saleQty,
        factionChoice: choice,
      });

      addLog(`Sale recorded! Attributed standing deduction to ${formatFactionName(attributed)}. Updated active listings.`, "success");
      setOverlapData(null);
      await loadData();
    } catch (e: any) {
      if (e.type === "Overlap") {
        addLog(`Attribution conflict: '${saleItem}' belongs to multiple represented syndicates.`, "info");
        setOverlapData({
          itemSlug: e.data.item_slug,
          eligibleFactions: e.data.eligible_factions,
          quantity: saleQty,
        });
      } else if (e.type === "InsufficientStanding") {
        addLog(`Insufficient standing: Cannot deduct standing for '${saleItem}'.`, "error");
      } else {
        const errStr = e.data || JSON.stringify(e);
        addLog(`Failed to log sale: ${errStr}`, "error");
      }
    } finally {
      setSaleLoading(false);
    }
  };

  const handleInstallUpdate = async () => {
    if (!availableUpdate) return;
    setUpdateInstalling(true);
    addLog(`Downloading update v${availableUpdate.version}...`, "info");
    try {
      await availableUpdate.downloadAndInstall();
      // App restarts automatically after install
    } catch (e: any) {
      addLog(`Update failed: ${e?.toString()}`, "error");
      setUpdateInstalling(false);
    }
  };

  const getMaxStanding = (rank: number) => {
    switch (rank) {
      case 5: return 132000;
      case 4: return 99000;
      case 3: return 70000;
      case 2: return 44000;
      case 1: return 22000;
      default: return 5000;
    }
  };

  const formatFactionName = (key: string) => {
    return key.replace(/_/g, " ");
  };

  if (loading) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card">
          <svg className="auth-icon spinner" viewBox="0 0 24 24">
            <path d="M12 4V2m0 20v-2m8-8h2M2 12h2m13.657-5.657l1.414-1.414M5.636 18.364l1.414-1.414m0-11.314L5.636 5.636m12.728 12.728l-1.414-1.414" stroke="#c79b3d" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <h2>Initialising Ledgers</h2>
          <p>Handshaking with safe Rust memory channels...</p>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card">
          <svg className="auth-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.75z" />
          </svg>
          <h2>Tenno Verification Required</h2>
          <p>Please enter your <code>warframe.market</code> JWT cookie token. Your token is encrypted and resides safely on your local disk backend.</p>
          
          <form onSubmit={handleSaveToken} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div className="auth-input-group">
              <label htmlFor="token">JWT Token Header</label>
              <input
                id="token"
                type="password"
                className="auth-input"
                placeholder="JWT cookie authentication token..."
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                disabled={authLoading}
              />
              <button
                type="button"
                className="token-instructions-btn"
                onClick={() => setShowInstructions(!showInstructions)}
              >
                {showInstructions ? "Hide Instructions" : "How do I get my JWT token?"}
              </button>
              
              {showInstructions && (
                <div className="token-instructions-box">
                  <strong>Easy Steps to Retrieve your Cookie:</strong>
                  <ol>
                    <li>Open <strong>https://warframe.market</strong> in your browser and log in.</li>
                    <li>Press <strong>F12</strong> (or right-click anywhere and select <strong>Inspect</strong>) to open Developer Tools.</li>
                    <li>Navigate to the <strong>Application</strong> tab (on Chrome/Edge) or <strong>Storage</strong> tab (on Firefox).</li>
                    <li>Expand <strong>Cookies</strong> on the left, then select <code>https://warframe.market</code>.</li>
                    <li>Locate the cookie named <code>JWT</code> in the table.</li>
                    <li>Double-click its <strong>Value</strong> column, copy the entire string, and paste it here!</li>
                  </ol>
                </div>
              )}
            </div>
            
            {authError && <div className="auth-error">{authError}</div>}
            
            <button type="submit" className="btn-primary" disabled={authLoading}>
              {authLoading ? "Verifying Token..." : "Authenticate Core"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Update Available Premium Banner */}
      {availableUpdate && (
        <div className="update-banner">
          <div className="update-banner-content">
            <svg className="update-banner-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span className="update-banner-text">
              New version <strong>v{availableUpdate.version}</strong> is available.
            </span>
          </div>
          <button
            className="btn-update-install"
            disabled={updateInstalling}
            onClick={handleInstallUpdate}
          >
            {updateInstalling ? "Installing..." : "Install & Restart"}
          </button>
        </div>
      )}

      {/* Header bar */}
      <header className="app-header">
        <div className="header-title-group">
          <svg className="header-logo" viewBox="0 0 24 24">
            <path d="M12 2L2 22h20L12 2zm0 4l6 12H6l6-12z" />
          </svg>
          <h1 className="app-title">Tenno Syndicate Automator</h1>
        </div>
        
        <div className="user-badge">
          <span className="badge-dot"></span>
          <span>{accountName || "Authenticated Tenno"}</span>
        </div>
      </header>

      {/* Dashboard Factions Grid */}
      <section className="dashboard-grid">
        {standings.map((state) => {
          const maxCap = getMaxStanding(state.rank);
          const isPublishing = publishingFactions.has(state.faction_key);
          const listQty = Math.floor(state.standing / 25000);

          return (
            <div
              key={state.faction_key}
              className="syndicate-card"
              style={{
                "--faction-glow": `var(--color-${state.faction_key})`,
              } as React.CSSProperties}
            >
              {/* Card Header */}
              <div className="card-header">
                <div className="faction-title-group">
                  <h3 className="faction-name">{formatFactionName(state.faction_key)}</h3>
                  <span className="faction-max-info">CAPACITY: {maxCap.toLocaleString()}</span>
                </div>
                
                <div className="rank-badge-group">
                  <span className="rank-label">Rank</span>
                  <select
                    className="rank-select"
                    value={state.rank}
                    onChange={(e) => handleRankChange(state.faction_key, parseInt(e.target.value))}
                  >
                    {[0, 1, 2, 3, 4, 5].map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Slider Controller */}
              <div className="slider-container">
                <div className="slider-labels">
                  <span style={{ color: "var(--text-secondary)" }}>STANDING</span>
                  <span className="standing-value">
                    {state.standing.toLocaleString()} / {maxCap.toLocaleString()}
                  </span>
                </div>
                <input
                  type="range"
                  className="standing-slider"
                  min="0"
                  max={maxCap}
                  value={state.standing}
                  onChange={(e) => handleStandingChange(state.faction_key, parseInt(e.target.value))}
                />
              </div>

              {/* Listable count info */}
              <div className="offerings-info">
                <span className="offerings-label">LISTABLE OFFERINGS</span>
                <span className="offerings-count">{listQty > 0 ? listQty : 0}</span>
              </div>

              {/* Mod catalog preview */}
              {(() => {
                const modsList = factionMods[state.faction_key] || [];
                const isExpanded = expandedFactions.has(state.faction_key);
                return (
                  <div className="mods-preview-container">
                    <button
                      type="button"
                      className="btn-mods-toggle"
                      onClick={() => toggleFactionExpand(state.faction_key)}
                    >
                      {isExpanded ? "Hide Mod Catalog" : `View Mod Catalog (${modsList.length} items)`}
                    </button>
                    {isExpanded && (
                      <div className="mods-list-drawer">
                        {modsList.length === 0 ? (
                          <span className="no-mods-msg">No mods available at this rank level.</span>
                        ) : (
                          modsList.map((m) => (
                            <span key={m} className="mod-pill">
                              {m.replace(/_/g, " ")}
                            </span>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Faction Actions */}
              <div className="syndicate-actions">
                <button
                  className={`btn-action ${isPublishing ? "publishing" : ""}`}
                  disabled={isPublishing}
                  onClick={() => {
                    setPublishPreview({
                      factionKey: state.faction_key,
                      quantity: Math.floor(state.standing / 25000),
                      mods: factionMods[state.faction_key] || []
                    });
                  }}
                >
                  {isPublishing ? (
                    <>
                      <svg className="spinner" viewBox="0 0 24 24" style={{ width: 14, height: 14 }}>
                        <path d="M12 4V2m0 20v-2m8-8h2M2 12h2" stroke="currentColor" strokeWidth="2" />
                      </svg>
                      Updating...
                    </>
                  ) : (
                    "Publish Offerings"
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </section>

      {/* Sales Record Quick Form */}
      <section className="ledger-panel">
        <h2 className="panel-title">Record Market Transaction</h2>
        
        <div className="ledger-form">
          <div className="form-group" style={{ flex: 2 }}>
            <label htmlFor="mod-slug">Offering Item Mod</label>
            <select
              id="mod-slug"
              className="form-select"
              value={saleItem}
              onChange={(e) => setSaleItem(e.target.value)}
            >
              {allMods.map((m) => (
                <option key={m} value={m}>
                  {m.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="quantity">Sale Quantity</label>
            <input
              id="quantity"
              type="number"
              className="form-number-input"
              min="1"
              max="10"
              value={saleQty}
              onChange={(e) => setSaleQty(Math.max(1, parseInt(e.target.value) || 1))}
            />
          </div>

          <button
            className="btn-record"
            disabled={saleLoading}
            onClick={() => handleRecordSale(null)}
          >
            {saleLoading ? "Logging..." : "Log Completed Sale"}
          </button>
        </div>
      </section>

      {/* Logging Ticker Console */}
      <footer className="log-console">
        <div className="console-header">Transaction Ticker Console Logs</div>
        <div className="console-logs">
          {logs.length === 0 ? (
            <div className="log-entry" style={{ color: "#475569" }}>
              <span>[SYSTEM LOGS]</span>
              <span>No transactions executed in this session. Awaiting operations...</span>
            </div>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} className="log-entry">
                <span className="log-timestamp">[{log.timestamp}]</span>
                <span className={`log-msg ${log.type}`}>{log.message}</span>
              </div>
            ))
          )}
        </div>
      </footer>

      {/* Frosted Confirm Publish Modal */}
      {publishPreview && (
        <div className="modal-overlay">
          <div
            className="modal-content publish-confirm"
            style={{
              "--faction-glow": `var(--color-${publishPreview.factionKey})`,
            } as React.CSSProperties}
          >
            <div className="modal-header">
              <h3>Confirm Market Publication</h3>
            </div>
            
            <div className="modal-body">
              <p>
                You are about to publish active sell orders for <strong>{formatFactionName(publishPreview.factionKey)}</strong>.
              </p>
              
              {publishPreview.quantity > 0 ? (
                <div className="publish-preview-info">
                  <div className="publish-stat-box">
                    <span className="stat-label">Quantity per Mod</span>
                    <span className="stat-value">{publishPreview.quantity}</span>
                  </div>
                  <div className="publish-stat-box">
                    <span className="stat-label">Total Mods to Publish</span>
                    <span className="stat-value">{publishPreview.mods.length}</span>
                  </div>
                </div>
              ) : (
                <div className="publish-preview-info warning">
                  <p className="warning-text">
                    Your standing is <strong>{standings.find(s => s.faction_key === publishPreview.factionKey)?.standing.toLocaleString()}</strong>, which is below the 25,000 threshold.
                  </p>
                </div>
              )}

              {publishPreview.quantity > 0 ? (
                <p style={{ marginTop: "16px", marginBottom: "8px" }}>
                  The following <strong>{publishPreview.mods.length}</strong> mods will be posted or updated at the lowest active market price (undercut by 1 Platinum):
                </p>
              ) : (
                <p style={{ marginTop: "16px", marginBottom: "8px", color: "var(--color-danger)" }}>
                  All existing active listings for these <strong>{publishPreview.mods.length}</strong> mods will be <strong>DELETED</strong> from your profile:
                </p>
              )}
              
              <div className="preview-mods-list">
                {publishPreview.mods.length === 0 ? (
                  <span className="no-mods-msg">No mods available at this rank level.</span>
                ) : (
                  publishPreview.mods.map((m) => (
                    <span key={m} className="mod-pill-preview">
                      {m.replace(/_/g, " ")}
                    </span>
                  ))
                )}
              </div>

              {publishPreview.quantity > 0 && (
                <div className="preview-disclaimer">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="var(--color-gold)">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                  </svg>
                  <span>Prices are queried live from warframe.market. Standing is only deducted when you record a sale.</span>
                </div>
              )}
            </div>
            
            <div className="modal-footer" style={{ gap: "12px" }}>
              <button className="btn-secondary" onClick={() => setPublishPreview(null)}>
                Cancel
              </button>
              <button
                className="btn-action btn-confirm-publish"
                style={{
                  background: publishPreview.quantity > 0 ? "linear-gradient(135deg, var(--faction-glow) 0%, rgba(0,0,0,0.6) 100%)" : "linear-gradient(135deg, var(--color-danger) 0%, rgba(0,0,0,0.6) 100%)",
                  boxShadow: `0 0 10px var(--faction-glow)`,
                  color: "#fff",
                  border: "1px solid var(--faction-glow)",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontWeight: "bold",
                  textTransform: "uppercase",
                  fontSize: "0.85rem",
                  letterSpacing: "1px",
                  transition: "all 0.25s ease"
                }}
                onClick={() => handlePublish(publishPreview.factionKey)}
              >
                {publishPreview.quantity > 0 ? "Confirm & Publish" : "Confirm Deletion"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Frosted Attribution Overlap Modal */}
      {overlapData && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Deduction Attribution Conflict</h3>
            </div>
            
            <div className="modal-body">
              <p>
                The offering item <strong>{overlapData.itemSlug.replace(/_/g, " ")}</strong> is shared across multiple represented factions that meet the standing requirement.
              </p>
              <p style={{ marginTop: "8px" }}>
                Select which Syndicate's standing should be deducted for this transaction:
              </p>
              
              <div className="overlap-grid">
                {overlapData.eligibleFactions.map((f) => (
                  <button
                    key={f}
                    className="btn-faction-choice"
                    style={{
                      "--faction-glow": `var(--color-${f})`,
                    } as React.CSSProperties}
                    onClick={() => handleRecordSale(f)}
                  >
                    <span>{formatFactionName(f)}</span>
                  </button>
                ))}
              </div>
            </div>
            
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setOverlapData(null)}>
                Cancel Transaction
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
