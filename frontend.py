def get_html() -> str:
    return """<!DOCTYPE html>
<html lang="de" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VBrowser</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..700&display=swap" rel="stylesheet">
<style>
/* ── Design Tokens ─────────────────────────────────────── */
:root {
  --font-body: 'Inter', system-ui, sans-serif;
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
  --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.75vw, 1.5rem);
  --text-xl: clamp(1.5rem, 1.2rem + 1.25vw, 2.25rem);
  --space-1:.25rem;--space-2:.5rem;--space-3:.75rem;--space-4:1rem;
  --space-5:1.25rem;--space-6:1.5rem;--space-8:2rem;--space-10:2.5rem;
  --space-12:3rem;--space-16:4rem;
  --radius-sm:.375rem;--radius-md:.5rem;--radius-lg:.75rem;
  --radius-xl:1rem;--radius-full:9999px;
  --transition: 180ms cubic-bezier(0.16,1,0.3,1);
}
[data-theme="light"] {
  --bg:#f7f6f2;--surface:#f9f8f5;--surface-2:#fbfbf9;
  --surface-offset:#f3f0ec;--surface-dynamic:#e6e4df;
  --border:#d4d1ca;--divider:#dcd9d5;
  --text:#28251d;--text-muted:#7a7974;--text-faint:#bab9b4;--text-inv:#f9f8f4;
  --primary:#01696f;--primary-h:#0c4e54;--primary-hl:#cedcd8;
  --success:#437a22;--success-hl:#d4dfcc;
  --error:#a12c7b;--error-hl:#e0ced7;
  --warning:#964219;--warning-hl:#ddcfc6;
  --shadow-sm:0 1px 2px oklch(0.2 0.01 80/0.06);
  --shadow-md:0 4px 12px oklch(0.2 0.01 80/0.08);
  --shadow-lg:0 12px 32px oklch(0.2 0.01 80/0.12);
}
[data-theme="dark"] {
  --bg:#171614;--surface:#1c1b19;--surface-2:#201f1d;
  --surface-offset:#1d1c1a;--surface-dynamic:#2d2c2a;
  --border:#393836;--divider:#262523;
  --text:#cdccca;--text-muted:#797876;--text-faint:#5a5957;--text-inv:#2b2a28;
  --primary:#4f98a3;--primary-h:#227f8b;--primary-hl:#313b3b;
  --success:#6daa45;--success-hl:#3a4435;
  --error:#d163a7;--error-hl:#4c3d46;
  --warning:#bb653b;--warning-hl:#564942;
  --shadow-sm:0 1px 2px oklch(0 0 0/0.2);
  --shadow-md:0 4px 12px oklch(0 0 0/0.3);
  --shadow-lg:0 12px 32px oklch(0 0 0/0.4);
}

/* ── Reset ─────────────────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
body{min-height:100dvh;font-family:var(--font-body);font-size:var(--text-base);
  color:var(--text);background:var(--bg);line-height:1.6}
input,button,select,textarea{font:inherit;color:inherit}
button{cursor:pointer;background:none;border:none}
table{border-collapse:collapse;width:100%}
a,button,[role="button"],input,select,textarea{
  transition:color var(--transition),background var(--transition),
    border-color var(--transition),box-shadow var(--transition)}
:focus-visible{outline:2px solid var(--primary);outline-offset:3px;border-radius:var(--radius-sm)}

/* ── Layout ────────────────────────────────────────────── */
.app{display:flex;flex-direction:column;min-height:100dvh}
.topbar{
  display:flex;align-items:center;justify-content:space-between;
  padding:var(--space-3) var(--space-6);
  background:var(--surface);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100;
  box-shadow:var(--shadow-sm)
}
.topbar-logo{display:flex;align-items:center;gap:var(--space-3);font-weight:600;font-size:var(--text-base)}
.topbar-right{display:flex;align-items:center;gap:var(--space-4)}
.main{flex:1;padding:var(--space-8) var(--space-6);max-width:1280px;margin-inline:auto;width:100%}

/* ── Buttons ───────────────────────────────────────────── */
.btn{
  display:inline-flex;align-items:center;gap:var(--space-2);
  padding:var(--space-2) var(--space-4);border-radius:var(--radius-md);
  font-size:var(--text-sm);font-weight:500;white-space:nowrap;
  border:1px solid transparent;min-height:36px
}
.btn-primary{background:var(--primary);color:var(--text-inv);border-color:var(--primary)}
.btn-primary:hover{background:var(--primary-h);border-color:var(--primary-h)}
.btn-secondary{background:transparent;color:var(--text);border-color:var(--border)}
.btn-secondary:hover{background:var(--surface-offset)}
.btn-ghost{background:transparent;color:var(--text-muted)}
.btn-ghost:hover{background:var(--surface-offset);color:var(--text)}
.btn-danger{background:var(--error);color:var(--text-inv);border-color:var(--error)}
.btn-danger:hover{filter:brightness(1.1)}
.btn-sm{padding:var(--space-1) var(--space-3);font-size:var(--text-xs);min-height:28px}
.btn-icon{padding:var(--space-2);min-height:36px;width:36px;justify-content:center;border-radius:var(--radius-md)}

/* ── Cards ─────────────────────────────────────────────── */
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-lg);padding:var(--space-6);
  box-shadow:var(--shadow-sm)
}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(280px,100%),1fr));gap:var(--space-4)}

/* Container-Kachel (Nutzer) */
.container-card{
  background:var(--surface);border:2px solid var(--border);
  border-radius:var(--radius-lg);padding:var(--space-6);
  cursor:pointer;transition:border-color var(--transition),box-shadow var(--transition);
  position:relative
}
.container-card:hover{border-color:var(--primary);box-shadow:var(--shadow-md)}
.container-card.selected{border-color:var(--primary);background:color-mix(in oklch,var(--primary) 6%,var(--surface))}
.container-card .default-badge{
  position:absolute;top:var(--space-3);right:var(--space-3);
  background:var(--primary);color:var(--text-inv);
  font-size:var(--text-xs);padding:2px var(--space-2);
  border-radius:var(--radius-full);font-weight:600
}
.container-card h3{font-size:var(--text-base);font-weight:600;margin-bottom:var(--space-1)}
.container-card p{font-size:var(--text-sm);color:var(--text-muted);margin-bottom:var(--space-3)}
.container-card .meta{display:flex;gap:var(--space-2);flex-wrap:wrap}
.tag{font-size:var(--text-xs);padding:2px var(--space-2);border-radius:var(--radius-full);
  background:var(--surface-offset);color:var(--text-muted);border:1px solid var(--border)}

/* ── Tabs ──────────────────────────────────────────────── */
.tabs{display:flex;gap:var(--space-1);border-bottom:1px solid var(--border);margin-bottom:var(--space-6)}
.tab-btn{
  padding:var(--space-2) var(--space-4);font-size:var(--text-sm);font-weight:500;
  color:var(--text-muted);border-bottom:2px solid transparent;
  background:none;border-radius:0;margin-bottom:-1px;
  transition:color var(--transition),border-color var(--transition)
}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{color:var(--primary);border-bottom-color:var(--primary)}
.tab-panel{display:none}.tab-panel.active{display:block}

/* ── Tabelle ───────────────────────────────────────────── */
.table-wrap{overflow-x:auto;border-radius:var(--radius-lg);border:1px solid var(--border)}
table th,table td{padding:var(--space-3) var(--space-4);text-align:left;font-size:var(--text-sm);
  border-bottom:1px solid var(--divider)}
table th{background:var(--surface-offset);font-weight:600;color:var(--text-muted);font-size:var(--text-xs);
  text-transform:uppercase;letter-spacing:0.05em}
table tr:last-child td{border-bottom:none}
table tbody tr:hover{background:var(--surface-offset)}

/* ── Forms ─────────────────────────────────────────────── */
.form-group{display:flex;flex-direction:column;gap:var(--space-1);margin-bottom:var(--space-4)}
.form-group label{font-size:var(--text-sm);font-weight:500;color:var(--text-muted)}
.form-control{
  width:100%;padding:var(--space-2) var(--space-3);
  background:var(--surface-2);border:1px solid var(--border);
  border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--text)
}
.form-control:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px color-mix(in oklch,var(--primary) 20%,transparent)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4)}
.form-hint{font-size:var(--text-xs);color:var(--text-faint)}

/* ── Modal ─────────────────────────────────────────────── */
.modal-backdrop{
  display:none;position:fixed;inset:0;background:oklch(0 0 0/0.5);
  z-index:200;align-items:center;justify-content:center;padding:var(--space-4)
}
.modal-backdrop.open{display:flex}
.modal{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-xl);padding:var(--space-8);
  max-width:640px;width:100%;max-height:90vh;overflow-y:auto;
  box-shadow:var(--shadow-lg)
}
.modal-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-6)}
.modal-header h2{font-size:var(--text-lg);font-weight:600}
.modal-footer{display:flex;justify-content:flex-end;gap:var(--space-3);margin-top:var(--space-6);
  padding-top:var(--space-6);border-top:1px solid var(--divider)}

/* ── ENV-Editor ────────────────────────────────────────── */
.env-list{display:flex;flex-direction:column;gap:var(--space-2);margin-bottom:var(--space-3)}
.env-row{display:grid;grid-template-columns:1fr 1fr auto auto;gap:var(--space-2);align-items:center}
.env-row input{padding:var(--space-2);background:var(--surface-2);border:1px solid var(--border);
  border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--text);width:100%}
.env-row input:focus{outline:none;border-color:var(--primary)}
.masked-toggle{display:flex;align-items:center;gap:var(--space-1);font-size:var(--text-xs);
  color:var(--text-muted);white-space:nowrap}
.masked-toggle input[type=checkbox]{accent-color:var(--primary)}

/* ── Status-Badges ─────────────────────────────────────── */
.badge{display:inline-flex;align-items:center;gap:4px;padding:2px var(--space-2);
  border-radius:var(--radius-full);font-size:var(--text-xs);font-weight:500}
.badge-green{background:var(--success-hl);color:var(--success)}
.badge-red{background:var(--error-hl);color:var(--error)}
.badge-yellow{background:var(--warning-hl);color:var(--warning)}
.badge-blue{background:var(--primary-hl);color:var(--primary)}
.dot{width:6px;height:6px;border-radius:50%;background:currentColor}

/* ── Sessions ──────────────────────────────────────────── */
.session-card{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
  padding:var(--space-4);display:flex;align-items:center;
  justify-content:space-between;gap:var(--space-4);flex-wrap:wrap
}
.session-info{display:flex;flex-direction:column;gap:var(--space-1)}
.session-actions{display:flex;gap:var(--space-2)}

/* ── Login ─────────────────────────────────────────────── */
#login-view{display:flex;align-items:center;justify-content:center;min-height:100dvh;
  background:var(--bg)}
.login-box{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-xl);
  padding:var(--space-10);width:100%;max-width:400px;box-shadow:var(--shadow-lg)}
.login-logo{display:flex;align-items:center;justify-content:center;gap:var(--space-3);
  margin-bottom:var(--space-8)}
.login-logo span{font-size:var(--text-lg);font-weight:700}
.login-error{background:var(--error-hl);color:var(--error);padding:var(--space-3);
  border-radius:var(--radius-md);font-size:var(--text-sm);margin-bottom:var(--space-4);display:none}

/* ── KPI Strip ─────────────────────────────────────────── */
.kpi-strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));
  gap:var(--space-4);margin-bottom:var(--space-6)}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
  padding:var(--space-4)}
.kpi-val{font-size:var(--text-xl);font-weight:700;font-variant-numeric:tabular-nums}
.kpi-label{font-size:var(--text-xs);color:var(--text-muted);text-transform:uppercase;
  letter-spacing:0.05em;margin-top:var(--space-1)}

/* ── Team-Checkboxen ───────────────────────────────────── */
.team-checks{display:flex;flex-wrap:wrap;gap:var(--space-3)}
.team-check{display:flex;align-items:center;gap:var(--space-2);font-size:var(--text-sm)}
.team-check input{accent-color:var(--primary)}

/* ── Toast ─────────────────────────────────────────────── */
#toast{position:fixed;bottom:var(--space-6);right:var(--space-6);z-index:999;
  background:var(--surface-2);border:1px solid var(--border);border-radius:var(--radius-lg);
  padding:var(--space-3) var(--space-5);box-shadow:var(--shadow-lg);
  font-size:var(--text-sm);opacity:0;transition:opacity 0.3s;pointer-events:none}
#toast.show{opacity:1}

/* ── Responsive ────────────────────────────────────────── */
@media(max-width:640px){
  .main{padding:var(--space-4)}
  .form-row{grid-template-columns:1fr}
  .env-row{grid-template-columns:1fr 1fr;grid-template-rows:auto auto}
  .modal{padding:var(--space-5)}
}
</style>
</head>
<body>

<!-- Login -->
<div id="login-view">
  <div class="login-box">
    <div class="login-logo">
      <svg aria-label="VBrowser" width="32" height="32" viewBox="0 0 32 32" fill="none"
           xmlns="http://www.w3.org/2000/svg">
        <rect x="2" y="2" width="28" height="28" rx="6" stroke="var(--primary)" stroke-width="2"/>
        <rect x="2" y="8" width="28" height="2" fill="var(--primary)"/>
        <circle cx="7" cy="5" r="1.5" fill="var(--primary)"/>
        <circle cx="12" cy="5" r="1.5" fill="var(--primary)"/>
        <path d="M8 17l4 5 8-8" stroke="var(--primary)" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>VBrowser</span>
    </div>
    <div id="login-error" class="login-error"></div>
    <div class="form-group">
      <label for="login-user">Benutzername</label>
      <input id="login-user" class="form-control" type="text" autocomplete="username" placeholder="admin">
    </div>
    <div class="form-group">
      <label for="login-pass">Passwort</label>
      <input id="login-pass" class="form-control" type="password" autocomplete="current-password">
    </div>
    <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:var(--space-2)"
            onclick="doLogin()">Anmelden</button>
  </div>
</div>

<!-- App Shell (nach Login) -->
<div id="app-view" class="app" style="display:none">
  <header class="topbar">
    <div class="topbar-logo">
      <svg aria-label="VBrowser" width="28" height="28" viewBox="0 0 32 32" fill="none">
        <rect x="2" y="2" width="28" height="28" rx="6" stroke="var(--primary)" stroke-width="2"/>
        <rect x="2" y="8" width="28" height="2" fill="var(--primary)"/>
        <circle cx="7" cy="5" r="1.5" fill="var(--primary)"/>
        <circle cx="12" cy="5" r="1.5" fill="var(--primary)"/>
        <path d="M8 17l4 5 8-8" stroke="var(--primary)" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      VBrowser
    </div>
    <div class="topbar-right">
      <span id="topbar-user" style="font-size:var(--text-sm);color:var(--text-muted)"></span>
      <button class="btn btn-icon btn-ghost" onclick="toggleTheme()" aria-label="Theme wechseln" id="theme-btn">
        🌙
      </button>
      <button class="btn btn-sm btn-secondary" onclick="doLogout()">Abmelden</button>
    </div>
  </header>

  <main class="main">
    <!-- Nutzer-Navigation -->
    <div id="user-nav" class="tabs">
      <button class="tab-btn active" onclick="showTab('tab-start','user-nav',this)">Browser starten</button>
      
    </div>

    <!-- Tab: Browser starten -->
    <div id="tab-start" class="tab-panel active">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-6)">
        <div>
          <h2 style="font-size:var(--text-lg);font-weight:600">Container wählen</h2>
          <p style="font-size:var(--text-sm);color:var(--text-muted);margin-top:var(--space-1)">
            Wähle einen Browser-Container und starte deine Session.
          </p>
        </div>
        <button class="btn btn-primary" id="btn-start" onclick="startSession()" disabled>
          ▶ Starten
        </button>
      </div>
      <div id="container-grid" class="card-grid">
        <p style="color:var(--text-muted);font-size:var(--text-sm)">Lädt…</p>
      </div>
    </div>

    <!-- Admin-Navigation (nur für Admins) -->
    <div id="admin-section" style="display:none;margin-top:var(--space-10)">
      <div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-6)">
        <div style="width:3px;height:24px;background:var(--primary);border-radius:2px"></div>
        <h2 style="font-size:var(--text-lg);font-weight:600">Administration</h2>
      </div>
      <div id="admin-nav" class="tabs">
        <button class="tab-btn active" onclick="showTab('tab-admin-overview','admin-nav',this)">Übersicht</button>
        <button class="tab-btn" onclick="showTab('tab-admin-containers','admin-nav',this);loadAdminContainers()">Container</button>
        <button class="tab-btn" onclick="showTab('tab-admin-users','admin-nav',this);loadAdminUsers()">Nutzer</button>
        <button class="tab-btn" onclick="showTab('tab-admin-teams','admin-nav',this);loadAdminTeams()">Teams</button>
        <button class="tab-btn" onclick="showTab('tab-admin-sessions','admin-nav',this);loadAdminSessions()">Alle Sessions</button>
        <button class="tab-btn" onclick="showTab('tab-admin-log','admin-nav',this);loadAdminLog()">Audit-Log</button>
      </div>

      <!-- Admin: Übersicht -->
      <div id="tab-admin-overview" class="tab-panel active">
        <div id="kpi-strip" class="kpi-strip"></div>
      </div>

      <!-- Admin: Container -->
      <div id="tab-admin-containers" class="tab-panel">
        <div style="display:flex;justify-content:flex-end;margin-bottom:var(--space-4)">
          <button class="btn btn-primary" onclick="openContainerModal(null)">+ Container hinzufügen</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>Name</th><th>Image</th><th>Port</th><th>CPU</th><th>RAM</th>
              <th>ENV</th><th>Teams</th><th>Standard</th><th>Aktionen</th>
            </tr></thead>
            <tbody id="admin-containers-tbody">
              <tr><td colspan="9" style="color:var(--text-muted);text-align:center;padding:var(--space-8)">Lädt…</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Admin: Nutzer -->
      <div id="tab-admin-users" class="tab-panel">
        <div style="display:flex;justify-content:flex-end;margin-bottom:var(--space-4)">
          <button class="btn btn-primary" onclick="openNewUserModal()">+ Nutzer anlegen</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Benutzername</th><th>Rolle</th><th>Team</th><th>Angelegt</th><th>Aktionen</th></tr></thead>
            <tbody id="admin-users-tbody"></tbody>
          </table>
        </div>
      </div>

      <!-- Admin: Teams -->
      <div id="tab-admin-teams" class="tab-panel">
        <div style="display:flex;justify-content:flex-end;margin-bottom:var(--space-4)">
          <button class="btn btn-primary" onclick="openNewTeamModal()">+ Team anlegen</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Team</th><th>Mitglieder</th><th>Container</th><th>Aktionen</th></tr></thead>
            <tbody id="admin-teams-tbody"></tbody>
          </table>
        </div>
      </div>

      <!-- Admin: Alle Sessions -->
      <div id="tab-admin-sessions" class="tab-panel">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Nutzer</th><th>Container</th><th>Status</th><th>Gestartet</th><th>Aktionen</th></tr></thead>
            <tbody id="admin-sessions-tbody"></tbody>
          </table>
        </div>
      </div>

<!-- Admin: Audit-Log -->
<div id="tab-admin-log" class="tab-panel">
  <div class="card" style="margin-bottom:var(--space-4)">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:var(--space-3);align-items:end">
      
      <div class="form-group" style="margin-bottom:0">
        <label for="audit-period">Zeitraum</label>
        <select id="audit-period" class="form-control" onchange="syncAuditFilterVisibility()">
          <option value="all">Gesamt</option>
          <option value="year">Jahr</option>
          <option value="month" selected>Monat</option>
          <option value="week">Woche</option>
          <option value="day">Tag</option>
        </select>
      </div>

      <div class="form-group" style="margin-bottom:0" id="audit-year-wrapper">
        <label for="audit-year">Jahr</label>
        <input id="audit-year" class="form-control" type="number" min="2024" max="2100">
      </div>

      <div class="form-group" style="margin-bottom:0" id="audit-month-wrapper">
        <label for="audit-month">Monat</label>
        <select id="audit-month" class="form-control">
          <option value="">—</option>
          <option value="1">01</option><option value="2">02</option>
          <option value="3">03</option><option value="4">04</option>
          <option value="5">05</option><option value="6">06</option>
          <option value="7">07</option><option value="8">08</option>
          <option value="9">09</option><option value="10">10</option>
          <option value="11">11</option><option value="12">12</option>
        </select>
      </div>

      <div class="form-group" style="margin-bottom:0; display:none" id="audit-week-wrapper">
        <label for="audit-week">Woche</label>
        <input id="audit-week" class="form-control" type="number" min="1" max="53" placeholder="z.B. 14">
      </div>

      <div class="form-group" style="margin-bottom:0; display:none" id="audit-day-wrapper">
        <label for="audit-day">Tag</label>
        <input id="audit-day" class="form-control" type="number" min="1" max="31" placeholder="z.B. 06">
      </div>

      <div class="form-group" style="margin-bottom:0">
        <label for="audit-user-name">Nutzername</label>
        <input id="audit-user-name" class="form-control" type="text" placeholder="optional">
      </div>

      <div class="form-group" style="margin-bottom:0">
        <label for="audit-image">Docker-Container</label>
        <select id="audit-image" class="form-control">
          <option value="">Alle Container</option>
        </select>
      </div>

      <div style="display:flex;gap:var(--space-2);align-items:end">
        <button class="btn btn-sm btn-secondary" onclick="loadAdminLog()">↻ Aktualisieren</button>
        <button class="btn btn-sm btn-secondary" onclick="resetAuditFilters()">Zurücksetzen</button>
        <button class="btn btn-sm btn-secondary" onclick="exportLog()">↓ CSV Export</button>
      </div>
    </div>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Nutzer</th>
          <th>Sitzungen</th>
          <th>Gesamtzeit</th>
        </tr>
      </thead>
      <tbody id="admin-log-ranking-tbody">
        <tr>
          <td colspan="4" style="color:var(--text-muted);text-align:center;padding:var(--space-8)">Lädt…</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<!-- Fullscreen Session Overlay -->
<div id="session-fullscreen" style="display:none; position:fixed; inset:0; z-index:9999; background:#000; flex-direction:column;">
  <div style="height:40px; background:#111; display:flex; align-items:center; justify-content:space-between; padding:0 16px; border-bottom:1px solid #333;">
    <div style="color:#aaa; font-size:14px; font-weight:500; display:flex; gap:10px; align-items:center;">
      <div style="width:8px; height:8px; border-radius:50%; background:var(--success);"></div>
      <span id="session-title">Aktive Session</span>
    </div>
    <button onclick="stopSession()" style="background:var(--error); color:#fff; border:none; padding:4px 12px; border-radius:4px; cursor:pointer; font-size:12px; font-weight:bold;">
      ⏹ Session beenden
    </button>
  </div>
  <iframe id="browserFrame" style="flex:1; width:100%; border:none; background:#000;"></iframe>
</div>

<!-- Modal: Container hinzufügen / bearbeiten -->
<div id="modal-container" class="modal-backdrop">
  <div class="modal">
    <div class="modal-header">
      <h2 id="modal-container-title">Container</h2>
      <button class="btn btn-icon btn-ghost" onclick="closeModal('modal-container')" aria-label="Schließen">✕</button>
    </div>
    <form id="form-container" onsubmit="saveContainer(event)">
      <input type="hidden" id="cdef-id">
      <div class="form-row">
        <div class="form-group">
          <label for="cdef-name">Name *</label>
          <input id="cdef-name" class="form-control" required placeholder="z.B. Firefox ESR">
        </div>
        <div class="form-group">
          <label for="cdef-image">Docker-Image *</label>
          <input id="cdef-image" class="form-control" required placeholder="jlesage/firefox:latest">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label for="cdef-port">Interner Port</label>
          <input id="cdef-port" class="form-control" type="number" value="5800" min="1" max="65535">
        </div>
        <div class="form-group">
          <label for="cdef-shm">SHM-Größe</label>
          <input id="cdef-shm" class="form-control" placeholder="2g">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label for="cdef-cpu">CPU-Limit (Kerne, leer = unbegrenzt)</label>
          <input id="cdef-cpu" class="form-control" type="number" step="0.1" min="0.1" placeholder="z.B. 2.0">
        </div>
        <div class="form-group">
          <label for="cdef-mem">RAM-Limit (leer = unbegrenzt)</label>
          <input id="cdef-mem" class="form-control" placeholder="z.B. 2g">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label for="cdef-restart">Neustart-Policy</label>
          <select id="cdef-restart" class="form-control">
            <option value="no">no</option>
            <option value="on-failure">on-failure</option>
            <option value="always">always</option>
            <option value="unless-stopped">unless-stopped</option>
          </select>
        </div>
        <div class="form-group" style="justify-content:flex-end;padding-top:var(--space-6)">
          <label style="display:flex;align-items:center;gap:var(--space-2);font-weight:500;cursor:pointer">
            <input type="checkbox" id="cdef-default" style="accent-color:var(--primary)">
            Standard-Container
          </label>
        </div>
      </div>
      <div class="form-group">
        <label for="cdef-desc">Beschreibung</label>
        <input id="cdef-desc" class="form-control" placeholder="Kurze Beschreibung für Nutzer">
      </div>

      <!-- ENV-Variablen -->
      <div style="margin-bottom:var(--space-4)">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-2)">
          <label style="font-size:var(--text-sm);font-weight:500;color:var(--text-muted)">
            Environment-Variablen
          </label>
          <button type="button" class="btn btn-sm btn-secondary" onclick="addEnvRow()">+ ENV hinzufügen</button>
        </div>
        <div id="env-list" class="env-list"></div>
        <p class="form-hint">TOKEN wird automatisch gesetzt und muss nicht angegeben werden.</p>
      </div>

      <!-- Team-Zuweisung -->
      <div class="form-group">
        <label style="margin-bottom:var(--space-2)">Team-Zugang (leer = alle Teams)</label>
        <div id="team-checks" class="team-checks">
          <p style="font-size:var(--text-sm);color:var(--text-muted)">Lädt…</p>
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeModal('modal-container')">Abbrechen</button>
        <button type="submit" class="btn btn-primary">Speichern</button>
      </div>
    </form>
  </div>
</div>

<!-- Modal: Nutzer anlegen -->
<div id="modal-user" class="modal-backdrop">
  <div class="modal">
    <div class="modal-header">
      <h2>Nutzer anlegen</h2>
      <button class="btn btn-icon btn-ghost" onclick="closeModal('modal-user')" aria-label="Schließen">✕</button>
    </div>
    <form onsubmit="createUser(event)">
      <div class="form-group"><label>Benutzername *</label>
        <input id="new-username" class="form-control" required></div>
      <div class="form-group"><label>Passwort *</label>
        <input id="new-password" class="form-control" type="password" required></div>
      <div class="form-group"><label>Team</label>
        <select id="new-user-team" class="form-control">
          <option value="">— kein Team —</option>
        </select>
      </div>
      <div class="form-group">
        <label style="display:flex;align-items:center;gap:var(--space-2);cursor:pointer">
          <input type="checkbox" id="new-isadmin" style="accent-color:var(--primary)"> Admin
        </label>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeModal('modal-user')">Abbrechen</button>
        <button type="submit" class="btn btn-primary">Anlegen</button>
      </div>
    </form>
  </div>
</div>

<!-- Modal: Team anlegen -->
<div id="modal-team" class="modal-backdrop">
  <div class="modal" style="max-width:400px">
    <div class="modal-header">
      <h2>Team anlegen</h2>
      <button class="btn btn-icon btn-ghost" onclick="closeModal('modal-team')" aria-label="Schließen">✕</button>
    </div>
    <form onsubmit="createTeam(event)">
      <div class="form-group"><label>Team-Name *</label>
        <input id="new-teamname" class="form-control" required></div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeModal('modal-team')">Abbrechen</button>
        <button type="submit" class="btn btn-primary">Anlegen</button>
      </div>
    </form>
  </div>
</div>

<!-- Modal: Nutzer-Details Log -->
<div id="user-detail-modal" class="modal-backdrop">
  <div class="modal" style="max-width:900px">
    <div class="modal-header">
      <h2 id="detail-title">Sitzungen</h2>
      <button class="btn btn-icon btn-ghost" onclick="closeModal('user-detail-modal')" aria-label="Schließen">✕</button>
    </div>

    <div class="table-wrap" style="max-height:400px;overflow-y:auto">
      <table>
        <thead>
          <tr>
            <th>Start</th>
            <th>Ende</th>
            <th>Dauer</th>
            <th>Image</th>
            <th>Container</th>
            <th>IP</th>
          </tr>
        </thead>
        <tbody id="detail-body">
          <tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:var(--space-4)">Lädt…</td></tr>
        </tbody>
      </table>
    </div>
    
    <div style="margin-top:var(--space-4);display:flex;justify-content:space-between;align-items:center">
      <button class="btn btn-sm btn-secondary" onclick="exportUserLog()">↓ Detail-CSV Export</button>
      <div style="font-weight:bold" id="detail-total"></div>
    </div>
  </div>
</div>

<!-- Toast -->
<div id="toast"></div>

<script>
// ── State ──────────────────────────────────────────────────────────────
let token = null;
let currentUser = null;
let selectedContainerDefId = null;
let allContainerDefs = [];
let allTeams = [];
let logData = [];
let auditRanking = [];
let auditUserSessions = [];
let auditSelectedUser = null;
let auditContainersLoaded = false;

// ── Theme ──────────────────────────────────────────────────────────────
let theme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
document.documentElement.setAttribute('data-theme', theme);
function toggleTheme() {
  theme = theme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  document.getElementById('theme-btn').textContent = theme === 'dark' ? '🌙' : '☀️';
}

// ── Toast ──────────────────────────────────────────────────────────────
function toast(msg, type='info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.borderColor = type === 'error' ? 'var(--error)' : type === 'ok' ? 'var(--success)' : 'var(--border)';
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 3000);
}

// ── API helper ─────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(token ? {'Authorization': 'Bearer ' + token} : {}) },
    ...opts
  });
  if (res.status === 401) { doLogout(); return null; }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Fehler ' + res.status);
  return data;
}

// ── Auth ───────────────────────────────────────────────────────────────
async function doLogin() {
  const u = document.getElementById('login-user').value.trim();
  const p = document.getElementById('login-pass').value;
  const err = document.getElementById('login-error');
  err.style.display = 'none';
  try {
    const data = await fetch('/api/login', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({username: u, password: p})
    }).then(async r => {
      const json = await r.json();
      if (!r.ok) throw new Error(json.detail || 'Falsche Zugangsdaten');
      return json;
    });
    
    const jwt = data.token || data.access_token;
    if (!jwt) throw new Error('Ungültige Server-Antwort (kein Token)');
    
    token = jwt;
    currentUser = data.user || {
      username: u, 
      isadmin: data.isadmin !== undefined ? data.isadmin : (data.user && data.user.isadmin)
    };
    
    if (typeof currentUser.isadmin === 'number') {
        currentUser.isadmin = currentUser.isadmin === 1;
    }
    
    document.getElementById('login-view').style.display = 'none';
    document.getElementById('app-view').style.display = 'flex';
    document.getElementById('topbar-user').textContent = currentUser.username;
    initApp();
  } catch(e) {
    err.textContent = e.message;
    err.style.display = 'block';
  }
}

document.getElementById('login-pass').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

function doLogout() {
  token = null; currentUser = null;
  document.getElementById('login-view').style.display = 'flex';
  document.getElementById('app-view').style.display = 'none';
}

// ── App Init ───────────────────────────────────────────────────────────
function initApp() {
  if (currentUser.isadmin) {
    document.getElementById('admin-section').style.display = 'block';
    loadKPIs();
  }
  loadContainerDefs();
  
}

// ── Tabs ───────────────────────────────────────────────────────────────
function showTab(panelId, navId, btn) {
  document.querySelectorAll('#' + navId + ' .tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('#' + panelId.replace(/-[^-]*$/, '') + ' .tab-panel, .tab-panel').forEach(p => {
    if (p.id && p.id.startsWith(panelId.split('-').slice(0,2).join('-'))) p.classList.remove('active');
  });
  btn.classList.add('active');
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const siblings = panel.parentElement.querySelectorAll('.tab-panel');
  siblings.forEach(s => s.classList.remove('active'));
  panel.classList.add('active');
}

// ── Modal helpers ──────────────────────────────────────────────────────
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
document.querySelectorAll('.modal-backdrop').forEach(el =>
  el.addEventListener('click', e => { if (e.target === el) el.classList.remove('open'); })
);

// ── Container-Auswahl (Nutzer) ─────────────────────────────────────────
async function loadContainerDefs() {
  const grid = document.getElementById('container-grid');
  try {
    allContainerDefs = await api('/api/containers');
    grid.innerHTML = '';
    if (!allContainerDefs.length) {
      grid.innerHTML = '<p style="color:var(--text-muted)">Keine Container verfügbar.</p>';
      return;
    }
    allContainerDefs.forEach(cd => {
      const card = document.createElement('div');
      card.className = 'container-card';
      card.dataset.id = cd.id;
      if (cd.is_default) card.innerHTML += '<span class="default-badge">Standard</span>';
      const teams = cd.team_ids && cd.team_ids.length
        ? '<span class="tag">Teams: ' + cd.team_ids.length + '</span>'
        : '<span class="tag">Alle Teams</span>';
      const envCount = cd.env_vars ? cd.env_vars.length : 0;
      card.innerHTML += `
        <h3>${esc(cd.name)}</h3>
        <p>${esc(cd.description || cd.image)}</p>
        <div class="meta">
          <span class="tag">${esc(cd.image.split(':')[0].split('/').pop())}</span>
          ${envCount > 0 ? '<span class="tag">' + envCount + ' ENV</span>' : ''}
          ${teams}
        </div>`;
      card.addEventListener('click', () => selectContainer(cd.id, card));
      grid.appendChild(card);
      if (cd.is_default) selectContainer(cd.id, card);
    });
  } catch(e) {
    grid.innerHTML = '<p style="color:var(--error)">Fehler: ' + esc(e.message) + '</p>';
  }
}

function selectContainer(id, card) {
  document.querySelectorAll('.container-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  selectedContainerDefId = id;
  document.getElementById('btn-start').disabled = false;
}

let activeSessionInterval = null;

async function startSession() {
  const btn = document.getElementById("btn-start");
  btn.disabled = true;
  btn.textContent = "⏳ Startet… (Bitte warten)";

  try {
    const data = await api("/api/session/start", {
      method: "POST",
      body: JSON.stringify({container_def_id: selectedContainerDefId})
    });

    // Cookie über verstecktes iFrame setzen
    const cookieFrame = document.createElement("iframe");
    cookieFrame.style.display = "none";
    const browserHost = new URL(data.url).host;
    cookieFrame.src = `https://${browserHost}/auth/set-cookie?token=${encodeURIComponent(data.token)}&redirect=${encodeURIComponent(data.url)}`;
    document.body.appendChild(cookieFrame);

    // Sanduhr länger anzeigen (6 Sekunden), um Spam zu verhindern
    setTimeout(() => {
        document.body.removeChild(cookieFrame);

        // Container ins Haupt-iFrame laden
        const frame = document.getElementById("browserFrame");
        frame.src = data.url;

        document.getElementById("session-title").textContent = data.container_def || "Browser";
        document.getElementById("session-fullscreen").style.display = "flex";

        // Heartbeats starten (30s)
        if(activeSessionInterval) clearInterval(activeSessionInterval);
        activeSessionInterval = setInterval(async () => {
            try { await api(`/api/session/${data.session_id}/heartbeat`, {method: "POST"}); } catch(e) {}
        }, 30000);

        window.currentRunningSessionId = data.session_id;
        toast("Browser bereit", "ok");

        // WICHTIG: Start-Button wird hier NICHT aktiviert! 
        // Er bleibt deaktiviert, solange die Session läuft.
    }, 6000);

  } catch(e) {
    toast("Fehler: " + e.message, "error");
    btn.disabled = false;
    btn.textContent = "▶ Starten";
  }
}

// ── Sessions ───────────────────────────────────────────────────────────
async function loadSessions() {
  const list = document.getElementById('sessions-list');
  try {
    const sessions = await api('/api/session/list');
    if (!sessions || !sessions.length) {
      list.innerHTML = '<p style="color:var(--text-muted);font-size:var(--text-sm)">Noch keine Sessions.</p>';
      return;
    }
    list.innerHTML = sessions.map(s => `
      <div class="session-card">
        <div class="session-info">
          <strong style="font-size:var(--text-sm)">${esc(s.container_name)}</strong>
          <span style="font-size:var(--text-xs);color:var(--text-muted)">${fmtDate(s.created_at)}</span>
          <span class="badge ${s.status === 'running' ? 'badge-green' : 'badge-red'}">
            <span class="dot"></span>${esc(s.status)}
          </span>
        </div>
        <div class="session-actions">
          ${s.status === 'running' ? `
            <button class="btn btn-sm btn-secondary" onclick="connectSession('${s.id}')">Verbinden</button>
            <button class="btn btn-sm btn-danger" onclick="stopSession('${s.id}')">Stoppen</button>
          ` : `<button class="btn btn-sm btn-ghost" onclick="deleteSession('${s.id}')">Entfernen</button>`}
        </div>
      </div>`).join('');
  } catch(e) {
    list.innerHTML = '<p style="color:var(--error)">Fehler beim Laden.</p>';
  }
}

async function connectSession(id) {
  try {
     const sessions = await api("/api/session/list");
     const s = sessions.find(x => x.id === id);
     if(s) {
        const cookieFrame = document.createElement("iframe");
        cookieFrame.style.display = "none";

        // Construct the URL properly via Traefik Subdomain
        let targetUrl = s.url;
        if (!targetUrl) {
            const hostId = s.container_name.replace("vbrowser-", "");
            // Errate die Base Domain aus der aktuellen URL
            let baseParts = window.location.hostname.split('.');
            let baseDomain = window.location.hostname;
            if (baseParts.length > 2) {
                baseDomain = baseParts.slice(1).join('.'); // z.B. vbrowser.de
            }
            targetUrl = `https://${hostId}.${baseDomain}/`;
        }

        const browserHost = new URL(targetUrl).host;
        cookieFrame.src = `https://${browserHost}/auth/set-cookie?token=${encodeURIComponent(s.token)}&redirect=${encodeURIComponent(targetUrl)}`;
        document.body.appendChild(cookieFrame);

        setTimeout(() => {
            document.body.removeChild(cookieFrame);
            const frame = document.getElementById("browserFrame");
            frame.src = targetUrl;
            document.getElementById("session-title").textContent = s.container_name;
            document.getElementById("session-fullscreen").style.display = "flex";

            if(activeSessionInterval) clearInterval(activeSessionInterval);
            window.currentRunningSessionId = s.session_id;
        }, 3000);
     }
  } catch(e) { toast("Verbindung fehlgeschlagen", "error"); }
}


async function stopSession(id = null) {
  const targetId = id || window.currentRunningSessionId;
  if (!targetId) return;
  if (!confirm("Session wirklich beenden und löschen?")) return;

  const btn = document.getElementById("btn-start");

  try {
    // Ruft nun DELETE statt POST /stop auf. Dadurch wird der Container gestoppt UND aus der DB gelöscht!
    await api("/api/session/" + targetId, {method:"DELETE"});
    toast("Session beendet und entfernt.", "ok");

    if (targetId === window.currentRunningSessionId) {
        document.getElementById("session-fullscreen").style.display = "none";
        document.getElementById("browserFrame").src = "about:blank";
        if(activeSessionInterval) clearInterval(activeSessionInterval);
        window.currentRunningSessionId = null;
    }

    // Admins haben noch die Übersicht, diese manuell laden
    if (currentUser && currentUser.isadmin && typeof loadAdminSessions === "function") {
        loadAdminSessions();
    }
  } catch(e) { 
    toast(e.message, "error"); 
  } finally {
    // Start-Button erst nach dem endgültigen Beenden wieder freigeben
    if (btn) {
        btn.disabled = false;
        btn.textContent = "▶ Starten";
    }
  }
}

async function deleteSession(id) {
  try {
    await api('/api/session/' + id, {method:'DELETE'});
    toast('Session entfernt.', 'ok');
    
  } catch(e) { toast(e.message, 'error'); }
}

// ── Admin: KPIs ────────────────────────────────────────────────────────
async function loadKPIs() {
  try {
    const [containers, users, teams, sessions] = await Promise.all([
      api('/api/admin/containers'),
      api('/api/admin/users'),
      api('/api/admin/teams'),
      api('/api/session/list'),
    ]);
    const running = sessions ? sessions.filter(s => s.status === 'running').length : 0;
    document.getElementById('kpi-strip').innerHTML = [
      {v: containers ? containers.length : 0, l: 'Container-Defs'},
      {v: running, l: 'Laufende Sessions'},
      {v: users ? users.length : 0, l: 'Nutzer'},
      {v: teams ? teams.length : 0, l: 'Teams'},
    ].map(k => `<div class="kpi"><div class="kpi-val">${k.v}</div><div class="kpi-label">${k.l}</div></div>`).join('');
  } catch {}
}

// ── Admin: Container ───────────────────────────────────────────────────
async function loadAdminContainers() {
  const tbody = document.getElementById('admin-containers-tbody');
  try {
    const defs = await api('/api/admin/containers');
    tbody.innerHTML = defs.map(cd => `
      <tr>
        <td><strong>${esc(cd.name)}</strong></td>
        <td style="font-size:var(--text-xs);color:var(--text-muted)">${esc(cd.image)}</td>
        <td>${cd.internal_port}</td>
        <td>${cd.cpu_limit || '—'}</td>
        <td>${cd.mem_limit || '—'}</td>
        <td><span class="badge badge-blue">${cd.env_vars ? cd.env_vars.length : 0} Vars</span></td>
        <td>${cd.team_ids && cd.team_ids.length ? cd.team_ids.length + ' Teams' : 'Alle'}</td>
        <td>${cd.is_default ? '<span class="badge badge-green">✓</span>' : ''}</td>
        <td>
          <div style="display:flex;gap:var(--space-2)">
            <button class="btn btn-sm btn-secondary" onclick="openContainerModal(${cd.id})">Bearbeiten</button>
            ${!cd.is_default ? `<button class="btn btn-sm btn-danger" onclick="deleteContainerDef(${cd.id})">Löschen</button>` : ''}
          </div>
        </td>
      </tr>`).join('');
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="9" style="color:var(--error)">' + esc(e.message) + '</td></tr>';
  }
}

async function openContainerModal(defId) {
  allTeams = await api('/api/admin/teams') || [];
  const checks = document.getElementById('team-checks');
  checks.innerHTML = allTeams.length
    ? allTeams.map(t => `
        <label class="team-check">
          <input type="checkbox" name="team" value="${t.id}"> ${esc(t.name)}
        </label>`).join('')
    : '<p style="font-size:var(--text-sm);color:var(--text-muted)">Keine Teams vorhanden.</p>';

  document.getElementById('env-list').innerHTML = '';
  document.getElementById('cdef-id').value = '';

  if (defId) {
    document.getElementById('modal-container-title').textContent = 'Container bearbeiten';
    const cd = await api('/api/admin/containers/' + defId);
    document.getElementById('cdef-id').value = cd.id;
    document.getElementById('cdef-name').value = cd.name;
    document.getElementById('cdef-image').value = cd.image;
    document.getElementById('cdef-port').value = cd.internal_port;
    document.getElementById('cdef-shm').value = cd.shm_size;
    document.getElementById('cdef-cpu').value = cd.cpu_limit || '';
    document.getElementById('cdef-mem').value = cd.mem_limit || '';
    document.getElementById('cdef-restart').value = cd.restart_policy;
    document.getElementById('cdef-desc').value = cd.description || '';
    document.getElementById('cdef-default').checked = cd.is_default;
    (cd.env_vars || []).forEach(ev => addEnvRow(ev.key, ev.value, ev.masked));
    (cd.team_ids || []).forEach(tid => {
      const cb = document.querySelector('#team-checks input[value="' + tid + '"]');
      if (cb) cb.checked = true;
    });
  } else {
    document.getElementById('modal-container-title').textContent = 'Container hinzufügen';
    ['cdef-name','cdef-image','cdef-cpu','cdef-mem','cdef-desc'].forEach(id =>
      document.getElementById(id).value = '');
    document.getElementById('cdef-port').value = 5800;
    document.getElementById('cdef-shm').value = '2g';
    document.getElementById('cdef-restart').value = 'no';
    document.getElementById('cdef-default').checked = false;
  }
  openModal('modal-container');
}

function addEnvRow(key='', value='', masked=false) {
  const row = document.createElement('div');
  row.className = 'env-row';
  row.innerHTML = `
    <input type="text" placeholder="KEY" value="${esc(key)}" class="env-key">
    <input type="${masked ? 'password' : 'text'}" placeholder="value" value="${esc(value)}" class="env-val">
    <label class="masked-toggle">
      <input type="checkbox" ${masked ? 'checked' : ''} onchange="this.closest('.env-row').querySelector('.env-val').type=this.checked?'password':'text'">
      🔒
    </label>
    <button type="button" class="btn btn-icon btn-ghost" onclick="this.closest('.env-row').remove()" aria-label="Entfernen">✕</button>`;
  document.getElementById('env-list').appendChild(row);
}

async function saveContainer(e) {
  e.preventDefault();
  const defId = document.getElementById('cdef-id').value;
  const envVars = [...document.querySelectorAll('#env-list .env-row')].map(row => ({
    key: row.querySelector('.env-key').value.trim(),
    value: row.querySelector('.env-val').value,
    masked: row.querySelector('input[type=checkbox]').checked,
  })).filter(ev => ev.key);
  const teamIds = [...document.querySelectorAll('#team-checks input[type=checkbox]:checked')]
    .map(cb => parseInt(cb.value));
  const payload = {
    name: document.getElementById('cdef-name').value.trim(),
    image: document.getElementById('cdef-image').value.trim(),
    internal_port: parseInt(document.getElementById('cdef-port').value) || 5800,
    shm_size: document.getElementById('cdef-shm').value.trim() || '2g',
    cpu_limit: parseFloat(document.getElementById('cdef-cpu').value) || null,
    mem_limit: document.getElementById('cdef-mem').value.trim() || null,
    restart_policy: document.getElementById('cdef-restart').value,
    description: document.getElementById('cdef-desc').value.trim() || null,
    is_default: document.getElementById('cdef-default').checked,
    env_vars: envVars,
    team_ids: teamIds,
  };
  try {
    if (defId) {
      await api('/api/admin/containers/' + defId, {method:'PUT', body:JSON.stringify(payload)});
      toast('Container aktualisiert.', 'ok');
    } else {
      await api('/api/admin/containers', {method:'POST', body:JSON.stringify(payload)});
      toast('Container erstellt.', 'ok');
    }
    closeModal('modal-container');
    loadAdminContainers();
    loadContainerDefs();
    loadKPIs();
  } catch(e) { toast(e.message, 'error'); }
}

async function deleteContainerDef(id) {
  if (!confirm('Container-Definition wirklich löschen?')) return;
  try {
    await api('/api/admin/containers/' + id, {method:'DELETE'});
    toast('Gelöscht.', 'ok');
    loadAdminContainers();
    loadContainerDefs();
    loadKPIs();
  } catch(e) { toast(e.message, 'error'); }
}

// ── Admin: Nutzer ──────────────────────────────────────────────────────
async function loadAdminUsers() {
  const tbody = document.getElementById('admin-users-tbody');
  try {
    const [users, teams] = await Promise.all([api('/api/admin/users'), api('/api/admin/teams')]);
    const teamMap = Object.fromEntries((teams||[]).map(t => [t.id, t.name]));
    tbody.innerHTML = (users||[]).map(u => `
      <tr>
        <td>${esc(u.username)}</td>
        <td>${u.isadmin ? '<span class="badge badge-blue">Admin</span>' : '<span class="badge">Nutzer</span>'}</td>
        <td>${u.team_id ? esc(teamMap[u.team_id] || '?') : '<span style="color:var(--text-faint)">—</span>'}</td>
        <td style="font-size:var(--text-xs);color:var(--text-muted)">${fmtDate(u.created_at)}</td>
        <td><button class="btn btn-sm btn-danger" onclick="deleteUser(${u.id},'${esc(u.username)}')">Löschen</button></td>
      </tr>`).join('');
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="5" style="color:var(--error)">' + esc(e.message) + '</td></tr>';
  }
}

async function openNewUserModal() {
  const teams = await api('/api/admin/teams') || [];
  const sel = document.getElementById('new-user-team');
  sel.innerHTML = '<option value="">— kein Team —</option>' +
    teams.map(t => `<option value="${t.id}">${esc(t.name)}</option>`).join('');
  openModal('modal-user');
}

async function createUser(e) {
  e.preventDefault();
  try {
    await api('/api/admin/users', {method:'POST', body: JSON.stringify({
      username: document.getElementById('new-username').value.trim(),
      password: document.getElementById('new-password').value,
      isadmin: document.getElementById('new-isadmin').checked,
      team_id: parseInt(document.getElementById('new-user-team').value) || null,
    })});
    toast('Nutzer angelegt.', 'ok');
    closeModal('modal-user');
    loadAdminUsers();
    loadKPIs();
  } catch(e) { toast(e.message, 'error'); }
}

async function deleteUser(id, name) {
  if (!confirm('Nutzer "' + name + '" löschen?')) return;
  try {
    await api('/api/admin/users/' + id, {method:'DELETE'});
    toast('Nutzer gelöscht.', 'ok');
    loadAdminUsers();
    loadKPIs();
  } catch(e) { toast(e.message, 'error'); }
}

// ── Admin: Teams ───────────────────────────────────────────────────────
async function loadAdminTeams() {
  const tbody = document.getElementById('admin-teams-tbody');
  try {
    const [teams, users, containers] = await Promise.all([
      api('/api/admin/teams'), api('/api/admin/users'), api('/api/admin/containers')
    ]);
    tbody.innerHTML = (teams||[]).map(t => {
      const members = (users||[]).filter(u => u.team_id === t.id).length;
      const assigned = (containers||[]).filter(c => c.team_ids && c.team_ids.includes(t.id)).length;
      return `<tr>
        <td><strong>${esc(t.name)}</strong></td>
        <td>${members}</td>
        <td>${assigned || '<span style="color:var(--text-faint)">alle</span>'}</td>
        <td><button class="btn btn-sm btn-danger" onclick="deleteTeam(${t.id},'${esc(t.name)}')">Löschen</button></td>
      </tr>`;
    }).join('');
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="4" style="color:var(--error)">' + esc(e.message) + '</td></tr>';
  }
}

function openNewTeamModal() { openModal('modal-team'); }

async function createTeam(e) {
  e.preventDefault();
  try {
    await api('/api/admin/teams', {method:'POST', body: JSON.stringify({
      name: document.getElementById('new-teamname').value.trim()
    })});
    toast('Team angelegt.', 'ok');
    closeModal('modal-team');
    loadAdminTeams();
    loadKPIs();
  } catch(e) { toast(e.message, 'error'); }
}

async function deleteTeam(id, name) {
  if (!confirm('Team "' + name + '" löschen?')) return;
  try {
    await api('/api/admin/teams/' + id, {method:'DELETE'});
    toast('Team gelöscht.', 'ok');
    loadAdminTeams();
    loadKPIs();
  } catch(e) { toast(e.message, 'error'); }
}

// ── Admin: Alle Sessions ───────────────────────────────────────────────
async function loadAdminSessions() {
  const tbody = document.getElementById("admin-sessions-tbody");
  try {
    const sessions = await api("/api/session/list");
    if (!sessions || !sessions.length) {
      tbody.innerHTML = "<tr><td colspan='5' style='color:var(--text-muted);text-align:center;padding:var(--space-8)'>Keine Sessions.</td></tr>";
      return;
    }
    tbody.innerHTML = sessions.map(s => `
      <tr>
        <td>${esc(s.username)}</td>
        <td>
           <div><strong>${esc(s.container_name)}</strong></div>
           <div style="font-size:var(--text-xs);color:var(--text-muted)">${esc(s.image || "Unbekannt")}</div>
        </td>
        <td><span class="badge ${s.status === 'running' ? 'badge-green' : 'badge-red'}">${esc(s.status)}</span></td>
        <td>${fmtDate(s.created_at)}</td>
        <td>
           ${s.status === 'running' ? `<button class="btn btn-sm btn-danger" onclick="stopSession('${s.id}')">Stoppen</button>` : `<button class="btn btn-sm btn-ghost" onclick="deleteSession('${s.id}')">Entfernen</button>`}
        </td>
      </tr>
    `).join('');
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="5" style="color:var(--error);text-align:center">' + esc(e.message) + '</td></tr>';
  }
}

// ── Admin: Audit-Log ───────────────────────────────────────────────────
// ── Log / Ranking ────────────────────────────────────────────────────────
function showPeriodFields(prefix) {
    const p = document.getElementById(prefix + "period").value;
    ["year", "month", "week", "day"].forEach(f => {
        document.getElementById(prefix + f).style.display = "none";
    });
    if (p === "year")  document.getElementById(prefix + "year").style.display = "block";
    if (p === "month") {
        document.getElementById(prefix + "year").style.display = "block";
        document.getElementById(prefix + "month").style.display = "block";
    }
    if (p === "week") {
        document.getElementById(prefix + "year").style.display = "block";
        document.getElementById(prefix + "week").style.display = "block";
    }
    if (p === "day")   document.getElementById(prefix + "day").style.display = "block";
}

function onLogPeriodChange() { showPeriodFields("log-"); loadRanking(); }

function buildLogParams(prefix) {
    const p = document.getElementById(prefix + "period").value;
    let qs = "period=" + p;
    if (p === "year" || p === "month" || p === "week") {
        const y = document.getElementById(prefix + "year").value;
        if (y) qs += "&year=" + y;
    }
    if (p === "month") {
        const m = document.getElementById(prefix + "month").value;
        if (m) qs += "&month=" + m;
    }
    if (p === "week") {
        const w = document.getElementById(prefix + "week").value;
        if (w) qs += "&week=" + w;
    }
    if (p === "day") {
        const d = document.getElementById(prefix + "day").value;
        if (d) qs += "&day=" + d;
    }
    return qs;
}

function fmtDuration(seconds) {
    if (!seconds) return "0s";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    let res = [];
    if (h > 0) res.push(h + "h");
    if (m > 0) res.push(m + "m");
    if (s > 0 || res.length === 0) res.push(s + "s");
    return res.join(" ");
}

function jsEsc(s) {
  if (!s) return '';
  return String(s)
    .split(String.fromCharCode(92)).join(String.fromCharCode(92) + String.fromCharCode(92))
    .split(String.fromCharCode(39)).join(String.fromCharCode(92) + String.fromCharCode(39))
    .split(String.fromCharCode(13)).join(' ')
    .split(String.fromCharCode(10)).join(' ');
}

function fmtDuration(sec) {
  const n = Math.max(0, Math.floor(Number(sec) || 0));
  const h = Math.floor(n / 3600);
  const m = Math.floor((n % 3600) / 60);
  const s = n % 60;
  if (h > 0) return `${h}h ${String(m).padStart(2, '0')}m`;
  if (m > 0) return `${m}m ${String(s).padStart(2, '0')}s`;
  return `${s}s`;
}

function qs(params) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') sp.set(k, String(v));
  });
  return sp.toString();
}

function getAuditFilters() {
  return {
    period: document.getElementById('audit-period')?.value || 'month',
    year: parseInt(document.getElementById('audit-year')?.value || '') || null,
    month: parseInt(document.getElementById('audit-month')?.value || '') || null,
    week: parseInt(document.getElementById('audit-week')?.value || '') || null,
    day: parseInt(document.getElementById('audit-day')?.value || '') || null,
    image: document.getElementById('audit-image')?.value || null,
    container_name: document.getElementById('audit-container-name')?.value.trim() || null,
  };
}

function syncAuditFilterVisibility() {
  const period = document.getElementById('audit-period')?.value || 'month';
  const year = document.getElementById('audit-year');
  const month = document.getElementById('audit-month');
  const week = document.getElementById('audit-week');
  const day = document.getElementById('audit-day');

  if (!year || !month || !week || !day) return;

  year.disabled = period === 'all';
  month.disabled = !['month', 'day'].includes(period);
  week.disabled = period !== 'week';
  day.disabled = period !== 'day';
}

function resetAuditFilters() {
  const now = new Date();
  document.getElementById('audit-period').value = 'month';
  document.getElementById('audit-year').value = now.getFullYear();
  document.getElementById('audit-month').value = now.getMonth() + 1;
  document.getElementById('audit-week').value = '';
  document.getElementById('audit-day').value = '';
  document.getElementById('audit-image').value = '';
  document.getElementById('audit-container-name').value = '';
  auditSelectedUser = null;
  syncAuditFilterVisibility();
  loadAdminLog();
}

async function loadAuditContainerFilter() {
  const sel = document.getElementById('audit-image');
  if (!sel) return;

  const defs = await api('/api/admin/containers') || [];
  const current = sel.value || '';

  sel.innerHTML =
    '<option value="">Alle Docker-Container</option>' +
    defs.map(cd => `<option value="${esc(cd.image)}">${esc(cd.name)} (${esc(cd.image)})</option>`).join('');

  sel.value = current;
  auditContainersLoaded = true;
}

function renderAuditRanking() {
  const tbody = document.getElementById('admin-log-ranking-tbody');

  if (!auditRanking.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" style="color:var(--text-muted);text-align:center;padding:var(--space-8)">
          Keine Werte für den gewählten Filter.
        </td>
      </tr>`;
    return;
  }

  tbody.innerHTML = auditRanking.map((r, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>
        <a href="#"
           style="color:var(--primary);text-decoration:none;font-weight:600"
           onclick="loadAuditUserLog(${r.user_id}, '${jsEsc(r.username)}');return false;">
          ${esc(r.username)}
        </a>
      </td>
      <td>${Number(r.session_count || 0)}</td>
      <td>${fmtDuration(r.total_seconds || 0)}</td>
    </tr>
  `).join('');
}



async function loadAuditUserLog(userId, username) {
  auditSelectedUser = { id: userId, username };
  document.getElementById('admin-log-selected-user').textContent = username;
  document.getElementById('admin-log-user-box').style.display = 'block';

  const filters = getAuditFilters();
  auditUserSessions = await api('/api/admin/logging/user/' + userId + '?' + qs(filters)) || [];
  logData = auditUserSessions;

}


async function loadAdminLog() {
  const rankingTbody = document.getElementById('admin-log-ranking-tbody');
  const detailsTbody = document.getElementById('admin-log-tbody');

  try {
    if (!document.getElementById('audit-year').value) {
      const now = new Date();
      document.getElementById('audit-year').value = now.getFullYear();
      document.getElementById('audit-month').value = now.getMonth() + 1;
    }

    syncAuditFilterVisibility();

    if (!auditContainersLoaded) {
      await loadAuditContainerFilter();
    }

    rankingTbody.innerHTML = `
      <tr>
        <td colspan="4" style="color:var(--text-muted);text-align:center;padding:var(--space-8)">Lädt…</td>
      </tr>`;

    if (!auditSelectedUser) {
      detailsTbody.innerHTML = `
        <tr>
          <td colspan="6" style="color:var(--text-muted);text-align:center;padding:var(--space-8)">
            Bitte oben einen Nutzer auswählen.
          </td>
        </tr>`;
    }

    const filters = getAuditFilters();
    auditRanking = await api('/api/admin/logging/ranking?' + qs(filters)) || [];
    renderAuditRanking();

    if (auditSelectedUser?.id) {
      await loadAuditUserLog(auditSelectedUser.id, auditSelectedUser.username);
    }
  } catch (e) {
    rankingTbody.innerHTML = `
      <tr>
        <td colspan="4" style="color:var(--error);text-align:center;padding:var(--space-8)">
          ${esc(e.message)}
        </td>
      </tr>`;
    detailsTbody.innerHTML = `
      <tr>
        <td colspan="6" style="color:var(--error);text-align:center;padding:var(--space-8)">
          ${esc(e.message)}
        </td>
      </tr>`;
  }
}

async function loadRanking() {
  const params = buildLogParams("log-");
  const tbody = document.getElementById("admin-log-tbody");
  tbody.innerHTML = "<tr><td colspan='4' style='color:var(--text-muted);text-align:center'>Lädt…</td></tr>";
  try {
    const data = await api("/api/admin/logging/ranking?" + params) || [];
    if (!data.length) {
      tbody.innerHTML = "<tr><td colspan='4' style='color:var(--text-muted);text-align:center'>Keine Daten gefunden.</td></tr>";
      return;
    }
    tbody.innerHTML = data.map((r, i) => `
      <tr>
        <td style="color:var(--text-muted)">${i + 1}</td>
        <td><a href="#" onclick="openUserDetail(${r.user_id}, '${esc(r.username)}');return false" style="color:var(--primary);text-decoration:none;font-weight:500">${esc(r.username)}</a></td>
        <td style="text-align:right">${r.session_count}</td>
        <td style="text-align:right">${fmtDuration(r.total_seconds)}</td>
      </tr>`).join('');
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="4" style="color:var(--error);text-align:center">' + esc(e.message) + '</td></tr>';
  }
}

let _detailUserId = null;
async function openUserDetail(userId, username) {
    _detailUserId = userId;
    document.getElementById("detail-title").textContent = `Sitzungen: ${username}`;
    document.getElementById("detail-period").value = "all";
    showPeriodFields("detail-");
    openModal("user-detail-modal");
    await loadUserDetail();
}

async function loadUserDetail() {
    if (!_detailUserId) return;
    const params = buildLogParams("detail-");
    const tbody = document.getElementById("detail-body");
    tbody.innerHTML = "<tr><td colspan='4' style='color:var(--text-muted);text-align:center'>Lädt…</td></tr>";
    document.getElementById("detail-total").textContent = "";
    try {
        const data = await api(`/api/admin/logging/user/${_detailUserId}?` + params) || [];
        if (!data.length) {
            tbody.innerHTML = "<tr><td colspan='4' style='color:var(--text-muted);text-align:center'>Keine Sitzungen.</td></tr>";
            return;
        }
        let totalSec = 0;
        tbody.innerHTML = data.map(r => {
            totalSec += r.duration || 0;
            return `<tr>
              <td style="font-size:var(--text-xs);color:var(--text-muted)">${esc(r.image || 'Unbekannt')}</td>
              <td>${esc(r.container_name)}</td>
              <td>${fmtDate(r.started_at)}</td>
              <td>${fmtDuration(r.duration)}</td>
            </tr>`;
        }).join('');
        document.getElementById("detail-total").textContent = `Gesamtdauer: ${fmtDuration(totalSec)}`;
    } catch(e) {
        tbody.innerHTML = '<tr><td colspan="4" style="color:var(--error);text-align:center">' + esc(e.message) + '</td></tr>';
    }
}


function exportLog() {
  let rows = [];
  let filename = 'audit-ranking.csv';

  if (auditSelectedUser && auditUserSessions.length) {
    rows = [['Start', 'Ende', 'Dauer (s)', 'Docker-Image', 'Container', 'IP']];
    auditUserSessions.forEach(s => {
      rows.push([
        s.started_at || '',
        s.ended_at || '',
        Math.floor(Number(s.duration) || 0),
        s.image || '',
        s.container_name || '',
        s.container_ip || ''
      ]);
    });
    filename = 'audit-user-' + auditSelectedUser.username + '.csv';
  } else {
    rows = [['Nutzer', 'Sitzungen', 'Gesamtzeit (s)']];
    auditRanking.forEach(r => {
      rows.push([
        r.username || '',
        Number(r.session_count || 0),
        Math.floor(Number(r.total_seconds) || 0),
      ]);
    });
  }

  const csv = rows
    .map(r => r.map(c => '"' + String(c).split('"').join('""') + '"').join(','))
    .join(String.fromCharCode(13) + String.fromCharCode(10));

  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = filename;
  a.click();
}

function getAuditFilters() {
  return {
    period: document.getElementById('audit-period')?.value || 'month',
    year: document.getElementById('audit-year')?.value || null,
    month: document.getElementById('audit-month')?.value || null,
    week: document.getElementById('audit-week')?.value || null,
    day: document.getElementById('audit-day')?.value || null,
    image: document.getElementById('audit-image')?.value || null,
    username: document.getElementById('audit-user-name')?.value.trim().toLowerCase() || null,
  };
}

function syncAuditFilterVisibility() {
  const period = document.getElementById('audit-period')?.value || 'month';
  const yw = document.getElementById('audit-year-wrapper');
  const mw = document.getElementById('audit-month-wrapper');
  const ww = document.getElementById('audit-week-wrapper');
  const dw = document.getElementById('audit-day-wrapper');

  if (!yw || !mw || !ww || !dw) return;

  yw.style.display = period === 'all' ? 'none' : 'block';
  mw.style.display = ['month', 'day'].includes(period) ? 'block' : 'none';
  ww.style.display = period === 'week' ? 'block' : 'none';
  dw.style.display = period === 'day' ? 'block' : 'none';
}

function resetAuditFilters() {
  const now = new Date();
  document.getElementById('audit-period').value = 'month';
  document.getElementById('audit-year').value = now.getFullYear();
  document.getElementById('audit-month').value = now.getMonth() + 1;
  document.getElementById('audit-week').value = '';
  document.getElementById('audit-day').value = '';
  document.getElementById('audit-image').value = '';
  document.getElementById('audit-user-name').value = '';
  
  syncAuditFilterVisibility();
  loadAdminLog();
}

async function loadAuditContainerFilter() {
  const sel = document.getElementById('audit-image');
  if (!sel) return;
  const defs = await api('/api/admin/containers') || [];
  const current = sel.value || '';
  sel.innerHTML = '<option value="">Alle Container</option>' +
    defs.map(cd => `<option value="${esc(cd.image)}">${esc(cd.name)} (${esc(cd.image)})</option>`).join('');
  sel.value = current;
  auditContainersLoaded = true;
}

async function loadAdminLog() {
  const tbody = document.getElementById('admin-log-ranking-tbody');
  try {
    if (!document.getElementById('audit-year').value) {
      const now = new Date();
      document.getElementById('audit-year').value = now.getFullYear();
      document.getElementById('audit-month').value = now.getMonth() + 1;
    }
    syncAuditFilterVisibility();
    if (!auditContainersLoaded) await loadAuditContainerFilter();

    tbody.innerHTML = `<tr><td colspan="4" style="color:var(--text-muted);text-align:center;padding:var(--space-8)">Lädt…</td></tr>`;

    const filters = getAuditFilters();
    let ranking = await api('/api/admin/logging/ranking?' + qs(filters)) || [];
    
    if (filters.username) {
       ranking = ranking.filter(r => (r.username || '').toLowerCase().includes(filters.username));
    }
    auditRanking = ranking;

    if (!auditRanking.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="color:var(--text-muted);text-align:center;padding:var(--space-8)">Keine Werte für den gewählten Filter.</td></tr>`;
      return;
    }

    tbody.innerHTML = auditRanking.map((r, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>
          <a href="#" style="color:var(--primary);text-decoration:none;font-weight:600"
             onclick="loadAuditUserLog(${r.user_id}, '${jsEsc(r.username)}');return false;">
            ${esc(r.username)}
          </a>
        </td>
        <td>${Number(r.session_count || 0)}</td>
        <td>${fmtDuration(r.total_seconds || 0)}</td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="4" style="color:var(--error);text-align:center;padding:var(--space-8)">${esc(e.message)}</td></tr>`;
  }
}

async function loadAuditUserLog(userId, username) {
  auditSelectedUser = { id: userId, username };
  document.getElementById('detail-title').textContent = `Sitzungen von ${username}`;
  openModal('user-detail-modal');

  const tbody = document.getElementById('detail-body');
  tbody.innerHTML = `<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:var(--space-4)">Lädt…</td></tr>`;
  document.getElementById('detail-total').textContent = "";

  try {
    const filters = getAuditFilters();
    auditUserSessions = await api('/api/admin/logging/user/' + userId + '?' + qs(filters)) || [];
    
    if (!auditUserSessions.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:var(--space-4)">Keine Sitzungen im Zeitraum.</td></tr>`;
      return;
    }

    let totalSec = 0;
    tbody.innerHTML = auditUserSessions.map(s => {
      totalSec += s.duration || 0;
      return `<tr>
        <td style="font-size:var(--text-xs);white-space:nowrap">${fmtDate(s.started_at)}</td>
        <td style="font-size:var(--text-xs);white-space:nowrap">${fmtDate(s.ended_at)}</td>
        <td>${fmtDuration(s.duration)}</td>
        <td style="font-size:var(--text-xs)">${esc(s.image || '—')}</td>
        <td style="font-size:var(--text-xs)">${esc(s.container_name || '—')}</td>
        <td style="font-size:var(--text-xs);color:var(--text-muted)">${esc(s.container_ip || '—')}</td>
      </tr>`;
    }).join('');
    document.getElementById('detail-total').textContent = `Gesamtdauer: ${fmtDuration(totalSec)}`;
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--error);text-align:center;padding:var(--space-4)">${esc(e.message)}</td></tr>`;
  }
}

function exportLog() {
  const rows = [['Nutzer', 'Sitzungen', 'Gesamtzeit (s)']];
  auditRanking.forEach(r => {
    rows.push([ r.username || '', Number(r.session_count || 0), Math.floor(Number(r.total_seconds) || 0) ]);
  });
  const csv = rows.map(r => r.map(c => '"' + String(c).split('"').join('""') + '"').join(',')).join(String.fromCharCode(13) + String.fromCharCode(10));
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = 'audit-ranking.csv';
  a.click();
}

function exportUserLog() {
  if (!auditSelectedUser || !auditUserSessions.length) return;
  const rows = [['Start', 'Ende', 'Dauer (s)', 'Docker-Image', 'Container', 'IP']];
  auditUserSessions.forEach(s => {
    rows.push([
      s.started_at || '', s.ended_at || '', Math.floor(Number(s.duration) || 0),
      s.image || '', s.container_name || '', s.container_ip || ''
    ]);
  });
  const csv = rows.map(r => r.map(c => '"' + String(c).split('"').join('""') + '"').join(',')).join(String.fromCharCode(13) + String.fromCharCode(10));
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = 'audit-user-' + auditSelectedUser.username + '.csv';
  a.click();
}


// ── Utilities ──────────────────────────────────────────────────────────
function esc(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtDate(s) {
  if (s === null || s === undefined || s === '') return '—';

  if (typeof s === 'number') {
    return new Date(s * 1000).toLocaleString('de-DE', {
      day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'
    });
  }

  const v = String(s);
  return new Date(v + (v.endsWith('Z') ? '' : 'Z')).toLocaleString('de-DE', {
    day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'
  });
}
</script>
</body>
</html>"""