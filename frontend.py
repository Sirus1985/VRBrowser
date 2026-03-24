def get_html() -> str:
    return """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>VBrowser</title>
    <style>
        :root { --bg:#1e1e1e; --panel:#252526; --border:#333; --accent:#0e639c; --text:#ccc; --green:#2da44e; --sidebar-w:320px; --sidebar-admin-w:580px; }

        /* ── Light Mode ──────────────────────────────────────── */
        body.light-mode {
            --bg: #f0f0f0;
            --panel: #ffffff;
            --border: #ccc;
            --text: #222;
        }
        body.light-mode input,
        body.light-mode select {
            background: #fff;
            border-color: #bbb;
            color: #222;
        }
        body.light-mode input.search {
            background: #f5f5f5;
            border-color: #bbb;
        }
        body.light-mode .section   { background: #e8e8e8; border-color: #ccc; }
        body.light-mode .item      { background: #ddd; }
        body.light-mode .tab       { background: #ddd; border-color: #bbb; color: #333; }
        body.light-mode .session-item { background: #ddd; }
        body.light-mode .session-item .s-meta { color: #555; }
        body.light-mode .log-table th { background: #ccc; color: #222; }
        body.light-mode .log-table td { border-bottom-color: #ccc; color: #222; }
        body.light-mode .log-table tr:hover td { background: #e0e0e0; }
        body.light-mode .log-table a { color: #0e639c; }
        body.light-mode .modal-box { background: #f5f5f5; color: #222; border-color: #ccc; }
        body.light-mode button.secondary { background: #d0d0d0; border-color: #bbb; color: #222; }
        body.light-mode h3 { color: #111; }
        body.light-mode h4 { color: #555; }
        body.light-mode hr { border-top-color: #ccc; }
        body.light-mode #placeholder { color: #999; }
        body.light-mode #content { background: #e0e0e0; }

        * { box-sizing:border-box; }
        body { background:var(--bg); color:var(--text); font-family:-apple-system,system-ui,sans-serif; display:flex; height:100vh; margin:0; overflow:hidden; }

        #sidebar {
            width: var(--sidebar-w);
            min-width: var(--sidebar-w);
            background: var(--panel);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            border-right: 1px solid var(--border);
            overflow-y: auto;
            overflow-x: hidden;
            transition: min-width 0.3s ease, width 0.3s ease, padding 0.25s ease, opacity 0.2s ease;
        }

        /* Admin-Bereich erweitert die Sidebar */
        body.admin-expanded #sidebar {
            width: var(--sidebar-admin-w);
            min-width: var(--sidebar-admin-w);
        }

        /* Collapsed hat immer Vorrang – auch über admin-expanded */
        body.sidebar-collapsed #sidebar {
            width: 0 !important;
            min-width: 0 !important;
            padding: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
            border-right: none !important;
        }

        #sidebarToggle {
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            z-index: 100;
            width: 18px;
            height: 48px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-left: none;
            border-radius: 0 6px 6px 0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #888;
            font-size: 10px;
            padding: 0;
            transition: left 0.25s ease, background 0.15s;
        }
        #sidebarToggle:hover { background: #333; color: #fff; }

        #content { flex:1; position:relative; background:#111; }
        iframe { width:100%; height:100%; border:none; display:none; }
        #placeholder { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#555; font-size:15px; }

        h3 { margin:0 0 4px 0; color:#fff; font-weight:600; }
        h4 { margin:0 0 6px 0; color:#aaa; font-size:12px; text-transform:uppercase; letter-spacing:1px; }
        input, select { padding:9px; border-radius:6px; border:1px solid #555; background:#3c3c3c; color:#fff; width:100%; font-size:14px; }
        input.search { background:#2a2a2a; border-color:#444; padding-left:30px; background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='%23888' viewBox='0 0 16 16'%3E%3Cpath d='M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398l3.85 3.85a1 1 0 0 0 1.415-1.415l-3.868-3.833zm-5.242 1.156a5 5 0 1 1 0-10 5 5 0 0 1 0 10z'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:10px center; }
        button { padding:9px; border-radius:6px; border:none; cursor:pointer; background:var(--accent); color:#fff; width:100%; font-size:14px; }
        button.green { background:var(--green); }
        button.secondary { background:#3a3d41; border:1px solid #555; }
        button.danger { background:#8b2010; }
        button.reset { background:#c0392b; }
        button.small { padding:4px 8px; font-size:12px; width:auto; }
        button:disabled { opacity:0.4; cursor:not-allowed; }
        .hidden { display:none !important; }
        .section { background:#2d2d2d; padding:12px; border:1px solid #444; border-radius:8px; display:flex; flex-direction:column; gap:8px; }
        .item { display:flex; justify-content:space-between; align-items:center; background:#333; padding:7px 10px; border-radius:6px; font-size:13px; gap:6px; }
        .item-left { display:flex; flex-direction:column; gap:3px; flex:1; min-width:0; }
        .item-name { font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .item-badges { display:flex; flex-wrap:wrap; gap:3px; }
        .item-actions { display:flex; gap:4px; flex-shrink:0; }
        .badge { padding:2px 7px; border-radius:999px; font-size:11px; font-weight:600; white-space:nowrap; }
        .badge.admin { background:#c0392b; color:#fff; }
        .badge.teamadmin { background:#dda108; color:#000; }
        .badge.team { background:#1a6b3c; color:#fff; }
        .badge.active { background:#1a6b3c; color:#fff; }
        hr { border:none; border-top:1px solid #444; margin:4px 0; }
        #status { margin-top:auto; font-size:12px; color:#888; border-top:1px solid var(--border); padding-top:10px; }
        label { display:flex; gap:8px; align-items:center; font-size:13px; }
        input[type=checkbox] { width:auto; }
        .tabs { display:flex; gap:4px; flex-wrap:wrap; }
        .tab { flex:1; padding:7px; border-radius:6px; border:1px solid #555; background:#3a3d41; color:#ccc; cursor:pointer; font-size:13px; text-align:center; }
        .tab.active { background:var(--accent); border-color:var(--accent); color:#fff; }
        .tab-content { display:none; flex-direction:column; gap:8px; }
        .tab-content.active { display:flex; }
        .filter-row { display:flex; gap:6px; }
        .filter-row input, .filter-row select { flex:1; }
        .count { font-size:11px; color:#666; text-align:right; }
        .searchable { display:flex; flex-direction:column; gap:4px; }
        .searchable select { max-height:120px; }
        .session-item { display:flex; flex-direction:column; gap:3px; background:#333; padding:8px 10px; border-radius:6px; font-size:12px; }
        .session-item .s-user { font-weight:600; color:#fff; font-size:13px; }
        .session-item .s-meta { color:#888; }
        .settings-hint { font-size:11px; color:#666; margin-top:-4px; }

        /* Logging Tab */
        .log-table { width:100%; border-collapse:collapse; font-size:13px; }
        .log-table th { background:#333; color:#fff; padding:6px 10px; text-align:left; position:sticky; top:0; }
        .log-table td { padding:6px 10px; border-bottom:1px solid #3a3a3a; }
        .log-table tr:hover td { background:#2a2a2a; }
        .log-table a { color:#7eb8f7; text-decoration:none; }
        .log-table a:hover { text-decoration:underline; }
        .log-filter-row { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
        .log-filter-row input, .log-filter-row select { flex:1; min-width:80px; }
        .log-filter-row button { width:auto; padding:7px 14px; }

        /* Detail Modal */
        #user-detail-modal {
            display:none; position:fixed; inset:0;
            background:rgba(0,0,0,0.75); z-index:9999; overflow-y:auto;
        }
        .modal-box {
            background:#1e1e1e; color:#eee; margin:40px auto;
            max-width:860px; border-radius:10px; padding:24px;
            position:relative; border:1px solid #444;
        }
        .modal-close {
            position:absolute; top:12px; right:16px;
            background:none; border:none; color:#aaa;
            font-size:1.4rem; cursor:pointer; width:auto; padding:0;
        }
        .modal-close:hover { color:#fff; }
        #detail-total { margin-top:10px; font-weight:bold; text-align:right; font-size:13px; color:#aaa; }

        /* Theme-Toggle Button */
        #themeToggleBtn {
            width:auto; padding:5px 8px; font-size:15px;
            line-height:1;
        }
        #themeToggleBtn:hover { background:#555; }
        body.light-mode #themeToggleBtn:hover { background:#bbb; }
    </style>
</head>
<body>
<div id="sidebar">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
        <h3 style="margin:0;">VBrowser</h3>
        <div style="display:flex; gap:5px; align-items:center;">
            <button class="secondary" id="themeToggleBtn" onclick="cycleTheme()" title="Dark / Light / Auto">🌙</button>
            <button class="secondary hidden" id="logoutBtn" onclick="logout()"
                    style="width:auto; padding:5px 10px; font-size:12px;">
                Logout
            </button>
        </div>
    </div>

    <div id="loginForm" class="section">
        <input id="username" placeholder="Benutzername" autocomplete="username">
        <input id="password" placeholder="Passwort" type="password" autocomplete="current-password">
        <button onclick="doLogin()">Einloggen</button>
    </div>
    <div id="sessionControls" class="hidden section">
        <button class="green" id="btnStart" onclick="startSession()">&#9654; Session starten</button>
        <button class="danger" id="btnStop" onclick="stopSession()" disabled>&#9632; Session beenden</button>
    </div>
    <div id="settingsPanel" class="hidden section">
        <h4>&#9881; Einstellungen</h4>
        <label>
            <input type="checkbox" id="autoStartCb" onchange="saveSettings()">
            Session automatisch nach Login starten
        </label>
        <hr>
        <button class="reset" onclick="resetProfile()">&#128308; Firefox-Profil zuruecksetzen</button>
        <div class="settings-hint">Loescht alle Einstellungen, Lesezeichen und den Verlauf dauerhaft.</div>
    </div>
    <div id="adminPanel" class="hidden">
        <hr>
        <button class="secondary" onclick="toggleAdmin()">&#9881; Verwaltung</button>
        <div id="adminArea" class="hidden">
            <div class="tabs" style="margin-top:8px">
                <div class="tab active" onclick="switchTab('users')">Benutzer</div>
                <div class="tab" id="teamsTabBtn" onclick="switchTab('teams')">Teams</div>
                <div class="tab" id="sessionsTabBtn" onclick="switchTab('sessions')">Sessions</div>
                <div class="tab" id="loggingTabBtn" onclick="switchTab('logging')">&#128202; Log</div>
            </div>

            <!-- TAB: Benutzer -->
            <div id="tab-users" class="tab-content active section" style="margin-top:6px">
                <h4>Benutzer</h4>
                <div class="filter-row">
                    <input class="search" id="filterUsername" placeholder="Name suchen..." oninput="renderUsers()">
                    <select id="filterTeam" onchange="renderUsers()">
                        <option value="">Alle Teams</option>
                    </select>
                </div>
                <div id="userCount" class="count"></div>
                <div id="userList"></div>
                <hr>
                <h4>Neu anlegen</h4>
                <input id="newUsername" placeholder="Benutzername">
                <input id="newPassword" placeholder="Passwort" type="password">
                <select id="newTeam"><option value="">-- Kein Team --</option></select>
                <label id="newIsAdminLabel"><input id="newIsAdmin" type="checkbox"> Superadmin</label>
                <button class="secondary" onclick="addUser()">+ User anlegen</button>
            </div>

            <!-- TAB: Teams -->
            <div id="tab-teams" class="tab-content section" style="margin-top:6px">
                <h4>Teams</h4>
                <div id="teamList"></div>
                <hr>
                <h4>Team anlegen</h4>
                <input id="newTeamName" placeholder="Teamname">
                <button class="secondary" onclick="addTeam()">+ Team anlegen</button>
                <hr>
                <h4>Team-Admin zuweisen</h4>
                <div class="searchable">
                    <input class="search" id="taTeamSearch" placeholder="Team suchen..." oninput="filterSelect('taTeam','taTeamSearch')">
                    <select id="taTeam" size="4"></select>
                </div>
                <div class="searchable">
                    <input class="search" id="taUserSearch" placeholder="User suchen..." oninput="filterSelect('taUser','taUserSearch')">
                    <select id="taUser" size="4"></select>
                </div>
                <button class="secondary" onclick="assignTeamAdmin()">+ Als Team-Admin setzen</button>
            </div>

            <!-- TAB: Aktive Sessions -->
            <div id="tab-sessions" class="tab-content section" style="margin-top:6px">
                <h4>Aktive Sessions</h4>
                <button class="secondary" onclick="loadSessions()">&#8635; Aktualisieren</button>
                <div id="sessionList"><div style="color:#666;font-size:13px">Lade...</div></div>
            </div>

            <!-- TAB: Logging / Nutzungsanalyse (nur Superadmin) -->
            <div id="tab-logging" class="tab-content section" style="margin-top:6px">
                <h4>&#128202; Nutzungsrangliste</h4>
                <div class="log-filter-row">
                    <select id="log-period" onchange="onLogPeriodChange()">
                        <option value="all">Gesamt</option>
                        <option value="day">Tag</option>
                        <option value="week">Woche</option>
                        <option value="month">Monat</option>
                        <option value="year">Jahr</option>
                    </select>
                    <input id="log-year"  type="number" placeholder="Jahr" style="display:none" onchange="loadRanking()">
                    <input id="log-month" type="number" placeholder="Monat 1-12" style="display:none" min="1" max="12" onchange="loadRanking()">
                    <input id="log-week"  type="number" placeholder="KW 1-53"    style="display:none" min="1" max="53" onchange="loadRanking()">
                    <input id="log-day"   type="date"                            style="display:none" onchange="loadRanking()">
                    <button onclick="loadRanking()" style="width:auto;padding:7px 12px;">&#8635;</button>
                </div>
                <div id="ranking-wrap" style="overflow-x:auto">
                    <table class="log-table">
                        <thead>
                            <tr>
                                <th style="width:32px">#</th>
                                <th>Nutzer</th>
                                <th style="text-align:right">Sitzungen</th>
                                <th style="text-align:right">Gesamtzeit</th>
                            </tr>
                        </thead>
                        <tbody id="ranking-body">
                            <tr><td colspan="4" style="color:#666;padding:12px">Noch nicht geladen.</td></tr>
                        </tbody>
                    </table>
                </div>
                <hr>
                <h4>&#128269; Container &#8594; Nutzer</h4>
                <div class="log-filter-row">
                    <input id="container-search-input" type="text" placeholder="Container-Name z.B. vbrowser-a1b2c3d4">
                    <button onclick="searchContainer()" style="width:auto;padding:7px 12px;">Suchen</button>
                </div>
                <div id="container-result"></div>
            </div>
            <!-- ENDE TAB Logging -->

        </div>
    </div>
    <div id="status">Bereit</div>
</div>

<div id="content">
    <button id="sidebarToggle" onclick="toggleSidebar()" title="Sidebar ein-/ausblenden (Ctrl+B)">&#9664;</button>
    <div id="placeholder">Bitte einloggen...</div>
    <iframe id="browserFrame"></iframe>

    <!-- Session-Expired Overlay -->
    <div id="sessionOverlay" style="display:none; position:absolute; inset:0;
         background:rgba(0,0,0,0.82); color:white; flex-direction:column;
         align-items:center; justify-content:center; z-index:50; gap:14px;">
        <div style="font-size:32px">&#9888;&#65039;</div>
        <div id="overlayMessage" style="font-size:15px; color:#ccc; text-align:center; max-width:300px;">
            Deine Session ist nicht mehr aktiv.
        </div>
        <button class="green" id="overlayStartBtn" onclick="restartSessionFromOverlay()"
                style="width:200px; margin-top:8px;">
            &#9654; Session starten
        </button>
    </div>

    <!-- Nutzer-Detail Modal -->
    <div id="user-detail-modal">
        <div class="modal-box">
            <button class="modal-close" onclick="closeUserDetail()">&#10005;</button>
            <h3 id="detail-title" style="margin-bottom:12px">Sitzungsdetails</h3>
            <div class="log-filter-row" style="margin-bottom:10px">
                <select id="detail-period" onchange="onDetailPeriodChange()">
                    <option value="all">Gesamt</option>
                    <option value="day">Tag</option>
                    <option value="week">Woche</option>
                    <option value="month">Monat</option>
                    <option value="year">Jahr</option>
                </select>
                <input id="detail-year"  type="number" placeholder="Jahr" style="display:none" onchange="loadUserDetail()">
                <input id="detail-month" type="number" placeholder="Monat" min="1" max="12" style="display:none" onchange="loadUserDetail()">
                <input id="detail-week"  type="number" placeholder="KW" min="1" max="53" style="display:none" onchange="loadUserDetail()">
                <input id="detail-day"   type="date" style="display:none" onchange="loadUserDetail()">
            </div>
            <div style="overflow-x:auto">
                <table class="log-table">
                    <thead>
                        <tr>
                            <th>Start</th>
                            <th>Ende</th>
                            <th style="text-align:right">Dauer</th>
                            <th>IP</th>
                            <th>Container</th>
                        </tr>
                    </thead>
                    <tbody id="detail-body"></tbody>
                </table>
            </div>
            <div id="detail-total"></div>
        </div>
    </div>

</div>


<script>
let token = localStorage.getItem("token");
let currentUser = JSON.parse(localStorage.getItem("currentUser") || "null");
let allUsers = [], allTeams = [], teamAdminMap = {};
let currentSessionId = null;
let healthCheckInterval = null;

if (token && currentUser) showSessionUI();


// ── Theme (Dark / Light / Auto) ────────────────────────────────
const _themes     = ['dark', 'light', 'auto'];
const _themeIcons = { dark: '🌙', light: '☀️', auto: '🖥' };

function applyTheme(mode) {
    document.body.classList.remove('light-mode');
    if (mode === 'light') {
        document.body.classList.add('light-mode');
    } else if (mode === 'auto') {
        if (!window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.classList.add('light-mode');
        }
    }
    const btn = document.getElementById('themeToggleBtn');
    if (btn) btn.textContent = _themeIcons[mode];
    localStorage.setItem('theme', mode);
}

function cycleTheme() {
    const current = localStorage.getItem('theme') || 'dark';
    const next = _themes[(_themes.indexOf(current) + 1) % 3];
    applyTheme(next);
}

applyTheme(localStorage.getItem('theme') || 'dark');

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if ((localStorage.getItem('theme') || 'dark') === 'auto') applyTheme('auto');
});


// ── Sidebar Toggle ──────────────────────────────────────────────
// Merkt sich ob admin-expanded war, bevor die Sidebar eingeklappt wurde
let _adminWasExpanded = false;

function toggleSidebar() {
    const willCollapse = !document.body.classList.contains("sidebar-collapsed");
    if (willCollapse) {
        // Einfahren: admin-expanded-Zustand merken und entfernen
        _adminWasExpanded = document.body.classList.contains("admin-expanded");
        document.body.classList.remove("admin-expanded");
        document.body.classList.add("sidebar-collapsed");
        document.getElementById("sidebarToggle").innerHTML = "&#9654;";
    } else {
        // Ausfahren: sidebar-collapsed entfernen, admin-expanded ggf. wiederherstellen
        document.body.classList.remove("sidebar-collapsed");
        if (_adminWasExpanded) document.body.classList.add("admin-expanded");
        document.getElementById("sidebarToggle").innerHTML = "&#9664;";
    }
    localStorage.setItem("sidebarCollapsed", willCollapse ? "1" : "0");
}

if (localStorage.getItem("sidebarCollapsed") === "1") {
    document.body.classList.add("sidebar-collapsed");
    document.getElementById("sidebarToggle").innerHTML = "&#9654;";
}
document.addEventListener("keydown", e => {
    if (e.ctrlKey && e.key === "b") { e.preventDefault(); toggleSidebar(); }
});


// ── Session State ───────────────────────────────────────────────
function setSessionState(running) {
    document.getElementById("btnStart").disabled = running;
    document.getElementById("btnStop").disabled = !running;
}

function setStatus(msg, isError=false) {
    const el = document.getElementById("status");
    el.textContent = msg;
    el.style.color = isError ? "#f66" : "#888";
}

function setButtons(disabled) {
    document.querySelectorAll("button").forEach(b => {
        if (!b.classList.contains("small") && b.id !== "btnStart" && b.id !== "btnStop") {
            b.disabled = disabled;
        }
    });
}

async function api(path, method="GET", body=null) {
    const opts = { method, headers: { "Authorization": `Bearer ${token}` } };
    if (body) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
    const res = await fetch(path, opts);
    if (!res.ok) { const e = await res.json().catch(()=>({detail:"Fehler"})); throw new Error(e.detail||"Fehler"); }
    return res.json();
}

// ── Enter-Taste im Login ────────────────────────────────────────
document.getElementById("username").addEventListener("keydown", e => {
    if (e.key === "Enter") document.getElementById("password").focus();
});
document.getElementById("password").addEventListener("keydown", e => {
    if (e.key === "Enter") doLogin();
});


// ── Login ───────────────────────────────────────────────────────
async function doLogin() {
    setButtons(true);
    const u = document.getElementById("username").value;
    const p = document.getElementById("password").value;
    setStatus("Logge ein...");
    try {
        const res = await fetch("/api/login", {
            method: "POST", headers: {"Content-Type":"application/json"},
            body: JSON.stringify({username:u, password:p})
        });
        if (!res.ok) throw new Error("Login fehlgeschlagen");
        const data = await res.json();
        token = data.token; currentUser = data;
        localStorage.setItem("token", token);
        localStorage.setItem("currentUser", JSON.stringify(data));
        showSessionUI();
        setStatus("Eingeloggt als " + u);
        if (data.auto_start_session) {
            setTimeout(() => startSession(), 500);
        }
    } catch(e) { setStatus(e.message, true); }
    setButtons(false);
}

function showSessionUI() {
    document.getElementById("loginForm").classList.add("hidden");
    document.getElementById("sessionControls").classList.remove("hidden");
    document.getElementById("settingsPanel").classList.remove("hidden");
    document.getElementById("logoutBtn").classList.remove("hidden");
    document.getElementById("placeholder").textContent = "";
    const isAdmin = currentUser?.isadmin;
    const isTeamAdmin = currentUser?.admin_teams?.length > 0;
    if (isAdmin || isTeamAdmin) {
        document.getElementById("adminPanel").classList.remove("hidden");
        document.getElementById("teamsTabBtn").classList.toggle("hidden", !isAdmin);
        document.getElementById("sessionsTabBtn").classList.toggle("hidden", !isAdmin);
        document.getElementById("loggingTabBtn").classList.toggle("hidden", !isAdmin);
        document.getElementById("newIsAdminLabel").classList.toggle("hidden", !isAdmin);
    }
    loadSettings();
}

async function loadSettings() {
    try {
        const data = await api("/api/user/settings");
        document.getElementById("autoStartCb").checked = !!data.auto_start_session;
    } catch(e) {}
}

async function saveSettings() {
    const auto = document.getElementById("autoStartCb").checked;
    try {
        await api("/api/user/settings", "PATCH", { auto_start_session: auto });
        setStatus("Einstellungen gespeichert");
    } catch(e) { setStatus(e.message, true); }
}

async function resetProfile() {
    if (!confirm("Wirklich das Firefox-Profil zuruecksetzen? Alle Lesezeichen und Einstellungen werden geloescht!")) return;
    setButtons(true);
    setStatus("Setze Profil zurueck...");
    try {
        await api("/api/session/reset", "POST");
        document.getElementById("browserFrame").src = "";
        document.getElementById("browserFrame").style.display = "none";
        document.getElementById("placeholder").style.display = "flex";
        document.getElementById("placeholder").textContent = "Profil zurueckgesetzt. Neue Session starten.";
        setStatus("Profil zurueckgesetzt");
        setSessionState(false);
        stopHealthPolling();
        currentSessionId = null;
    } catch(e) { setStatus(e.message, true); }
    setButtons(false);
}

// ── Session Start / Stop ────────────────────────────────────────
async function startSession() {
    setButtons(true);
    setStatus("Starte Container...");
    try {
        const data = await api("/api/session/start", "POST");
        currentSessionId = data.session_id ?? "active";
        setStatus("Lade Browser...");
        const cookieFrame = document.createElement("iframe");
        cookieFrame.style.display = "none";
        const browserHost = new URL(data.url).host;
        cookieFrame.src = `https://${browserHost}/auth/set-cookie`
            + `?token=${encodeURIComponent(data.token)}`
            + `&redirect=${encodeURIComponent(data.url)}`;
        document.body.appendChild(cookieFrame);
        setTimeout(() => {
            document.body.removeChild(cookieFrame);
            const frame = document.getElementById("browserFrame");
            frame.src = data.url;
            frame.style.display = "block";
            document.getElementById("placeholder").style.display = "none";
            document.getElementById("sessionOverlay").style.display = "none";
            setStatus("Browser laeuft");
            setSessionState(true);
            setButtons(false);
            startHealthPolling();
            if (!document.body.classList.contains("sidebar-collapsed")) toggleSidebar();
        }, 5000);
    } catch(e) {
        setStatus(e.message, true);
        setButtons(false);
    }
}

async function stopSession() {
    stopHealthPolling();
    currentSessionId = null;
    setButtons(true);
    try {
        await api("/api/session/stop", "POST");
        document.getElementById("browserFrame").src = "";
        document.getElementById("browserFrame").style.display = "none";
        document.getElementById("sessionOverlay").style.display = "none";
        document.getElementById("placeholder").style.display = "flex";
        document.getElementById("placeholder").textContent = "Session beendet";
        setStatus("Session gestoppt");
        setSessionState(false);
    } catch(e) { setStatus(e.message, true); }
    setButtons(false);
}

async function logout() {
    stopHealthPolling();
    currentSessionId = null;
    setStatus("Trenne Session...");
    if (!document.getElementById("btnStop").disabled) {
        try { await api("/api/session/stop", "POST"); } catch(e) {}
    }
    localStorage.clear();
    location.reload();
}


// ── Session Health Check ────────────────────────────────────────
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && currentSessionId) {
        pollSessionHealth();
        startHealthPolling();
    } else {
        stopHealthPolling();
    }
});

function startHealthPolling() {
    stopHealthPolling();
    healthCheckInterval = setInterval(pollSessionHealth, 30000);
}

function stopHealthPolling() {
    if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
        healthCheckInterval = null;
    }
}

async function pollSessionHealth() {
    if (!currentSessionId) return;
    try {
        const res = await fetch("/api/session/status", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) { showSessionOverlay("Session nicht mehr erreichbar."); return; }
        const data = await res.json();
        if (!data.running) showSessionOverlay("Deine Session ist abgelaufen oder wurde beendet.");
    } catch {
        showSessionOverlay("Verbindung zum Server verloren.");
    }
}

function showSessionOverlay(msg) {
    stopHealthPolling();
    currentSessionId = null;
    document.getElementById("browserFrame").style.display = "none";
    document.getElementById("overlayMessage").textContent = msg;
    const btn = document.getElementById("overlayStartBtn");
    btn.disabled = false;
    btn.textContent = "▶ Session starten";
    document.getElementById("sessionOverlay").style.display = "flex";
    setSessionState(false);
    setStatus("Session inaktiv", true);
    if (document.body.classList.contains("sidebar-collapsed")) toggleSidebar();
}

async function restartSessionFromOverlay() {
    const btn = document.getElementById("overlayStartBtn");
    btn.disabled = true;
    btn.textContent = "⏳ Starte...";
    document.getElementById("sessionOverlay").style.display = "none";
    await startSession();
}

// ── Admin Bereich ───────────────────────────────────────────────
function switchTab(tab) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(el => el.classList.remove("active"));
    document.getElementById("tab-" + tab).classList.add("active");
    const tabNames = ["users", "teams", "sessions", "logging"];
    const tabBtns  = document.querySelectorAll(".tab");
    const idx = tabNames.indexOf(tab);
    if (tabBtns[idx]) tabBtns[idx].classList.add("active");
    if (tab === "users")    loadUsers();
    if (tab === "teams")    loadTeams();
    if (tab === "sessions") loadSessions();
    if (tab === "logging")  loadRanking();
}

function toggleAdmin() {
    const area = document.getElementById("adminArea");
    area.classList.toggle("hidden");
    const expanded = !area.classList.contains("hidden");
    document.body.classList.toggle("admin-expanded", expanded);
    // Auch _adminWasExpanded aktualisieren damit toggleSidebar den Zustand kennt
    _adminWasExpanded = expanded;
    if (expanded) {
        loadUsers();
        if (currentUser?.isadmin) loadTeams();
    }
}

async function loadUsers() {
    try {
        allUsers = await api("/api/users");
        allTeams = currentUser?.isadmin ? await api("/api/teams") : (currentUser?.admin_teams || []);
        teamAdminMap = {};
        if (currentUser?.isadmin) {
            for (const team of allTeams) {
                const admins = await api(`/api/teams/${team.id}/admins`);
                for (const a of admins) {
                    if (!teamAdminMap[a.id]) teamAdminMap[a.id] = [];
                    teamAdminMap[a.id].push(team);
                }
            }
        }
        const filterTeam = document.getElementById("filterTeam");
        filterTeam.innerHTML = "<option value=''>Alle Teams</option>";
        allTeams.forEach(t => filterTeam.innerHTML += `<option value="${t.id}">${t.name}</option>`);
        const newTeamSel = document.getElementById("newTeam");
        newTeamSel.innerHTML = "<option value=''>-- Kein Team --</option>";
        allTeams.forEach(t => newTeamSel.innerHTML += `<option value="${t.id}">${t.name}</option>`);
        renderUsers();
    } catch(e) { setStatus(e.message, true); }
}

function renderUsers() {
    const filterName   = document.getElementById("filterUsername").value.toLowerCase();
    const filterTeamId = document.getElementById("filterTeam").value;
    const filtered = allUsers.filter(u => {
        const matchName = u.username.toLowerCase().includes(filterName);
        const matchTeam = !filterTeamId || String(u.team_id) === filterTeamId;
        return matchName && matchTeam;
    });
    document.getElementById("userCount").textContent = `${filtered.length} von ${allUsers.length} Benutzer`;
    document.getElementById("userList").innerHTML = filtered.length === 0
        ? "<div style='color:#666;font-size:13px'>Keine Treffer</div>"
        : filtered.map(u => {
            const teamName   = allTeams.find(t => t.id === u.team_id)?.name || "";
            const adminTeams = teamAdminMap[u.id] || [];
            return `<div class="item">
                <div class="item-left">
                    <div class="item-name">${u.username}</div>
                    <div class="item-badges">
                        ${u.isadmin ? '<span class="badge admin">SUPER</span>' : ''}
                        ${teamName ? `<span class="badge team">${teamName}</span>` : ''}
                        ${adminTeams.map(t => `<span class="badge teamadmin">Admin: ${t.name}</span>`).join('')}
                    </div>
                </div>
                <div class="item-actions">
                    ${u.username !== "admin" && !u.isadmin
                        ? `<button class="danger small" onclick="deleteUser(${u.id})">&#10005;</button>` : ''}
                </div>
            </div>`;
        }).join("");
}

async function addUser() {
    const username = document.getElementById("newUsername").value.trim();
    const password = document.getElementById("newPassword").value.trim();
    const team_id  = document.getElementById("newTeam").value || null;
    const isadmin  = document.getElementById("newIsAdmin")?.checked || false;
    if (!username || !password) return setStatus("Bitte Benutzername und Passwort eingeben", true);
    try {
        await api("/api/users", "POST", { username, password, isadmin, team_id: team_id ? parseInt(team_id) : null });
        document.getElementById("newUsername").value = "";
        document.getElementById("newPassword").value = "";
        if (document.getElementById("newIsAdmin")) document.getElementById("newIsAdmin").checked = false;
        loadUsers();
        setStatus("User angelegt: " + username);
    } catch(e) { setStatus(e.message, true); }
}

async function deleteUser(id) {
    if (!confirm("User wirklich loeschen?")) return;
    try {
        await api(`/api/users/${id}`, "DELETE");
        loadUsers();
        setStatus("User geloescht");
    } catch(e) { setStatus(e.message, true); }
}

async function loadTeams() {
    try {
        const teams = await api("/api/teams");
        document.getElementById("teamList").innerHTML = teams.length === 0
            ? "<div style='color:#666;font-size:13px'>Keine Teams</div>"
            : teams.map(t => `<div class="item">
                <div class="item-left"><div class="item-name">${t.name}</div></div>
                <button class="danger small" onclick="deleteTeam(${t.id})">&#10005;</button>
            </div>`).join("");
        const taTeam = document.getElementById("taTeam");
        taTeam.innerHTML = "";
        teams.forEach(t => taTeam.innerHTML += `<option value="${t.id}">${t.name}</option>`);
        taTeam._allOptions = Array.from(taTeam.options).map(o => ({v:o.value, t:o.text}));
        const allU   = await api("/api/users");
        const taUser = document.getElementById("taUser");
        taUser.innerHTML = "";
        allU.filter(u => !u.isadmin).forEach(u => taUser.innerHTML += `<option value="${u.id}">${u.username}</option>`);
        taUser._allOptions = Array.from(taUser.options).map(o => ({v:o.value, t:o.text}));
    } catch(e) { setStatus(e.message, true); }
}

function filterSelect(selectId, searchId) {
    const sel   = document.getElementById(selectId);
    const query = document.getElementById(searchId).value.toLowerCase();
    if (!sel._allOptions) return;
    sel.innerHTML = "";
    sel._allOptions.filter(o => o.t.toLowerCase().includes(query)).forEach(o => {
        const opt = document.createElement("option");
        opt.value = o.v; opt.text = o.t;
        sel.appendChild(opt);
    });
}

async function addTeam() {
    const name = document.getElementById("newTeamName").value.trim();
    if (!name) return setStatus("Bitte Teamname eingeben", true);
    try {
        await api("/api/teams", "POST", {name});
        document.getElementById("newTeamName").value = "";
        loadTeams(); loadUsers();
        setStatus("Team angelegt: " + name);
    } catch(e) { setStatus(e.message, true); }
}

async function deleteTeam(id) {
    if (!confirm("Team wirklich loeschen?")) return;
    try {
        await api(`/api/teams/${id}`, "DELETE");
        loadTeams(); loadUsers();
        setStatus("Team geloescht");
    } catch(e) { setStatus(e.message, true); }
}

async function assignTeamAdmin() {
    const team_id = parseInt(document.getElementById("taTeam").value);
    const user_id = parseInt(document.getElementById("taUser").value);
    if (!team_id || !user_id) return setStatus("Bitte Team und User waehlen", true);
    try {
        await api(`/api/teams/${team_id}/admins`, "POST", {user_id});
        loadUsers();
        setStatus("Team-Admin zugewiesen");
    } catch(e) { setStatus(e.message, true); }
}

async function loadSessions() {
    try {
        const sessions = await api("/api/sessions");
        if (sessions.length === 0) {
            document.getElementById("sessionList").innerHTML =
                "<div style='color:#666;font-size:13px'>Keine aktiven Sessions</div>";
            return;
        }
        document.getElementById("sessionList").innerHTML = sessions.map(s => {
            const since    = new Date(s.created_at * 1000).toLocaleString('de-DE');
            const lastSeen = new Date(s.last_seen * 1000).toLocaleTimeString('de-DE');
            return `<div class="session-item">
                <div class="s-user">&#128100; ${s.username} <span class="badge active">&#9679; aktiv</span></div>
                <div class="s-meta">Container: ${s.container_name}</div>
                <div class="s-meta">IP: ${s.container_ip || '–'}</div>
                <div class="s-meta">Gestartet: ${since}</div>
                <div class="s-meta">Zuletzt aktiv: ${lastSeen}</div>
            </div>`;
        }).join("");
    } catch(e) { setStatus(e.message, true); }
}


// ══════════════════════════════════════════════════════════════════
// LOGGING / NUTZUNGSANALYSE
// ══════════════════════════════════════════════════════════════════

function fmtDuration(sec) {
    sec = Math.round(sec || 0);
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

function fmtTs(ts) {
    return new Date(ts * 1000).toLocaleString("de-DE");
}

function buildLogParams(prefix) {
    const period = document.getElementById(prefix + "period").value;
    const p = new URLSearchParams({ period });
    if (period === "day")   { p.set("day",   document.getElementById(prefix + "day").value); }
    if (period === "week")  { p.set("year",  document.getElementById(prefix + "year").value);
                              p.set("week",  document.getElementById(prefix + "week").value); }
    if (period === "month") { p.set("year",  document.getElementById(prefix + "year").value);
                              p.set("month", document.getElementById(prefix + "month").value); }
    if (period === "year")  { p.set("year",  document.getElementById(prefix + "year").value); }
    return p;
}

function showPeriodFields(prefix) {
    const period = document.getElementById(prefix + "period").value;
    document.getElementById(prefix + "year").style.display  = ["week","month","year"].includes(period) ? "" : "none";
    document.getElementById(prefix + "month").style.display = period === "month" ? "" : "none";
    document.getElementById(prefix + "week").style.display  = period === "week"  ? "" : "none";
    document.getElementById(prefix + "day").style.display   = period === "day"   ? "" : "none";
}

function onLogPeriodChange()    { showPeriodFields("log-");    loadRanking(); }
function onDetailPeriodChange() { showPeriodFields("detail-"); loadUserDetail(); }

async function loadRanking() {
    const params = buildLogParams("log-");
    const tbody  = document.getElementById("ranking-body");
    tbody.innerHTML = "<tr><td colspan='4' style='color:#666;padding:10px'>Lade...</td></tr>";
    try {
        const data = await api("/api/admin/logging/ranking?" + params);
        if (!data.length) {
            tbody.innerHTML = "<tr><td colspan='4' style='color:#666;padding:10px'>Keine Daten fuer diesen Zeitraum.</td></tr>";
            return;
        }
        tbody.innerHTML = data.map((row, i) => `
            <tr>
                <td>${i + 1}</td>
                <td><a href="#" onclick="openUserDetail(${row.user_id},'${row.username}');return false">${row.username}</a></td>
                <td style="text-align:right">${row.session_count}</td>
                <td style="text-align:right">${fmtDuration(row.total_seconds)}</td>
            </tr>`).join("");
    } catch(e) {
        tbody.innerHTML = `<tr><td colspan='4' style='color:#f66;padding:10px'>${e.message}</td></tr>`;
    }
}

// ── Nutzer-Detail Modal ─────────────────────────────────────────
let _detailUserId   = null;
let _detailUsername = "";

async function openUserDetail(userId, username) {
    _detailUserId   = userId;
    _detailUsername = username;
    document.getElementById("detail-title").textContent = `Sitzungen: ${username}`;
    document.getElementById("detail-period").value = "all";
    showPeriodFields("detail-");
    document.getElementById("user-detail-modal").style.display = "block";
    await loadUserDetail();
}

function closeUserDetail() {
    document.getElementById("user-detail-modal").style.display = "none";
}

document.getElementById("user-detail-modal").addEventListener("click", function(e) {
    if (e.target === this) closeUserDetail();
});

async function loadUserDetail() {
    if (!_detailUserId) return;
    const params = buildLogParams("detail-");
    const tbody  = document.getElementById("detail-body");
    tbody.innerHTML = "<tr><td colspan='4' style='color:#666;padding:10px'>Lade...</td></tr>";
    document.getElementById("detail-total").textContent = "";
    try {
        const data = await api(`/api/admin/logging/user/${_detailUserId}?` + params);
        if (!data.length) {
            tbody.innerHTML = "<tr><td colspan='4' style='color:#666;padding:10px'>Keine Sitzungen gefunden.</td></tr>";
            return;
        }
        let totalSec = 0;
        tbody.innerHTML = data.map(row => {
            totalSec += row.duration || 0;
            return `<tr>
                <td>${fmtTs(row.started_at)}</td>
                <td>${fmtTs(row.ended_at)}</td>
                <td style="text-align:right">${fmtDuration(row.duration)}</td>
                <td style="color:#666;font-size:11px">${row.container_ip || '–'}</td>
                <td style="font-family:monospace;font-size:12px">${row.container_name}</td>
            </tr>`;
        }).join("");
        document.getElementById("detail-total").textContent =
            `Gesamt: ${data.length} Sitzung(en) · ${fmtDuration(totalSec)}`;
    } catch(e) {
        tbody.innerHTML = `<tr><td colspan='4' style='color:#f66;padding:10px'>${e.message}</td></tr>`;
    }
}

// ── Container-Suche ─────────────────────────────────────────────
async function searchContainer() {
    const name = document.getElementById("container-search-input").value.trim();
    const div  = document.getElementById("container-result");
    if (!name) { div.innerHTML = "<span style='color:#888;font-size:13px'>Bitte Container-Namen eingeben.</span>"; return; }
    div.innerHTML = "<span style='color:#666;font-size:13px'>Suche...</span>";
    try {
        const data = await api(`/api/admin/logging/container/${encodeURIComponent(name)}`);
        if (!data.length) {
            div.innerHTML = `<span style='color:#888;font-size:13px'>Kein Nutzer fuer <code>${name}</code> gefunden.</span>`;
            return;
        }
        div.innerHTML = `<table class="log-table" style="margin-top:6px">
            <thead><tr><th>Nutzer</th><th style="text-align:right">Sitzungen</th><th style="text-align:right">Gesamtzeit</th></tr></thead>
            <tbody>${data.map(r => `
                <tr>
                    <td><a href="#" onclick="openUserDetail(${r.user_id},'${r.username}');return false">${r.username}</a></td>
                    <td style="text-align:right">${r.session_count}</td>
                    <td style="text-align:right">${fmtDuration(r.total_seconds)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`;
    } catch(e) {
        div.innerHTML = `<span style='color:#f66;font-size:13px'>${e.message}</span>`;
    }
}

document.getElementById("container-search-input").addEventListener("keydown", e => {
    if (e.key === "Enter") searchContainer();
});

</script>
</body>
</html>
"""
