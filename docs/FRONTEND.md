# Frontend Stack & Styling Guide — CBT Pro Application

## Table of Contents

1. [Stack Overview](#1-stack-overview)
2. [Technology Details](#2-technology-details)
3. [Design System & Custom CSS](#3-design-system--custom-css)
4. [Base Templates](#4-base-templates)
5. [Layout Architecture](#5-layout-architecture)
6. [Reusable Components](#6-reusable-components)
7. [Page-Specific Guidelines](#7-page-specific-guidelines)
8. [JavaScript Patterns](#8-javascript-patterns)
9. [File Organization](#9-file-organization)
10. [Best Practices](#10-best-practices)
11. [CDN Quick Reference](#11-cdn-quick-reference)

---

## 1. Stack Overview

| #   | Technology           | Version | Purpose                        |
| --- | -------------------- | ------- | ------------------------------ |
| 1   | Django Templates     | 5.x     | Server-side HTML rendering     |
| 2   | Bootstrap 5          | v5.3.2  | CSS framework & UI components  |
| 3   | Remix Icon           | v4.0.0  | Icon library (2,800+ icons)    |
| 4   | Inter (Google Fonts) | latest  | Primary typography             |
| 5   | Alpine.js            | v3.13.5 | Lightweight JS reactivity      |
| 6   | Axios                | v1.6.2  | HTTP/AJAX calls                |
| 7   | Chart.js             | v4.4.1  | Data visualization             |
| 8   | TinyMCE              | v6+     | Rich text editor for questions |
| 9   | SortableJS           | v1.15.2 | Drag & drop question ordering  |

**Design Principles:**

- **Modern & Consistent** — unified visual language across all pages
- **Bootstrap-first** — use native Bootstrap components before writing custom CSS
- **Remix Icon only** — no emoji as icons, no other icon libraries
- **Inter font** — loaded from Google Fonts, applied globally
- **Light mode only** — no dark mode toggle
- **Responsive** — mobile-first, works on all screen sizes
- **Collapsible Sidebar** — Admin & Teacher only; Student uses topbar-only layout
- **Dynamic branding** — colors & logo from `branding` context (System Settings)

---

## 2. Technology Details

### 2.1 Bootstrap 5

CDN — load in `<head>` (CSS) and before `</body>` (JS):

```html
<link
  href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
  rel="stylesheet"
/>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
```

Bootstrap components used in this project:

- **Layout:** `.container`, `.container-fluid`, `.row`, `.col-*`, `.g-*`
- **Navigation:** `.navbar`, `.nav`, `.nav-tabs`, `.nav-pills`, `.dropdown`, `.offcanvas`
- **Content:** `.card`, `.table`, `.badge`, `.alert`, `.progress`, `.list-group`
- **Forms:** `.form-control`, `.form-select`, `.form-check`, `.input-group`, `.form-floating`
- **UI:** `.modal`, `.offcanvas`, `.toast`, `.spinner-border`, `.placeholder`
- **Utilities:** spacing (`m-*`, `p-*`), display (`d-*`), flex, text, shadow, rounded

---

### 2.2 Remix Icon

CDN — load in `<head>`:

```html
<link
  href="https://cdn.jsdelivr.net/npm/remixicon@4.0.0/fonts/remixicon.css"
  rel="stylesheet"
/>
```

Basic usage:

```html
<i class="ri-home-line"></i>
<!-- outline variant -->
<i class="ri-home-fill"></i>
<!-- solid variant -->
<i class="ri-home-line ri-lg"></i>
<!-- 1.33em -->
<i class="ri-home-line ri-xl"></i>
<!-- 1.5em -->
<i class="ri-home-line ri-2x"></i>
<!-- 2em -->
<i class="ri-home-line text-primary"></i>
<!-- Bootstrap color -->
```

**Complete CBT icon reference:**

```html
<!-- Navigation & Layout -->
<i class="ri-dashboard-line"></i>
<!-- Dashboard -->
<i class="ri-menu-line"></i>
<!-- Hamburger / toggle sidebar -->
<i class="ri-menu-fold-line"></i>
<!-- Collapse sidebar -->
<i class="ri-menu-unfold-line"></i>
<!-- Expand sidebar -->
<i class="ri-close-line"></i>
<!-- Close / X -->
<i class="ri-arrow-left-line"></i>
<!-- Back / Previous -->
<i class="ri-arrow-right-line"></i>
<!-- Next -->
<i class="ri-arrow-left-s-line"></i>
<!-- Breadcrumb separator -->
<i class="ri-logout-box-r-line"></i>
<!-- Logout -->
<i class="ri-login-box-line"></i>
<!-- Login -->
<i class="ri-home-line"></i>
<!-- Home -->

<!-- User & Auth -->
<i class="ri-user-line"></i>
<!-- User -->
<i class="ri-user-add-line"></i>
<!-- Add user -->
<i class="ri-group-line"></i>
<!-- Class / Group -->
<i class="ri-lock-line"></i>
<!-- Password -->
<i class="ri-shield-user-line"></i>
<!-- Admin role -->
<i class="ri-account-circle-line"></i>
<!-- Profile -->
<i class="ri-user-settings-line"></i>
<!-- User settings -->
<i class="ri-camera-line"></i>
<!-- Profile photo -->

<!-- Questions & Exams -->
<i class="ri-questionnaire-line"></i>
<!-- Question bank -->
<i class="ri-question-line"></i>
<!-- Question -->
<i class="ri-file-list-line"></i>
<!-- Exam list -->
<i class="ri-file-list-3-line"></i>
<!-- Exam detail -->
<i class="ri-file-add-line"></i>
<!-- Create exam -->
<i class="ri-radio-button-line"></i>
<!-- Multiple choice -->
<i class="ri-article-line"></i>
<!-- Essay -->
<i class="ri-input-method-line"></i>
<!-- Short answer -->
<i class="ri-image-line"></i>
<!-- Question image -->
<i class="ri-book-open-line"></i>
<!-- Subject -->

<!-- Exam Room -->
<i class="ri-time-line"></i>
<!-- Timer -->
<i class="ri-alarm-warning-line"></i>
<!-- Time warning -->
<i class="ri-bookmark-line"></i>
<!-- Mark for review (empty) -->
<i class="ri-bookmark-fill"></i>
<!-- Marked (filled) -->
<i class="ri-send-plane-line"></i>
<!-- Submit (outline) -->
<i class="ri-send-plane-fill"></i>
<!-- Submit (filled) -->
<i class="ri-save-line"></i>
<!-- Auto-save -->
<i class="ri-fullscreen-line"></i>
<!-- Fullscreen -->
<i class="ri-grid-line"></i>
<!-- Question map grid -->
<i class="ri-repeat-line"></i>
<!-- Retake / repeat -->

<!-- Monitoring -->
<i class="ri-eye-line"></i>
<!-- Monitor / View -->
<i class="ri-eye-off-line"></i>
<!-- Hide -->
<i class="ri-camera-line"></i>
<!-- Screenshot -->
<i class="ri-shield-check-line"></i>
<!-- Anti-cheat / secure -->
<i class="ri-broadcast-line"></i>
<!-- Announcement -->
<i class="ri-user-received-line"></i>
<!-- Student joined -->
<i class="ri-error-warning-line"></i>
<!-- Violation alert -->

<!-- Results & Analytics -->
<i class="ri-bar-chart-line"></i>
<!-- Bar chart -->
<i class="ri-line-chart-line"></i>
<!-- Line chart -->
<i class="ri-pie-chart-2-line"></i>
<!-- Pie / donut chart -->
<i class="ri-medal-line"></i>
<!-- Score / award -->
<i class="ri-trophy-line"></i>
<!-- Top score -->
<i class="ri-file-chart-line"></i>
<!-- Report -->
<i class="ri-star-line"></i>
<!-- Final score mark -->

<!-- CRUD Actions -->
<i class="ri-add-line"></i>
<!-- Add -->
<i class="ri-edit-line"></i>
<!-- Edit -->
<i class="ri-delete-bin-line"></i>
<!-- Delete -->
<i class="ri-search-line"></i>
<!-- Search -->
<i class="ri-filter-line"></i>
<!-- Filter -->
<i class="ri-download-line"></i>
<!-- Export / Download -->
<i class="ri-upload-line"></i>
<!-- Import / Upload -->
<i class="ri-refresh-line"></i>
<!-- Refresh -->
<i class="ri-file-copy-line"></i>
<!-- Duplicate -->
<i class="ri-more-2-fill"></i>
<!-- More actions (kebab) -->

<!-- Status -->
<i class="ri-checkbox-circle-line text-success"></i>
<!-- Success / Passed -->
<i class="ri-close-circle-line text-danger"></i>
<!-- Failed -->
<i class="ri-time-line text-warning"></i>
<!-- In progress -->
<i class="ri-error-warning-line text-danger"></i>
<!-- Error -->
<i class="ri-information-line text-info"></i>
<!-- Info -->
<i class="ri-draft-line text-secondary"></i>
<!-- Draft -->

<!-- System -->
<i class="ri-settings-line"></i>
<!-- Settings -->
<i class="ri-notification-line"></i>
<!-- Notifications -->
<i class="ri-mail-line"></i>
<!-- Email -->
<i class="ri-database-line"></i>
<!-- Database -->
<i class="ri-shield-line"></i>
<!-- Security -->
<i class="ri-palette-line"></i>
<!-- Branding / Theme -->
<i class="ri-global-line"></i>
<!-- Language / Timezone -->
<i class="ri-server-line"></i>
<!-- Server / System -->
```

Browse all 2,800+ icons: **<https://remixicon.com>**

---

### 2.3 Inter Font (Google Fonts)

Load in `<head>` of `base.html`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
  rel="stylesheet"
/>
```

Apply globally in `custom.css`:

```css
body {
  font-family:
    "Inter",
    system-ui,
    -apple-system,
    sans-serif;
  font-size: 0.9rem;
  color: #1e293b;
}
```

---

### 2.4 Alpine.js

CDN — load with `defer` before `</body>`:

```html
<script
  defer
  src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.5/dist/cdn.min.js"
></script>
```

**Key directives:**

| Directive               | Purpose                                |
| ----------------------- | -------------------------------------- |
| `x-data="{ key: val }"` | Declare component state                |
| `x-init="expression"`   | Run on component init                  |
| `x-show="condition"`    | Show/hide (keeps in DOM)               |
| `x-if="condition"`      | Render/remove from DOM                 |
| `x-for="item in list"`  | Loop (must wrap `<template>`)          |
| `x-model="prop"`        | Two-way input binding                  |
| `x-text="prop"`         | Set text content                       |
| `:attr="val"`           | Bind any HTML attribute                |
| `@event="handler"`      | Listen to DOM event                    |
| `@event.debounce.500ms` | Debounced event                        |
| `x-ref="name"`          | Reference DOM element via `$refs.name` |
| `x-cloak`               | Hide element until Alpine initialises  |
| `x-transition`          | CSS transition on show/hide            |

**Common patterns:**

```html
<!-- 1. Sidebar collapse toggle -->
<div x-data="{ sidebarOpen: true }">
  <button @click="sidebarOpen = !sidebarOpen">
    <i :class="sidebarOpen ? 'ri-menu-fold-line' : 'ri-menu-unfold-line'"></i>
  </button>
  <nav :class="sidebarOpen ? 'sidebar-expanded' : 'sidebar-collapsed'">
    <!-- sidebar content -->
  </nav>
</div>

<!-- 2. Loading button state -->
<div x-data="{ loading: false }">
  <button
    class="btn btn-primary"
    :disabled="loading"
    @click="loading = true; $el.form.submit()"
  >
    <span
      class="spinner-border spinner-border-sm me-2"
      x-show="loading"
      x-cloak
    ></span>
    <span x-text="loading ? 'Menyimpan...' : 'Simpan'"></span>
  </button>
</div>

<!-- 3. Password show/hide -->
<div class="input-group" x-data="{ show: false }">
  <input
    :type="show ? 'text' : 'password'"
    class="form-control"
    name="password"
    placeholder="Password"
    required
  />
  <button class="btn btn-outline-secondary" type="button" @click="show = !show">
    <i :class="show ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
  </button>
</div>

<!-- 4. Tabs with Alpine -->
<div x-data="{ tab: 'info' }">
  <ul class="nav nav-tabs mb-3">
    <li class="nav-item">
      <button
        class="nav-link"
        :class="{ active: tab === 'info' }"
        @click="tab = 'info'"
      >
        <i class="ri-information-line me-1"></i>Info
      </button>
    </li>
    <li class="nav-item">
      <button
        class="nav-link"
        :class="{ active: tab === 'settings' }"
        @click="tab = 'settings'"
      >
        <i class="ri-settings-line me-1"></i>Settings
      </button>
    </li>
  </ul>
  <div x-show="tab === 'info'">Info content</div>
  <div x-show="tab === 'settings'">Settings content</div>
</div>

<!-- 5. Dynamic options list (Question form) -->
<div x-data="{ options: ['', '', '', ''] }">
  <template x-for="(opt, i) in options" :key="i">
    <div class="input-group mb-2">
      <span
        class="input-group-text fw-bold"
        x-text="['A','B','C','D','E'][i]"
      ></span>
      <input
        type="text"
        class="form-control"
        x-model="options[i]"
        :name="`option_${['A','B','C','D','E'][i]}`"
        :placeholder="`Pilihan ${['A','B','C','D','E'][i]}`"
        required
      />
      <button
        class="btn btn-outline-danger"
        type="button"
        x-show="options.length > 2"
        @click="options.splice(i, 1)"
      >
        <i class="ri-delete-bin-line"></i>
      </button>
    </div>
  </template>
  <button
    class="btn btn-outline-secondary btn-sm"
    type="button"
    x-show="options.length < 5"
    @click="options.push('')"
  >
    <i class="ri-add-line me-1"></i>Tambah Pilihan
  </button>
</div>
```

---

### 2.5 Axios

CDN — load before `</body>`, after Bootstrap JS:

```html
<script src="https://cdn.jsdelivr.net/npm/axios@1.6.2/dist/axios.min.js"></script>
```

**Global setup in `static/js/main.js`:**

```javascript
// ─── CSRF Token ─────────────────────────────────────────────────────
function getCookie(name) {
  let val = null;
  if (document.cookie) {
    document.cookie.split(";").forEach((c) => {
      const [k, v] = c.trim().split("=");
      if (k === name) val = decodeURIComponent(v);
    });
  }
  return val;
}
axios.defaults.headers.common["X-CSRFToken"] = getCookie("csrftoken");

// ─── Global Response Interceptor ────────────────────────────────────
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    if (status === 403) window.location.href = "/login/";
    else if (status === 500) showToast("Server error. Coba lagi.", "danger");
    return Promise.reject(error);
  },
);

// ─── Global Toast Helper ────────────────────────────────────────────
function showToast(message, type = "success") {
  window.dispatchEvent(
    new CustomEvent("show-toast", {
      detail: { message, type },
    }),
  );
}

// ─── Confirm Modal Helper ────────────────────────────────────────────
function openConfirmModal({
  title,
  message,
  label = "Hapus",
  btnClass = "btn-danger",
  onConfirm,
}) {
  document.getElementById("confirmTitle").textContent = title;
  document.getElementById("confirmMessage").textContent = message;
  const btn = document.getElementById("confirmActionBtn");
  btn.textContent = label;
  btn.className = `btn ${btnClass}`;
  const newBtn = btn.cloneNode(true);
  btn.parentNode.replaceChild(newBtn, btn);
  newBtn.addEventListener("click", () => {
    bootstrap.Modal.getInstance(document.getElementById("confirmModal")).hide();
    onConfirm();
  });
  new bootstrap.Modal(document.getElementById("confirmModal")).show();
}
```

---

### 2.6 Chart.js

CDN — load only on pages that need it via `{% block extra_js %}`:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
```

---

### 2.7 TinyMCE

```bash
pip install django-tinymce
```

```python
# settings.py
INSTALLED_APPS = ['tinymce', ...]
TINYMCE_DEFAULT_CONFIG = {
    'height': 350,
    'menubar': False,
    'plugins': 'advlist autolink lists link image charmap anchor',
    'toolbar': 'undo redo | bold italic underline | bullist numlist | link image | charmap',
    'content_style': "body { font-family: 'Inter', sans-serif; font-size: 15px; }",
}
```

---

### 2.8 SortableJS

CDN — load only on exam creation / question ordering pages:

```html
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"></script>
```

```javascript
const list = document.getElementById("question-list");
new Sortable(list, {
  animation: 150,
  handle: ".drag-handle",
  ghostClass: "sortable-ghost",
  onEnd: async () => {
    const order = [...list.querySelectorAll(".question-item")].map((el, i) => ({
      id: el.dataset.questionId,
      order: i + 1,
    }));
    await axios.post("/api/exams/reorder-questions/", { order });
  },
});
```

---

## 3. Design System & Custom CSS

> **Arsitektur CSS:** Styling didistribusikan dalam 2 file global:
>
> | File                    | Fungsi                                       | Isi                                                                      |
> | ----------------------- | -------------------------------------------- | ------------------------------------------------------------------------ |
> | `static/css/theme.css`  | Override/customize default Bootstrap classes | Typography, card, table, form, button, modal, pagination overrides       |
> | `static/css/custom.css` | Custom component classes                     | Sidebar, topbar, badge-status, stat-card, empty-state, page-header, dll. |
>
> **Urutan load di `base.html`:** Bootstrap CSS → Remix Icon → `theme.css` → `custom.css`
>
> **File CSS per-app** (`exams.css`, `questions.css`, `dashboard_pages.css`) **dihapus** — semua styling dipindahkan ke `theme.css` dan `custom.css`.

### 3.1 Color System

Warna primer diambil dari `branding.primary_color` (System Settings), di-inject sebagai CSS variable di `base.html`. Semua komponen menggunakan variable ini agar branding konsisten.

```css
/* Di base.html (inline style, server-rendered) */
:root {
    --cbt-primary:        {{ branding.primary_color|default:'#0d6efd' }};
}
```

Kemudian di `theme.css`, variabel-variabel global didefinisikan:

```css
/* static/css/theme.css */
:root {
  --cbt-font: "Inter", system-ui, -apple-system, sans-serif;
  --cbt-bg: #f3f6fb;
  --cbt-ink: #0f172a;
  --cbt-muted: #64748b;
  --cbt-border: #dbe4f0;
  --cbt-radius: 0.75rem;
  --cbt-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --cbt-shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
}
```

Dan di `custom.css`, variabel khusus untuk sidebar:

```css
/* static/css/custom.css */
:root {
  --sidebar-width: 260px;
  --sidebar-width-collapsed: 72px;
  --sidebar-bg: #0f1b2d;
  --sidebar-bg-soft: #13233a;
  --sidebar-text: #95a7c1;
  --sidebar-text-active: #ffffff;
  --topbar-height: 64px;
}
```

Bootstrap semantic colors (built-in, no override):

```
--bs-primary:   #0d6efd   (Blue  overridden by --cbt-primary via JS if needed)
--bs-secondary: #6c757d   (Gray)
--bs-success:   #198754   (Green)
--bs-danger:    #dc3545   (Red)
--bs-warning:   #ffc107   (Yellow)
--bs-info:      #0dcaf0   (Cyan)
--bs-light:     #f8f9fa
--bs-dark:      #212529
```

---

### 3.2 Typography

Typography overrides masuk ke `theme.css` (karena meng-override default Bootstrap):

```css
/* static/css/theme.css */
body {
  font-family: var(--cbt-font);
  color: var(--cbt-ink);
  background-color: var(--cbt-bg);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

h1,
h2,
h3,
h4,
h5,
h6 {
  font-weight: 600;
  color: var(--cbt-ink);
}
```

Kelas tipografi tambahan masuk ke `custom.css`:

```css
/* static/css/custom.css */

/* Page title in page header */
.cbt-page-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--cbt-ink);
  margin: 0;
}

/* Page subtitle */
.cbt-page-subtitle {
  font-size: 0.875rem;
  color: var(--cbt-muted);
  margin: 0.125rem 0 0;
}

/* Section heading inside page */
.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--cbt-muted);
  margin-bottom: 0.75rem;
}
```

---

### 3.3 `theme.css` — Bootstrap Overrides

> File ini berisi override/customize terhadap class default Bootstrap.
> **Catatan:** `body`, `card`, `table`, `form`, `btn`, `modal`, `pagination` di-override di sini.
> Semua variabel `--cbt-*` (font, bg, ink, muted, border, radius, shadow) didefinisikan di `:root` file ini.

```css
/* ============================================================
   static/css/theme.css
   Override/customize default Bootstrap classes.
   Loaded AFTER bootstrap.min.css, BEFORE custom.css.
   ============================================================ */

/* --- CSS Variables (global) --- */
:root {
  --cbt-font: "Inter", system-ui, -apple-system, sans-serif;
  --cbt-bg: #f3f6fb;
  --cbt-ink: #0f172a;
  --cbt-muted: #64748b;
  --cbt-border: #dbe4f0;
  --cbt-radius: 0.75rem;
  --cbt-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --cbt-shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* --- Body / Typography --- */
body {
  font-family: var(--cbt-font);
  color: var(--cbt-ink);
  background-color: var(--cbt-bg);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* ... additional theme.css overrides: card, table, form, btn, modal, pagination ...
   Lihat docs/UI_REDESIGN_PLAN.md Section 3.2 untuk daftar lengkap override. */
```

### 3.4 `custom.css` — Custom Components

> File ini berisi class-class custom yang tidak ada di Bootstrap.
> **Catatan:** Kode di bawah masih menggunakan variabel naming lama (akan dimigrasi saat implementasi).
> Untuk referensi naming terbaru, gunakan `docs/UI_REDESIGN_PLAN.md` Section 3.3.
>
> **Mapping variabel lama → baru:**
> | Lama | Baru |
> |------|------|
> | `--cbt-sidebar-width` | `--sidebar-width` |
> | `--cbt-sidebar-bg` | `--sidebar-bg` |
> | `--cbt-sidebar-collapsed-width` | `--sidebar-width-collapsed` |
> | `--cbt-topbar-height` | `--topbar-height` |
> | `--cbt-sidebar-text` | `--sidebar-text` |
> | `--cbt-text-primary` | `--cbt-ink` |
> | `--cbt-text-secondary` | `--cbt-muted` |
> | `--cbt-text-muted` | `--cbt-muted` |
> | `--cbt-content-bg` | `--cbt-bg` |
> | `--cbt-sidebar-hover` | `rgba(255,255,255,0.08)` (inline) |
> | `--cbt-sidebar-active` | `var(--cbt-primary)` (inline) |
> | `.sidebar-brand` | `.cbt-sidebar-header` |
> | `.nav-link` (sidebar) | `.cbt-sidebar-link` |
> | `.student-nav-link` | `.cbt-student-nav-link` |
> | `.stat-card` / `.stat-icon` | `.cbt-stat-card` / `.cbt-stat-icon` |

```css
/* ============================================================
   static/css/custom.css
   Custom component classes — loaded AFTER theme.css.
   Prefix: cbt-* untuk semua custom components.
   ============================================================ */

/* --- Sidebar variables --- */
:root {
  --sidebar-width: 260px;
  --sidebar-width-collapsed: 72px;
  --sidebar-bg: #0f1b2d;
  --sidebar-bg-soft: #13233a;
  --sidebar-text: #95a7c1;
  --sidebar-text-active: #ffffff;
  --topbar-height: 64px;
}

/*  1. Sidebar (Admin & Teacher)  */
.cbt-sidebar {
  width: var(--sidebar-width);
  min-height: 100vh;
  background-color: var(--cbt-sidebar-bg);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.25s ease;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 1030;
}

.cbt-sidebar.collapsed {
  width: var(--cbt-sidebar-collapsed-width);
}

/* Sidebar brand / logo area */
.cbt-sidebar .sidebar-brand {
  height: var(--cbt-topbar-height);
  display: flex;
  align-items: center;
  padding: 0 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  white-space: nowrap;
  overflow: hidden;
  flex-shrink: 0;
}

.cbt-sidebar .sidebar-brand-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  flex-shrink: 0;
  border-radius: 6px;
}

.cbt-sidebar .sidebar-brand-text {
  font-size: 1rem;
  font-weight: 700;
  color: #ffffff;
  margin-left: 0.75rem;
  white-space: nowrap;
  transition: opacity 0.2s ease;
}

.cbt-sidebar.collapsed .sidebar-brand-text {
  opacity: 0;
  pointer-events: none;
}

/* Sidebar section heading */
.cbt-sidebar .sidebar-section {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(148, 163, 184, 0.5);
  padding: 1rem 1rem 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  transition: opacity 0.2s ease;
}

.cbt-sidebar.collapsed .sidebar-section {
  opacity: 0;
}

/* Sidebar nav links */
.cbt-sidebar .nav-link {
  color: var(--cbt-sidebar-text);
  border-radius: 0.5rem;
  margin: 1px 0.5rem;
  padding: 0.6rem 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
  transition:
    background-color 0.15s,
    color 0.15s;
  font-size: 0.875rem;
  font-weight: 500;
}

.cbt-sidebar .nav-link i {
  font-size: 1.1rem;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.cbt-sidebar .nav-link .nav-label {
  transition: opacity 0.2s ease;
  white-space: nowrap;
}

.cbt-sidebar.collapsed .nav-link .nav-label {
  opacity: 0;
  pointer-events: none;
}

.cbt-sidebar .nav-link:hover {
  color: #ffffff;
  background-color: var(--cbt-sidebar-hover);
}

.cbt-sidebar .nav-link.active {
  color: #ffffff;
  background-color: var(--cbt-sidebar-active);
}

/* Sidebar tooltip when collapsed */
.cbt-sidebar.collapsed .nav-link {
  position: relative;
}

/* Sidebar bottom user area */
.cbt-sidebar .sidebar-footer {
  margin-top: auto;
  padding: 0.75rem 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

/*  2. Topbar (Admin & Teacher)  */
.cbt-topbar {
  height: var(--cbt-topbar-height);
  background-color: #ffffff;
  border-bottom: 1px solid var(--cbt-border);
  display: flex;
  align-items: center;
  padding: 0 1.25rem;
  position: fixed;
  top: 0;
  right: 0;
  left: var(--cbt-sidebar-width);
  z-index: 1020;
  transition: left 0.25s ease;
  gap: 0.75rem;
}

.cbt-topbar.sidebar-collapsed {
  left: var(--cbt-sidebar-collapsed-width);
}

/* Sidebar toggle button in topbar */
.cbt-topbar .sidebar-toggle {
  background: none;
  border: none;
  color: var(--cbt-text-secondary);
  font-size: 1.25rem;
  padding: 0.25rem;
  cursor: pointer;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  transition:
    background-color 0.15s,
    color 0.15s;
}

.cbt-topbar .sidebar-toggle:hover {
  background-color: var(--cbt-content-bg);
  color: var(--cbt-text-primary);
}

/* Breadcrumb in topbar */
.cbt-topbar .topbar-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--cbt-text-secondary);
  flex-grow: 1;
}

.cbt-topbar .topbar-breadcrumb .breadcrumb-current {
  color: var(--cbt-text-primary);
  font-weight: 600;
}

/* Topbar right actions */
.cbt-topbar .topbar-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

/* Topbar icon buttons */
.topbar-icon-btn {
  background: none;
  border: none;
  color: var(--cbt-text-secondary);
  font-size: 1.2rem;
  padding: 0.35rem;
  border-radius: 0.5rem;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  transition:
    background-color 0.15s,
    color 0.15s;
}

.topbar-icon-btn:hover {
  background-color: var(--cbt-content-bg);
  color: var(--cbt-text-primary);
}

/* User avatar in topbar */
.topbar-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background-color: var(--cbt-primary);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
  overflow: hidden;
}

.topbar-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/*  3. Main content area (Admin & Teacher)  */
.cbt-main {
  margin-left: var(--cbt-sidebar-width);
  margin-top: var(--cbt-topbar-height);
  min-height: calc(100vh - var(--cbt-topbar-height));
  background-color: var(--cbt-content-bg);
  transition: margin-left 0.25s ease;
  padding: 1.5rem;
}

.cbt-main.sidebar-collapsed {
  margin-left: var(--cbt-sidebar-collapsed-width);
}

/*  4. Student Topbar (no sidebar)  */
.cbt-student-topbar {
  height: var(--cbt-topbar-height);
  background-color: #ffffff;
  border-bottom: 1px solid var(--cbt-border);
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
  position: sticky;
  top: 0;
  z-index: 1020;
  gap: 1rem;
}

.cbt-student-topbar .student-nav-link {
  color: var(--cbt-text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.4rem 0.75rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition:
    background-color 0.15s,
    color 0.15s;
  white-space: nowrap;
}

.cbt-student-topbar .student-nav-link:hover {
  background-color: var(--cbt-content-bg);
  color: var(--cbt-text-primary);
}

.cbt-student-topbar .student-nav-link.active {
  background-color: rgba(13, 110, 253, 0.08);
  color: var(--cbt-primary);
  font-weight: 600;
}

.cbt-student-main {
  background-color: var(--cbt-content-bg);
  min-height: calc(100vh - var(--cbt-topbar-height));
  padding: 1.5rem;
}

/*  5. Card enhancements  */
.card {
  border: 1px solid var(--cbt-border);
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-header {
  background-color: #ffffff;
  border-bottom: 1px solid var(--cbt-border);
  padding: 0.875rem 1.25rem;
  font-weight: 600;
  font-size: 0.9rem;
}

.card-hover {
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
  cursor: pointer;
}

.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
}

/*  6. Stat cards  */
.stat-card {
  border-radius: 0.75rem;
  border: 1px solid var(--cbt-border);
  background: #ffffff;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  flex-shrink: 0;
}

.stat-value {
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1.1;
  color: var(--cbt-text-primary);
}

.stat-label {
  font-size: 0.8rem;
  color: var(--cbt-text-muted);
  margin-top: 0.15rem;
}

.stat-change {
  font-size: 0.75rem;
  font-weight: 500;
  margin-top: 0.2rem;
}

/*  7. Table enhancements  */
.table {
  font-size: 0.875rem;
}

.table thead th {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--cbt-text-muted);
  border-bottom: 2px solid var(--cbt-border);
  padding: 0.75rem 1rem;
  white-space: nowrap;
}

.table tbody td {
  padding: 0.75rem 1rem;
  vertical-align: middle;
  border-bottom: 1px solid var(--cbt-border);
  color: var(--cbt-text-primary);
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.table tbody tr:hover td {
  background-color: #f8fafc;
}

/*  8. Exam question option items  */
.option-item {
  border: 2px solid var(--cbt-border);
  border-radius: 0.625rem;
  padding: 0.875rem 1rem;
  cursor: pointer;
  transition:
    border-color 0.15s,
    background-color 0.15s;
  margin-bottom: 0.625rem;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.option-item:hover {
  border-color: var(--cbt-primary);
  background-color: rgba(13, 110, 253, 0.04);
}

.option-item.selected {
  border-color: var(--cbt-primary);
  background-color: rgba(13, 110, 253, 0.08);
}

.option-item.correct {
  border-color: #198754;
  background-color: #d1e7dd;
}

.option-item.wrong {
  border-color: #dc3545;
  background-color: #f8d7da;
}

.option-letter {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--cbt-content-bg);
  border: 2px solid var(--cbt-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.8rem;
  flex-shrink: 0;
  transition:
    background-color 0.15s,
    border-color 0.15s,
    color 0.15s;
}

.option-item.selected .option-letter {
  background-color: var(--cbt-primary);
  border-color: var(--cbt-primary);
  color: #ffffff;
}

/*  9. Exam room timer  */
.timer-display {
  font-size: 2rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.05em;
  line-height: 1;
}

.timer-warning {
  color: #f59e0b !important;
  animation: timer-pulse 1s ease-in-out infinite;
}

.timer-danger {
  color: #dc3545 !important;
  animation: timer-pulse 0.5s ease-in-out infinite;
}

@keyframes timer-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/*  10. Question navigation grid buttons  */
.question-nav-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  font-size: 0.78rem;
  font-weight: 600;
  border-radius: 0.5rem;
}

/*  11. Monitoring  student status cards  */
.student-status-card {
  border: 2px solid var(--cbt-border);
  border-radius: 0.75rem;
  transition: border-color 0.3s;
}

.student-status-card.status-active {
  border-color: #198754;
}
.student-status-card.status-idle {
  border-color: #f59e0b;
}
.student-status-card.status-violation {
  border-color: #dc3545;
}
.student-status-card.status-submitted {
  border-color: #6c757d;
}

/*  12. SortableJS drag handle & ghost  */
.drag-handle {
  cursor: grab;
  color: #adb5bd;
  touch-action: none;
}
.drag-handle:active {
  cursor: grabbing;
}
.sortable-ghost {
  opacity: 0.4;
  background-color: #cfe2ff;
  border-radius: 0.5rem;
}

/*  13. Difficulty badges  */
.badge-easy {
  background-color: #d1fae5;
  color: #065f46;
}
.badge-medium {
  background-color: #fef3c7;
  color: #92400e;
}
.badge-hard {
  background-color: #fee2e2;
  color: #991b1b;
}

/*  14. Status badges (exam)  */
.badge-draft {
  background-color: #f1f5f9;
  color: #64748b;
}
.badge-published {
  background-color: #dbeafe;
  color: #1d4ed8;
}
.badge-ongoing {
  background-color: #d1fae5;
  color: #065f46;
}
.badge-completed {
  background-color: #e0e7ff;
  color: #3730a3;
}
.badge-cancelled {
  background-color: #fee2e2;
  color: #991b1b;
}

/*  15. Alpine.js  hide before JS loads  */
[x-cloak] {
  display: none !important;
}

/*  16. Save status indicator  */
.save-status {
  font-size: 0.78rem;
  transition: color 0.3s;
  color: var(--cbt-text-muted);
}

/*  17. Profile page  */
.profile-avatar-wrapper {
  position: relative;
  display: inline-block;
}

.profile-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--cbt-border);
}

.profile-avatar-edit {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: var(--cbt-primary);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  cursor: pointer;
  border: 2px solid #ffffff;
}

/*  18. Landing page  */
.landing-hero {
  background: linear-gradient(135deg, #1a2332 0%, #0f172a 60%, #1e3a5f 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.landing-hero::before {
  content: "";
  position: absolute;
  top: -50%;
  right: -20%;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(13, 110, 253, 0.15) 0%,
    transparent 70%
  );
  pointer-events: none;
}

.landing-hero::after {
  content: "";
  position: absolute;
  bottom: -30%;
  left: -10%;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(99, 102, 241, 0.1) 0%,
    transparent 70%
  );
  pointer-events: none;
}

.feature-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
  margin-bottom: 1rem;
}

.stat-counter {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
}

/*  19. Responsive  mobile sidebar overlay  */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1025;
}

@media (max-width: 991.98px) {
  .cbt-sidebar {
    transform: translateX(-100%);
    transition:
      transform 0.25s ease,
      width 0.25s ease;
    width: var(--cbt-sidebar-width) !important;
  }

  .cbt-sidebar.mobile-open {
    transform: translateX(0);
  }

  .cbt-topbar {
    left: 0 !important;
  }

  .cbt-main {
    margin-left: 0 !important;
  }

  .sidebar-overlay.active {
    display: block;
  }
}

@media (max-width: 575.98px) {
  .cbt-main,
  .cbt-student-main {
    padding: 1rem;
  }

  .stat-card {
    padding: 1rem;
  }

  .topbar-breadcrumb {
    display: none;
  }
}
```

---

### 3.5 Utility Classes (dari `utilities.css` — akan dimigrasi ke `custom.css`)

> **⚠️ DEPRECATED:** File `utilities.css` akan dihapus.
> Utility classes di bawah ini akan dipindahkan ke `custom.css` saat implementasi.

```css
/* Akan dipindahkan ke static/css/custom.css */

/* Gap utilities (extra) */
.gap-xs {
  gap: 0.25rem;
}
.gap-sm {
  gap: 0.5rem;
}

/* Truncate text */
.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Smooth transitions */
.transition-all {
  transition: all 0.2s ease;
}

/* Cursor */
.cursor-pointer {
  cursor: pointer;
}

/* Min width helpers */
.min-w-0 {
  min-width: 0;
}

/* Divider with text */
.divider-text {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--cbt-text-muted);
  font-size: 0.8rem;
}
.divider-text::before,
.divider-text::after {
  content: "";
  flex: 1;
  height: 1px;
  background-color: var(--cbt-border);
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--cbt-text-muted);
}
.empty-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
  display: block;
  opacity: 0.4;
}
.empty-state p {
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}
```

---

## 4. Base Templates

### Template Hierarchy

```
templates/
 base.html                     Root: CDN, Fonts, theme.css, custom.css, JS globals
 ├── base_dashboard.html       Admin & Teacher: sidebar + topbar ({% include %} partials)
 │   ├── base_admin.html       Extends base_dashboard — admin sidebar context
 │   └── base_teacher.html     Extends base_dashboard — teacher sidebar context
 ├── base_student.html         Student: topbar-only layout
 ├── base_auth.html            Login/Auth: centered card layout
 └── landing.html              Public landing page
```

### 4.1 `base.html` Root Template

```html
{% load static %}
<!DOCTYPE html>
<html lang="id">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>
      {% block title %}{{ branding.institution_name|default:"CBT Pro" }}{%
      endblock %}
    </title>
    <link
      rel="icon"
      href="{{ branding.institution_favicon_url|default:'/static/images/favicon.ico' }}"
    />

    <!-- Google Fonts: Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
      rel="stylesheet"
    />

    <!-- Bootstrap 5 CSS -->
    <link
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
      rel="stylesheet"
    />

    <!-- Remix Icon -->
    <link
      href="https://cdn.jsdelivr.net/npm/remixicon@4.0.0/fonts/remixicon.css"
      rel="stylesheet"
    />

    <!-- Custom CSS (theme.css → custom.css, loaded AFTER Bootstrap) -->
    <link href="{% static 'css/theme.css' %}" rel="stylesheet" />
    <link href="{% static 'css/custom.css' %}" rel="stylesheet" />

    <!-- Dynamic branding variable (server-rendered) -->
    <style>
      :root {
          --cbt-primary: {{ branding.primary_color|default:'#0d6efd' }};
      }
    </style>

    {% block extra_css %}{% endblock %}
  </head>
  <body>
    {% block body %}{% endblock %}

    <!-- Toast notifications (Alpine component) -->
    {% include 'components/toast.html' %}

    <!-- Bootstrap 5 JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

    <!-- Axios -->
    <script src="https://cdn.jsdelivr.net/npm/axios@1.6.2/dist/axios.min.js"></script>

    <!-- Alpine.js (defer) -->
    <script
      defer
      src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.5/dist/cdn.min.js"
    ></script>

    <!-- App globals: CSRF + showToast + openConfirmModal -->
    <script src="{% static 'js/main.js' %}"></script>

    {% block extra_js %}{% endblock %}
  </body>
</html>
```

---

### 4.2 `base_dashboard.html` Admin & Teacher Layout

Layout: **Fixed sidebar (kiri) + Fixed topbar (atas) + Scrollable main content**

```html
{% extends 'base.html' %} {% load static %} {% block body %} {# Alpine root
manages sidebar collapse state, persisted in localStorage #}
<div x-data="dashboardLayout()" x-init="init()" class="cbt-shell d-flex">
  <!--  Sidebar Overlay (mobile)  -->
  <div
    class="cbt-sidebar-overlay"
    :class="{ active: mobileOpen }"
    @click="mobileOpen = false"
  ></div>

  <!--  Sidebar  -->
  <nav
    class="cbt-sidebar"
    :class="{ 'collapsed': collapsed, 'mobile-open': mobileOpen }"
    id="cbt-sidebar"
  >
    <!-- Brand -->
    <div class="cbt-sidebar-header">
      <img
        src="{{ branding.institution_logo_url|default:'/static/images/logo.png' }}"
        alt="Logo"
        class="cbt-sidebar-brand-logo"
        onerror="this.src='{% static 'images/logo.png' %}'"
      />
      <span class="cbt-sidebar-brand-text">
        {{ branding.institution_name|default:"CBT Pro" }}
      </span>
    </div>

    <!-- Navigation -->
    <div
      class="flex-grow-1 overflow-auto py-2"
      style="scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.1) transparent;"
    >
      {% include 'partials/_sidebar.html' %}
    </div>

    <!-- Sidebar Footer -->
    <div class="cbt-sidebar-footer">
      <a
        href="{% url 'profile' %}"
        class="cbt-sidebar-link {% if request.resolver_match.url_name == 'profile' %}active{% endif %}"
      >
        <i class="ri-account-circle-line"></i>
        <span>Profil Saya</span>
      </a>
      <form method="post" action="{% url 'logout' %}">
        {% csrf_token %}
        <button
          type="submit"
          class="cbt-sidebar-link w-100 border-0 bg-transparent text-start"
        >
          <i class="ri-logout-box-r-line"></i>
          <span>Keluar</span>
        </button>
      </form>
    </div>
  </nav>

  <!--  Right side: Topbar + Main  -->
  <div class="cbt-main-wrapper flex-grow-1 min-w-0">
    <!-- Topbar -->
    <header class="cbt-topbar" :class="{ 'sidebar-collapsed': collapsed }">
      <!-- Toggle button -->
      <button
        class="sidebar-toggle"
        @click="toggleSidebar()"
        :title="collapsed ? 'Buka sidebar' : 'Tutup sidebar'"
      >
        <i :class="collapsed ? 'ri-menu-unfold-line' : 'ri-menu-fold-line'"></i>
      </button>

      <!-- Breadcrumb (rendered from view context array) -->
      <nav
        class="cbt-topbar-breadcrumb d-none d-md-flex"
        aria-label="breadcrumb"
      >
        {% for crumb in breadcrumbs %} {% if crumb.url %}
        <a href="{{ crumb.url }}" class="text-decoration-none text-muted"
          >{{ crumb.label }}</a
        >
        <i class="ri-arrow-right-s-line text-muted"></i>
        {% else %}
        <span class="fw-semibold text-dark">{{ crumb.label }}</span>
        {% endif %} {% endfor %}
      </nav>

      <!-- Topbar Actions -->
      <div class="topbar-actions">
        <!-- Notification Bell -->
        <div class="dropdown">
          <button
            class="topbar-icon-btn position-relative"
            data-bs-toggle="dropdown"
            aria-expanded="false"
            title="Notifikasi"
          >
            <i class="ri-notification-line"></i>
            {% if unread_count %}
            <span
              class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
              style="font-size:0.55rem; padding:2px 5px;"
            >
              {{ unread_count }}
            </span>
            {% endif %}
          </button>
          <div
            class="dropdown-menu dropdown-menu-end shadow-lg border-0 p-0"
            style="min-width:320px; border-radius:0.75rem; overflow:hidden;"
          >
            <div
              class="d-flex align-items-center justify-content-between px-3 py-2 border-bottom"
            >
              <span class="fw-semibold small">Notifikasi</span>
              {% if unread_count %}
              <span class="badge bg-danger rounded-pill"
                >{{ unread_count }}</span
              >
              {% endif %}
            </div>
            <div style="max-height:320px; overflow-y:auto;">
              {% for notif in notifications %}
              <a
                class="dropdown-item px-3 py-2 {% if not notif.is_read %}bg-light{% endif %}"
                href="{{ notif.url|default:'#' }}"
              >
                <div class="d-flex gap-2 align-items-start">
                  <i
                    class="ri-information-line text-primary mt-1 flex-shrink-0"
                  ></i>
                  <div>
                    <div
                      class="small {% if not notif.is_read %}fw-semibold{% endif %}"
                    >
                      {{ notif.message }}
                    </div>
                    <div class="text-muted" style="font-size:0.72rem;">
                      {{ notif.created_at|timesince }} lalu
                    </div>
                  </div>
                </div>
              </a>
              {% empty %}
              <div class="text-center text-muted py-4 small">
                <i
                  class="ri-notification-off-line d-block mb-1"
                  style="font-size:1.5rem;"
                ></i>
                Tidak ada notifikasi
              </div>
              {% endfor %}
            </div>
            <div class="border-top text-center py-2">
              {# URL 'notification_list' — tambahkan ke apps/core/urls.py jika
              fitur notifikasi diimplementasi #}
              <a href="#" class="small text-primary text-decoration-none">
                Lihat semua
              </a>
            </div>
          </div>
        </div>

        <!-- User Menu -->
        <div class="dropdown">
          <button
            class="btn btn-link text-decoration-none p-0 d-flex align-items-center gap-2"
            data-bs-toggle="dropdown"
            aria-expanded="false"
          >
            <div class="cbt-user-avatar">
              {% if request.user.profile.profile_picture_url %}
              <img
                src="{{ request.user.profile.profile_picture_url }}"
                alt="Avatar"
              />
              {% else %} {{ request.user.first_name|slice:':1'|upper }}{{
              request.user.last_name|slice:':1'|upper }} {% endif %}
            </div>
            <div class="d-none d-lg-block text-start">
              <div
                class="fw-semibold text-dark"
                style="font-size:0.85rem; line-height:1.2;"
              >
                {{ request.user.get_full_name }}
              </div>
              <div class="text-muted" style="font-size:0.72rem;">
                {% if request.user.role == 'admin' %}Administrator {% elif
                request.user.role == 'teacher' %}Guru {% endif %}
              </div>
            </div>
            <i class="ri-arrow-down-s-line text-muted d-none d-lg-block"></i>
          </button>
          <ul
            class="dropdown-menu dropdown-menu-end shadow border-0 mt-1"
            style="border-radius:0.75rem; min-width:200px;"
          >
            <li class="px-3 py-2 border-bottom">
              <div class="fw-semibold small">
                {{ request.user.get_full_name }}
              </div>
              <div class="text-muted" style="font-size:0.75rem;">
                {{ request.user.email }}
              </div>
            </li>
            <li>
              <a class="dropdown-item py-2" href="{% url 'profile' %}">
                <i class="ri-account-circle-line me-2 text-muted"></i>Profil
                Saya
              </a>
            </li>
            {% if request.user.role == 'admin' %}
            <li>
              <a class="dropdown-item py-2" href="{% url 'system_settings' %}">
                <i class="ri-settings-line me-2 text-muted"></i>Pengaturan
              </a>
            </li>
            {% endif %}
            <li><hr class="dropdown-divider my-1" /></li>
            <li>
              <form method="post" action="{% url 'logout' %}">
                {% csrf_token %}
                <button type="submit" class="dropdown-item py-2 text-danger">
                  <i class="ri-logout-box-r-line me-2"></i>Keluar
                </button>
              </form>
            </li>
          </ul>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="cbt-main">
      {% include 'partials/_messages.html' %} {% block page_content %}{%
      endblock %}
    </main>
  </div>
</div>

<!-- Confirm Modal (shared) -->
{% include 'components/confirm_modal.html' %}

<script>
  function dashboardLayout() {
    return {
      collapsed: false,
      mobileOpen: false,
      init() {
        // Restore state from localStorage
        const saved = localStorage.getItem("cbt_sidebar_collapsed");
        this.collapsed = saved === "true";
        // Close mobile sidebar on resize
        window.addEventListener("resize", () => {
          if (window.innerWidth >= 992) this.mobileOpen = false;
        });
      },
      toggleSidebar() {
        if (window.innerWidth < 992) {
          this.mobileOpen = !this.mobileOpen;
        } else {
          this.collapsed = !this.collapsed;
          localStorage.setItem("cbt_sidebar_collapsed", this.collapsed);
        }
      },
    };
  }
</script>
{% endblock %}
```

> **Note:** Pages extending `base_dashboard.html` override `{% block page_content %}` dan `{% block title %}`. Breadcrumb didefinisikan sebagai array `breadcrumbs` di view context (bukan block).
>
> **Context requirements:** `base_dashboard.html` dan `base_student.html` membutuhkan `unread_count` (int) dan `notifications` (queryset) di context. Inject via **context processor** atau **mixin** di semua view yang extend base ini:
>
> ```python
> # apps/core/context_processors.py (tambahkan)
> def notifications_context(request):
>     if request.user.is_authenticated:
>         notifs = request.user.notifications.order_by('-created_at')[:10]
>         return {'notifications': notifs, 'unread_count': notifs.filter(is_read=False).count()}
>     return {'notifications': [], 'unread_count': 0}
> ```

---

### 4.3 `base_student.html` Student Layout (Topbar Only)

```html
{% extends 'base.html' %} {% load static %} {% block body %}
<!-- Student Topbar -->
<header class="cbt-student-topbar">
  <!-- Brand -->
  <a
    href="{% url 'student_dashboard' %}"
    class="text-decoration-none d-flex align-items-center gap-2 me-3"
  >
    <img
      src="{{ branding.institution_logo_url|default:'/static/images/logo.png' }}"
      alt="Logo"
      style="width:28px;height:28px;object-fit:contain;border-radius:6px;"
      onerror="this.src='{% static 'images/logo.png' %}'"
    />
    <span
      class="fw-bold text-dark d-none d-sm-inline"
      style="font-size:0.9rem;"
    >
      {{ branding.institution_name|default:"CBT Pro" }}
    </span>
  </a>

  <!-- Navigation Links -->
  <nav class="d-flex align-items-center gap-1 flex-grow-1">
    <a
      href="{% url 'student_dashboard' %}"
      class="cbt-student-nav-link {% if request.resolver_match.url_name == 'student_dashboard' %}active{% endif %}"
    >
      <i class="ri-dashboard-line"></i>
      <span class="d-none d-md-inline">Dashboard</span>
    </a>
    <a
      href="{% url 'student_exam_list' %}"
      class="cbt-student-nav-link {% if 'exam' in request.resolver_match.url_name %}active{% endif %}"
    >
      <i class="ri-file-list-line"></i>
      <span class="d-none d-md-inline">Ujian Saya</span>
    </a>
    <a
      href="{% url 'student_results' %}"
      class="cbt-student-nav-link {% if 'result' in request.resolver_match.url_name %}active{% endif %}"
    >
      <i class="ri-medal-line"></i>
      <span class="d-none d-md-inline">Hasil Ujian</span>
    </a>
  </nav>

  <!-- Right: Notification + User -->
  <div class="d-flex align-items-center gap-2 ms-auto">
    <!-- Notification -->
    <div class="dropdown">
      <button
        class="topbar-icon-btn position-relative"
        data-bs-toggle="dropdown"
        aria-expanded="false"
      >
        <i class="ri-notification-line"></i>
        {% if unread_count %}
        <span
          class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
          style="font-size:0.55rem;"
          >{{ unread_count }}</span
        >
        {% endif %}
      </button>
      <div
        class="dropdown-menu dropdown-menu-end shadow-lg border-0 p-0"
        style="min-width:300px; border-radius:0.75rem; overflow:hidden;"
      >
        <div class="px-3 py-2 border-bottom fw-semibold small">Notifikasi</div>
        <div style="max-height:280px; overflow-y:auto;">
          {% for notif in notifications %}
          <a
            class="dropdown-item px-3 py-2 small {% if not notif.is_read %}fw-semibold bg-light{% endif %}"
            href="{{ notif.url|default:'#' }}"
          >
            {{ notif.message }}
            <div class="text-muted fw-normal" style="font-size:0.72rem;">
              {{ notif.created_at|timesince }} lalu
            </div>
          </a>
          {% empty %}
          <div class="text-center text-muted py-3 small">
            Tidak ada notifikasi
          </div>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- User Menu -->
    <div class="dropdown">
      <button
        class="btn btn-link text-decoration-none p-0 d-flex align-items-center gap-2"
        data-bs-toggle="dropdown"
      >
        <div class="cbt-user-avatar">
          {% if request.user.profile.profile_picture_url %}
          <img
            src="{{ request.user.profile.profile_picture_url }}"
            alt="Avatar"
          />
          {% else %} {{ request.user.first_name|slice:':1'|upper }}{{
          request.user.last_name|slice:':1'|upper }} {% endif %}
        </div>
        <span
          class="fw-medium text-dark d-none d-sm-inline"
          style="font-size:0.85rem;"
        >
          {{ request.user.first_name }}
        </span>
      </button>
      <ul
        class="dropdown-menu dropdown-menu-end shadow border-0 mt-1"
        style="border-radius:0.75rem; min-width:180px;"
      >
        <li>
          <a class="dropdown-item py-2" href="{% url 'profile' %}">
            <i class="ri-account-circle-line me-2 text-muted"></i>Profil Saya
          </a>
        </li>
        <li><hr class="dropdown-divider my-1" /></li>
        <li>
          <form method="post" action="{% url 'logout' %}">
            {% csrf_token %}
            <button type="submit" class="dropdown-item py-2 text-danger">
              <i class="ri-logout-box-r-line me-2"></i>Keluar
            </button>
          </form>
        </li>
      </ul>
    </div>
  </div>
</header>

<!-- Main Content -->
<main class="cbt-student-main">
  {% include 'partials/_messages.html' %} {% block page_content %}{% endblock %}
</main>

{% include 'components/confirm_modal.html' %} {% endblock %}
```

---

## 5. Layout Architecture

### 5.1 Sidebar Navigation `partials/_sidebar.html`

```html
{# templates/partials/_sidebar.html #} {# Included inside .cbt-sidebar in
base_dashboard.html #} {# Variable `sidebar_menu` passed from base_admin.html /
base_teacher.html #} {% if request.user.role == 'admin' %}

<div class="cbt-sidebar-section">Menu Utama</div>
<a
  href="{% url 'admin_dashboard' %}"
  class="cbt-sidebar-link {% if request.resolver_match.url_name == 'admin_dashboard' %}active{% endif %}"
>
  <i class="ri-dashboard-line"></i>
  <span>Dashboard</span>
</a>

<div class="cbt-sidebar-section">Manajemen</div>
<a
  href="{% url 'user_list' %}"
  class="cbt-sidebar-link {% if 'user' in request.resolver_match.url_name %}active{% endif %}"
>
  <i class="ri-group-line"></i>
  <span>Pengguna</span>
</a>
<a
  href="{% url 'subject_list' %}"
  class="cbt-sidebar-link {% if 'subject' in request.resolver_match.url_name %}active{% endif %}"
>
  <i class="ri-book-open-line"></i>
  <span>Mata Pelajaran</span>
</a>

<div class="cbt-sidebar-section">Laporan</div>
<a
  href="{% url 'admin_analytics' %}"
  class="cbt-sidebar-link {% if 'analytics' in request.resolver_match.url_name %}active{% endif %}"
>
  <i class="ri-bar-chart-line"></i>
  <span>Analitik</span>
</a>

<div class="cbt-sidebar-section">Sistem</div>
<a
  href="{% url 'system_settings' %}"
  class="cbt-sidebar-link {% if 'settings' in request.resolver_match.url_name %}active{% endif %}"
>
  <i class="ri-settings-line"></i>
  <span>Pengaturan</span>
</a>

{% elif request.user.role == 'teacher' %}

<div class="cbt-sidebar-section">Menu Utama</div>
<a
  href="{% url 'teacher_dashboard' %}"
  class="cbt-sidebar-link {% if request.resolver_match.url_name == 'teacher_dashboard' %}active{% endif %}"
>
  <i class="ri-dashboard-line"></i>
  <span>Dashboard</span>
</a>

<div class="cbt-sidebar-section">Soal & Ujian</div>
<a
  href="{% url 'question_list' %}"
  class="cbt-sidebar-link {% if 'question' in request.resolver_match.url_name %}active{% endif %}"
>
  <i class="ri-questionnaire-line"></i>
  <span>Bank Soal</span>
</a>
<a
  href="{% url 'exam_list' %}"
  class="cbt-sidebar-link {% if 'exam' in request.resolver_match.url_name %}active{% endif %}"
>
  <i class="ri-file-list-line"></i>
  <span>Manajemen Ujian</span>
</a>

<div class="cbt-sidebar-section">Pemantauan</div>
<a
  href="{% url 'teacher_results' %}"
  class="cbt-sidebar-link {% if 'result' in request.resolver_match.url_name %}active{% endif %}"
>
  <i class="ri-bar-chart-line"></i>
  <span>Hasil & Analisis</span>
</a>
<a
  href="{% url 'monitoring_dashboard' %}"
  class="cbt-sidebar-link {% if 'monitoring' in request.resolver_match.url_name %}active{% endif %}"
>
  <i class="ri-eye-line"></i>
  <span>Monitoring Ujian</span>
</a>

{% endif %}
```

---

### 5.2 Breadcrumb Pattern (Array-based)

Breadcrumb didefinisikan sebagai **array di view context**, lalu di-render oleh `_topbar.html`.

**Di view (Python):**

```python
# apps/users/views.py
class UserListView(ListView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['breadcrumbs'] = [
            {'label': 'Dashboard', 'url': reverse('admin_dashboard')},
            {'label': 'Pengguna'},  # tanpa url = halaman saat ini
        ]
        return ctx

# Contoh nested: Edit User
class UserUpdateView(UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['breadcrumbs'] = [
            {'label': 'Dashboard', 'url': reverse('admin_dashboard')},
            {'label': 'Pengguna', 'url': reverse('user_list')},
            {'label': f'Edit {self.object.get_full_name()}'},
        ]
        return ctx
```

**Di `_topbar.html` (rendering):**

```html
{# templates/partials/_topbar.html — breadcrumb section #}
<nav class="cbt-topbar-breadcrumb d-none d-md-flex" aria-label="breadcrumb">
  {% for crumb in breadcrumbs %} {% if crumb.url %}
  <a href="{{ crumb.url }}" class="text-decoration-none text-muted"
    >{{ crumb.label }}</a
  >
  <i class="ri-arrow-right-s-line text-muted"></i>
  {% else %}
  <span class="fw-semibold text-dark">{{ crumb.label }}</span>
  {% endif %} {% endfor %}
</nav>
```

**Contoh render:**

```
🏠 Dashboard  ›  Pengguna  ›  Edit Ahmad Fauzi
     (link)         (link)       (text, current)
```

---

### 5.3 Page Header Pattern

Gunakan partial `_page_header.html` atau tulis langsung dengan class `cbt-page-header`:

```html
{# Option A: Menggunakan partial #} {% include "partials/_page_header.html" with
title="Manajemen Pengguna" subtitle="Kelola semua pengguna sistem" %} {# Option
B: Inline dengan action buttons #}
<div class="cbt-page-header">
  <div>
    <h1 class="cbt-page-title">Manajemen Pengguna</h1>
    <p class="cbt-page-subtitle">Kelola semua pengguna sistem</p>
  </div>
  <div class="d-flex gap-2 flex-wrap">
    <button class="btn btn-outline-secondary">
      <i class="ri-download-line me-1"></i>Export
    </button>
    <button
      class="btn btn-primary"
      data-bs-toggle="modal"
      data-bs-target="#addUserModal"
    >
      <i class="ri-user-add-line me-1"></i>Tambah Pengguna
    </button>
  </div>
</div>
```

> **⚠️ Perhatikan:** Button di page header menggunakan ukuran **normal** (bukan `btn-sm`).
> `btn-sm` hanya digunakan untuk action column di tabel.

---

## 6. Reusable Components

### 6.1 Toast Notification `components/toast.html`

```html
{# templates/components/toast.html #} {# Included in base.html listens for
'show-toast' custom event #}

<div
  x-data="toastManager()"
  @show-toast.window="addToast($event.detail)"
  class="toast-container position-fixed bottom-0 end-0 p-3"
  style="z-index:1100;"
  x-cloak
>
  <template x-for="toast in toasts" :key="toast.id">
    <div
      class="toast show align-items-center border-0"
      :class="`text-bg-${toast.type}`"
      role="alert"
      x-transition:enter="transition ease-out duration-300"
      x-transition:enter-start="opacity-0 translate-y-2"
      x-transition:enter-end="opacity-100 translate-y-0"
      x-transition:leave="transition ease-in duration-200"
      x-transition:leave-start="opacity-100"
      x-transition:leave-end="opacity-0"
    >
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i
            :class="{
                        'ri-checkbox-circle-line': toast.type === 'success',
                        'ri-error-warning-line':   toast.type === 'danger',
                        'ri-alert-line':            toast.type === 'warning',
                        'ri-information-line':      toast.type === 'info'
                    }"
          ></i>
          <span x-text="toast.message"></span>
        </div>
        <button
          type="button"
          class="btn-close btn-close-white me-2 m-auto"
          @click="removeToast(toast.id)"
        ></button>
      </div>
    </div>
  </template>
</div>

<script>
  function toastManager() {
    return {
      toasts: [],
      addToast({ message, type = "success", duration = 4000 }) {
        const id = Date.now();
        this.toasts.push({ id, message, type });
        setTimeout(() => this.removeToast(id), duration);
      },
      removeToast(id) {
        this.toasts = this.toasts.filter((t) => t.id !== id);
      },
    };
  }
</script>
```

---

### 6.2 Confirm Modal `components/confirm_modal.html`

```html
{# templates/components/confirm_modal.html #} {# Included in base_dashboard.html
and base_student.html #} {# Triggered via JS: openConfirmModal({ title, message,
label, btnClass, onConfirm }) #}

<div class="modal fade" id="confirmModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-sm">
    <div class="modal-content border-0 shadow-lg" style="border-radius:1rem;">
      <div class="modal-body text-center p-4">
        <div class="mb-3" style="font-size:2.5rem; color:#dc3545;">
          <i class="ri-error-warning-line"></i>
        </div>
        <h6 class="fw-bold mb-2" id="confirmTitle">Konfirmasi</h6>
        <p class="text-muted small mb-4" id="confirmMessage">
          Apakah Anda yakin?
        </p>
        <div class="d-flex gap-2 justify-content-center">
          <button
            type="button"
            class="btn btn-outline-secondary btn-sm px-4"
            data-bs-dismiss="modal"
          >
            Batal
          </button>
          <button
            type="button"
            class="btn btn-danger btn-sm px-4"
            id="confirmActionBtn"
          >
            Hapus
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

### 6.3 Pagination `components/pagination.html`

```html
{# templates/components/pagination.html #} {# Usage: {% include
'components/pagination.html' with page_obj=page_obj %} #} {% if
page_obj.has_other_pages %}
<nav aria-label="Pagination" class="mt-4">
  <ul class="pagination pagination-sm justify-content-center mb-0">
    <li class="page-item {% if not page_obj.has_previous %}disabled{% endif %}">
      <a
        class="page-link"
        href="?page={{ page_obj.previous_page_number }}{% for k,v in request.GET.items %}{% if k != 'page' %}&{{ k }}={{ v }}{% endif %}{% endfor %}"
        aria-label="Previous"
      >
        <i class="ri-arrow-left-s-line"></i>
      </a>
    </li>

    {% for num in page_obj.paginator.page_range %} {% if page_obj.number == num
    %}
    <li class="page-item active">
      <span class="page-link">{{ num }}</span>
    </li>
    {% elif num > page_obj.number|add:'-3' and num < page_obj.number|add:'3' %}
    <li class="page-item">
      <a
        class="page-link"
        href="?page={{ num }}{% for k,v in request.GET.items %}{% if k != 'page' %}&{{ k }}={{ v }}{% endif %}{% endfor %}"
      >
        {{ num }}
      </a>
    </li>
    {% endif %} {% endfor %}

    <li class="page-item {% if not page_obj.has_next %}disabled{% endif %}">
      <a
        class="page-link"
        href="?page={{ page_obj.next_page_number }}{% for k,v in request.GET.items %}{% if k != 'page' %}&{{ k }}={{ v }}{% endif %}{% endfor %}"
        aria-label="Next"
      >
        <i class="ri-arrow-right-s-line"></i>
      </a>
    </li>
  </ul>
  <p class="text-center text-muted small mt-2 mb-0">
    Halaman {{ page_obj.number }} dari {{ page_obj.paginator.num_pages }} ({{
    page_obj.paginator.count }} data)
  </p>
</nav>
{% endif %}
```

---

### 6.4 Search & Filter Bar Pattern

```html
{# Reusable search + filter bar adapt per page #}
<div class="card mb-4">
  <div class="card-body py-2">
    <form method="get" class="d-flex flex-wrap gap-2 align-items-center">
      <!-- Search -->
      <div class="input-group" style="max-width:280px;">
        <span class="input-group-text bg-white border-end-0">
          <i class="ri-search-line text-muted"></i>
        </span>
        <input
          type="text"
          name="q"
          class="form-control border-start-0 ps-0"
          placeholder="Cari..."
          value="{{ request.GET.q }}"
        />
      </div>

      <!-- Filter dropdown (example: role) -->
      <select name="role" class="form-select" style="width:auto;">
        <option value="">Semua Role</option>
        <option value="admin" {% if request.GET.role == 'admin' %}selected{% endif %}>Admin</option>
        <option value="teacher" {% if request.GET.role == 'teacher' %}selected{% endif %}>Guru</option>
        <option value="student" {% if request.GET.role == 'student' %}selected{% endif %}>Siswa</option>
      </select>

      <button type="submit" class="btn btn-primary btn-sm">
        <i class="ri-filter-line me-1"></i>Filter
      </button>

      {% if request.GET.q or request.GET.role %}
      <a href="{{ request.path }}" class="btn btn-outline-secondary btn-sm">
        <i class="ri-close-line me-1"></i>Reset
      </a>
      {% endif %}
    </form>
  </div>
</div>
```

---

### 6.5 Stat Card Pattern

```html
{# Stat card used in all dashboard overview pages #}
<div class="cbt-stat-card">
  <div class="cbt-stat-icon bg-primary bg-opacity-10 text-primary">
    <i class="ri-group-line"></i>
  </div>
  <div class="min-w-0">
    <div class="cbt-stat-value">{{ total_users }}</div>
    <div class="cbt-stat-label">Total Pengguna</div>
    <div class="cbt-stat-change text-success">
      <i class="ri-arrow-up-line"></i> +{{ new_users_this_month }} bulan ini
    </div>
  </div>
</div>
```

Stat card color variants:

```html
<!-- Primary (blue) -->
<div class="cbt-stat-icon bg-primary bg-opacity-10 text-primary">
  <i class="ri-group-line"></i>
</div>

<!-- Success (green) -->
<div class="cbt-stat-icon bg-success bg-opacity-10 text-success">
  <i class="ri-checkbox-circle-line"></i>
</div>

<!-- Warning (yellow) -->
<div class="cbt-stat-icon bg-warning bg-opacity-10 text-warning">
  <i class="ri-time-line"></i>
</div>

<!-- Danger (red) -->
<div class="cbt-stat-icon bg-danger bg-opacity-10 text-danger">
  <i class="ri-error-warning-line"></i>
</div>

<!-- Info (cyan) -->
<div class="cbt-stat-icon bg-info bg-opacity-10 text-info">
  <i class="ri-bar-chart-line"></i>
</div>
```

---

### 6.6 Data Table Pattern

```html
<div class="card">
  <div class="card-header d-flex align-items-center justify-content-between">
    <span>Daftar Pengguna</span>
    <span class="badge bg-secondary rounded-pill">{{ total }} data</span>
  </div>
  <div class="table-responsive">
    <table class="table mb-0">
      <thead>
        <tr>
          <th style="width:40px;">
            <input type="checkbox" class="form-check-input" id="selectAll" />
          </th>
          <th>Nama</th>
          <th>Email</th>
          <th>Role</th>
          <th>Status</th>
          <th style="width:120px;">Aksi</th>
        </tr>
      </thead>
      <tbody>
        {% for user in users %}
        <tr>
          <td>
            <input
              type="checkbox"
              class="form-check-input row-check"
              value="{{ user.id }}"
            />
          </td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <div
                class="cbt-user-avatar"
                style="width:32px;height:32px;font-size:0.75rem;"
              >
                {{ user.first_name|slice:':1'|upper }}{{
                user.last_name|slice:':1'|upper }}
              </div>
              <div>
                <div class="fw-medium">{{ user.get_full_name }}</div>
                <div class="text-muted small">{{ user.username }}</div>
              </div>
            </div>
          </td>
          <td class="text-muted small">{{ user.email }}</td>
          <td>
            <span
              class="badge-status
                            {% if user.role == 'admin' %}badge-role-admin
                            {% elif user.role == 'teacher' %}badge-role-teacher
                            {% else %}badge-role-student{% endif %}"
            >
              {% if user.role == 'admin' %}
              <i class="ri-shield-user-line me-1"></i>Admin {% elif user.role ==
              'teacher' %} <i class="ri-user-line me-1"></i>Guru {% else %}
              <i class="ri-user-line me-1"></i>Siswa {% endif %}
            </span>
          </td>
          <td>
            {% if user.is_active %}
            <span class="badge-status badge-status-active">
              <i class="ri-checkbox-circle-line me-1"></i>Aktif
            </span>
            {% else %}
            <span class="badge-status badge-status-inactive">
              <i class="ri-close-circle-line me-1"></i>Nonaktif
            </span>
            {% endif %}
          </td>
          <td>
            <div class="d-flex gap-1">
              <a
                href="{% url 'user_edit' user.pk %}"
                class="btn btn-sm btn-outline-primary"
                title="Edit"
              >
                <i class="ri-edit-line"></i>
              </a>
              <button
                class="btn btn-sm btn-outline-danger"
                title="Hapus"
                onclick="openConfirmModal({
                                        title: 'Hapus Pengguna',
                                        message: 'Hapus {{ user.get_full_name }}? Tindakan ini tidak dapat dibatalkan.',
                                        label: 'Hapus',
                                        btnClass: 'btn-danger',
                                        onConfirm: () => window.location.href='{% url 'user_delete' user.pk %}'
                                    })"
              >
                <i class="ri-delete-bin-line"></i>
              </button>
            </div>
          </td>
        </tr>
        {% empty %}
        <tr>
          <td colspan="6">
            <div class="cbt-empty-state">
              <i class="ri-group-line"></i>
              <p>Belum ada pengguna</p>
              <button
                class="btn btn-primary"
                data-bs-toggle="modal"
                data-bs-target="#addUserModal"
              >
                <i class="ri-user-add-line me-1"></i>Tambah Pengguna
              </button>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% if page_obj %}
  <div class="card-footer bg-white border-top">
    {% include 'components/pagination.html' with page_obj=page_obj %}
  </div>
  {% endif %}
</div>
```

---

## 7. Page-Specific Guidelines

### 7.1 Landing Page (`landing.html`)

Landing page adalah halaman publik yang **tidak** extend `base_dashboard.html` atau `base_student.html`. Ia extend langsung `base.html`.

**Sections:**

1. **Navbar** logo + nama institusi + tombol Login (jika belum login) atau Dashboard (jika sudah login)
2. **Hero** headline, subheadline, CTA button, ilustrasi/screenshot
3. **Features** 6 feature cards dengan icon Remix Icon
4. **Statistics** counter angka (siswa, ujian, institusi)
5. **How It Works** 3 langkah dengan nomor besar
6. **CTA Section** ajakan daftar / hubungi admin
7. **Footer** copyright, link

**Kondisi tombol CTA (penting):**

```html
{# Di navbar dan hero section #} {% if request.user.is_authenticated %} {% if
request.user.role == 'admin' %}
<a href="{% url 'admin_dashboard' %}" class="btn btn-primary">
  <i class="ri-dashboard-line me-2"></i>Dashboard Admin
</a>
{% elif request.user.role == 'teacher' %}
<a href="{% url 'teacher_dashboard' %}" class="btn btn-primary">
  <i class="ri-dashboard-line me-2"></i>Dashboard Guru
</a>
{% else %}
<a href="{% url 'student_dashboard' %}" class="btn btn-primary">
  <i class="ri-dashboard-line me-2"></i>Dashboard Siswa
</a>
{% endif %} {% else %}
<a href="{% url 'login' %}" class="btn btn-primary">
  <i class="ri-login-box-line me-2"></i>Masuk ke Sistem
</a>
{% endif %}
```

**Struktur template:**

```html
{% extends 'base.html' %} {% load static %} {% block title %}{{
branding.institution_name|default:"CBT Pro" }} Sistem Ujian Online{% endblock %}
{% block body %} {# Navbar #}
<nav
  class="navbar navbar-expand-lg position-absolute w-100"
  style="z-index:100;"
>
  <div class="container">
    <a class="navbar-brand d-flex align-items-center gap-2 text-white" href="/">
      <img
        src="{{ branding.institution_logo_url|default:'/static/images/logo.png' }}"
        alt="Logo"
        style="width:32px;height:32px;object-fit:contain;border-radius:6px;"
        onerror="this.src='{% static 'images/logo.png' %}'"
      />
      <span class="fw-bold"
        >{{ branding.institution_name|default:"CBT Pro" }}</span
      >
    </a>
    <div class="ms-auto">{# Conditional button see above #}</div>
  </div>
</nav>

{# Hero #}
<section class="landing-hero">
  <div class="container position-relative" style="z-index:1;">
    <div class="row align-items-center min-vh-100 py-5">
      <div class="col-lg-6 text-white">
        <span
          class="badge bg-primary bg-opacity-25 text-primary-emphasis mb-3 px-3 py-2 rounded-pill"
        >
          <i class="ri-shield-check-line me-1"></i>Platform CBT Terpercaya
        </span>
        <h1 class="display-5 fw-bold mb-4" style="line-height:1.2;">
          {{ branding.login_page_headline|default:"Ujian Online Modern & Aman"
          }}
        </h1>
        <p class="lead mb-4 opacity-75">
          {{ branding.login_page_subheadline|default:"Platform Computer Based
          Test yang mudah digunakan, aman, dan dapat dipercaya untuk semua
          jenjang pendidikan." }}
        </p>
        <div class="d-flex gap-3 flex-wrap">
          {# Conditional CTA button #}
          <a href="#features" class="btn btn-outline-light btn-lg">
            <i class="ri-information-line me-2"></i>Pelajari Fitur
          </a>
        </div>
      </div>
      <div class="col-lg-6 d-none d-lg-block">
        {# Illustration / screenshot #}
      </div>
    </div>
  </div>
</section>

{# Features #}
<section class="py-5 bg-white" id="features">
  <div class="container">
    <div class="text-center mb-5">
      <h2 class="fw-bold">Fitur Unggulan</h2>
      <p class="text-muted">Semua yang Anda butuhkan dalam satu platform</p>
    </div>
    <div class="row g-4">{# 6 feature cards #}</div>
  </div>
</section>

{# Statistics #} {# How It Works #} {# CTA #} {# Footer #} {% endblock %}
```

---

### 7.2 Login Page (`accounts/login.html`)

Login page extend `base.html` langsung (bukan dashboard/student base).

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Masuk {{ branding.institution_name|default:"CBT Pro" }}{% endblock %}

{% block body %}
<div
  class="min-vh-100 d-flex"
  {% if branding.login_page_background_url %}
  style="background-image: url('{{ branding.login_page_background_url }}'); background-size: cover; background-position: center;"
  {% else %}
  style="background: linear-gradient(135deg, #1a2332 0%, #0f172a 100%);"
  {% endif %}
>
  {# Left: Branding panel (hidden on mobile) #}
  <div
    class="d-none d-lg-flex col-lg-6 flex-column align-items-center justify-content-center text-white p-5"
  >
    <img
      src="{{ branding.institution_logo_url|default:'/static/images/logo.png' }}"
      alt="Logo"
      style="width:80px;height:80px;object-fit:contain;border-radius:16px;margin-bottom:1.5rem;"
      onerror="this.src='{% static 'images/logo.png' %}'"
    />
    <h2 class="fw-bold text-center mb-2">
      {{ branding.institution_name|default:"CBT Pro" }}
    </h2>
    <p class="text-center opacity-75 mb-0">
      {{ branding.login_page_headline|default:"Platform Ujian Online Terpercaya"
      }}
    </p>
  </div>

  {# Right: Login form #}
  <div
    class="col-12 col-lg-6 d-flex align-items-center justify-content-center p-4"
  >
    <div
      class="card border-0 shadow-lg w-100"
      style="max-width:420px; border-radius:1.25rem;"
    >
      <div class="card-body p-4 p-md-5">
        {# Mobile logo #}
        <div class="text-center mb-4 d-lg-none">
          <img
            src="{{ branding.institution_logo_url|default:'/static/images/logo.png' }}"
            alt="Logo"
            style="width:56px;height:56px;object-fit:contain;border-radius:12px;"
            onerror="this.src='{% static 'images/logo.png' %}'"
          />
        </div>

        <h4 class="fw-bold mb-1">Selamat Datang</h4>
        <p class="text-muted small mb-4">Masuk untuk melanjutkan</p>

        {% if form.errors %}
        <div class="alert alert-danger d-flex align-items-center gap-2 py-2">
          <i class="ri-error-warning-line flex-shrink-0"></i>
          <div class="small">Username atau password salah.</div>
        </div>
        {% endif %}

        <form method="post" action="{% url 'login' %}">
          {% csrf_token %}

          <div class="mb-3">
            <label class="form-label fw-medium small" for="id_username">
              Username / Email
            </label>
            <div class="input-group">
              <span class="input-group-text bg-light border-end-0">
                <i class="ri-user-line text-muted"></i>
              </span>
              <input
                type="text"
                name="username"
                id="id_username"
                class="form-control border-start-0 ps-0"
                placeholder="Masukkan username"
                value="{{ form.username.value|default:'' }}"
                autocomplete="username"
                required
                autofocus
              />
            </div>
          </div>

          <div class="mb-4" x-data="{ show: false }">
            <label class="form-label fw-medium small" for="id_password"
              >Password</label
            >
            <div class="input-group">
              <span class="input-group-text bg-light border-end-0">
                <i class="ri-lock-line text-muted"></i>
              </span>
              <input
                :type="show ? 'text' : 'password'"
                name="password"
                id="id_password"
                class="form-control border-start-0 border-end-0 ps-0"
                placeholder="Masukkan password"
                autocomplete="current-password"
                required
              />
              <button
                class="btn btn-outline-secondary border-start-0"
                type="button"
                @click="show = !show"
              >
                <i
                  :class="show ? 'ri-eye-off-line' : 'ri-eye-line'"
                  class="text-muted"
                ></i>
              </button>
            </div>
          </div>

          <div x-data="{ loading: false }">
            <button
              type="submit"
              class="btn btn-primary w-100 py-2 fw-semibold"
              :disabled="loading"
              @click="loading = true"
            >
              <span
                class="spinner-border spinner-border-sm me-2"
                x-show="loading"
                x-cloak
              ></span>
              <i class="ri-login-box-line me-2" x-show="!loading" x-cloak></i>
              <span x-text="loading ? 'Memproses...' : 'Masuk'">Masuk</span>
            </button>
          </div>

          <input type="hidden" name="next" value="{{ next }}" />
        </form>

        <p class="text-center text-muted small mt-4 mb-0">
          Lupa password? Hubungi administrator.
        </p>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

---

### 7.3 Profile Page (`accounts/profile.html`)

Split layout: kiri info + foto, kanan form edit.

> **Template location:** `apps/accounts/templates/accounts/profile.html`
>
> **Role handling:** Template ini digunakan oleh semua role (admin, teacher, student). Untuk siswa, extend `base_student.html` — gunakan kondisi:
>
> ```html
> {% if request.user.role == 'student' %} {# Extend base_student.html — gunakan
> template terpisah atau block override #} {% else %} {# Extend
> base_dashboard.html #} {% endif %}
> ```
>
> Solusi praktis: buat dua template — `profile.html` (admin/teacher, extend `base_dashboard.html`) dan `student_profile.html` (student, extend `base_student.html`).
>
> **URL names yang dibutuhkan** (tambahkan ke `apps/accounts/urls.py`):
>
> ```python
> path('profile/', ProfileView.as_view(), name='profile'),
> path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
> path('profile/change-password/', ChangePasswordView.as_view(), name='change_password'),
> ```

```html
{% extends 'base_dashboard.html' %} {% block page_content %}
<div class="row g-4">
  {# Left: Profile Card #}
  <div class="col-lg-4">
    <div class="card text-center">
      <div class="card-body p-4">
        <div class="profile-avatar-wrapper mx-auto mb-3">
          {% if user.profile.profile_picture_url %}
          <img
            src="{{ user.profile.profile_picture_url }}"
            alt="Foto Profil"
            class="profile-avatar"
          />
          {% else %}
          <div
            class="profile-avatar d-flex align-items-center justify-content-center
                                bg-primary text-white fw-bold fs-3"
          >
            {{ user.first_name|slice:':1'|upper }}{{
            user.last_name|slice:':1'|upper }}
          </div>
          {% endif %}
          <label
            for="photoInput"
            class="profile-avatar-edit"
            title="Ganti foto"
          >
            <i class="ri-camera-line"></i>
          </label>
          <input
            type="file"
            id="photoInput"
            class="d-none"
            accept="image/jpeg,image/png,image/webp"
          />
        </div>

        <h5 class="fw-bold mb-1">{{ user.get_full_name }}</h5>
        <p class="text-muted small mb-3">
          {% if user.role == 'admin' %}
          <span class="badge bg-danger bg-opacity-10 text-danger">
            <i class="ri-shield-user-line me-1"></i>Administrator
          </span>
          {% elif user.role == 'teacher' %}
          <span class="badge bg-primary bg-opacity-10 text-primary">
            <i class="ri-user-line me-1"></i>Guru
          </span>
          {% else %}
          <span class="badge bg-success bg-opacity-10 text-success">
            <i class="ri-user-line me-1"></i>Siswa
          </span>
          {% endif %}
        </p>

        <hr />

        <ul class="list-unstyled text-start small">
          <li class="d-flex align-items-center gap-2 mb-2 text-muted">
            <i class="ri-mail-line flex-shrink-0"></i>
            <span class="text-truncate">{{ user.email }}</span>
          </li>
          <li class="d-flex align-items-center gap-2 mb-2 text-muted">
            <i class="ri-user-line flex-shrink-0"></i>
            <span>{{ user.username }}</span>
          </li>
          {% if user.profile.phone %}
          <li class="d-flex align-items-center gap-2 text-muted">
            <i class="ri-phone-line flex-shrink-0"></i>
            <span>{{ user.profile.phone }}</span>
          </li>
          {% endif %}
        </ul>

        <hr />
        <p class="text-muted small mb-0">
          <i class="ri-time-line me-1"></i>
          Bergabung {{ user.date_joined|date:"d M Y" }}
        </p>
      </div>
    </div>
  </div>

  {# Right: Edit Forms #}
  <div class="col-lg-8">
    {# Tab: Info Profil / Ganti Password #}
    <div x-data="{ tab: 'info' }">
      <ul class="nav nav-tabs mb-4">
        <li class="nav-item">
          <button
            class="nav-link"
            :class="{ active: tab === 'info' }"
            @click="tab = 'info'"
          >
            <i class="ri-account-circle-line me-1"></i>Informasi Profil
          </button>
        </li>
        <li class="nav-item">
          <button
            class="nav-link"
            :class="{ active: tab === 'password' }"
            @click="tab = 'password'"
          >
            <i class="ri-lock-line me-1"></i>Ganti Password
          </button>
        </li>
      </ul>

      {# Tab: Info Profil #}
      <div x-show="tab === 'info'" x-cloak>
        <div class="card">
          <div class="card-header">Informasi Profil</div>
          <div class="card-body p-4">
            <form method="post" action="{% url 'profile_update' %}">
              {% csrf_token %}
              <div class="row g-3">
                <div class="col-sm-6">
                  <label class="form-label fw-medium small">Nama Depan</label>
                  <input
                    type="text"
                    name="first_name"
                    class="form-control"
                    value="{{ user.first_name }}"
                    required
                  />
                </div>
                <div class="col-sm-6">
                  <label class="form-label fw-medium small"
                    >Nama Belakang</label
                  >
                  <input
                    type="text"
                    name="last_name"
                    class="form-control"
                    value="{{ user.last_name }}"
                  />
                </div>
                <div class="col-12">
                  <label class="form-label fw-medium small">Email</label>
                  <input
                    type="email"
                    name="email"
                    class="form-control"
                    value="{{ user.email }}"
                    required
                  />
                </div>
                <div class="col-sm-6">
                  <label class="form-label fw-medium small">No. Telepon</label>
                  <input
                    type="tel"
                    name="phone"
                    class="form-control"
                    value="{{ user.profile.phone|default:'' }}"
                    placeholder="08xx-xxxx-xxxx"
                  />
                </div>
                {% if user.role == 'student' %}
                <div class="col-sm-6">
                  <label class="form-label fw-medium small">Kelas</label>
                  <input
                    type="text"
                    class="form-control"
                    value="{{ user.profile.class_name|default:'-' }}"
                    readonly
                    style="background-color:#f8f9fa;"
                  />
                </div>
                {% endif %}
              </div>
              <div class="mt-4 d-flex gap-2">
                <button type="submit" class="btn btn-primary">
                  <i class="ri-save-line me-1"></i>Simpan Perubahan
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {# Tab: Ganti Password #}
      <div x-show="tab === 'password'" x-cloak>
        <div class="card">
          <div class="card-header">Ganti Password</div>
          <div class="card-body p-4">
            <form method="post" action="{% url 'change_password' %}">
              {% csrf_token %}
              <div class="row g-3">
                <div class="col-12" x-data="{ show: false }">
                  <label class="form-label fw-medium small"
                    >Password Lama</label
                  >
                  <div class="input-group">
                    <input
                      :type="show ? 'text' : 'password'"
                      name="old_password"
                      class="form-control"
                      required
                    />
                    <button
                      class="btn btn-outline-secondary"
                      type="button"
                      @click="show = !show"
                    >
                      <i :class="show ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
                    </button>
                  </div>
                </div>
                <div class="col-sm-6" x-data="{ show: false }">
                  <label class="form-label fw-medium small"
                    >Password Baru</label
                  >
                  <div class="input-group">
                    <input
                      :type="show ? 'text' : 'password'"
                      name="new_password1"
                      class="form-control"
                      minlength="8"
                      required
                    />
                    <button
                      class="btn btn-outline-secondary"
                      type="button"
                      @click="show = !show"
                    >
                      <i :class="show ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
                    </button>
                  </div>
                </div>
                <div class="col-sm-6" x-data="{ show: false }">
                  <label class="form-label fw-medium small"
                    >Konfirmasi Password</label
                  >
                  <div class="input-group">
                    <input
                      :type="show ? 'text' : 'password'"
                      name="new_password2"
                      class="form-control"
                      minlength="8"
                      required
                    />
                    <button
                      class="btn btn-outline-secondary"
                      type="button"
                      @click="show = !show"
                    >
                      <i :class="show ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
                    </button>
                  </div>
                </div>
              </div>
              <div class="mt-4">
                <button type="submit" class="btn btn-warning">
                  <i class="ri-lock-line me-1"></i>Ganti Password
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

---

## 8. JavaScript Patterns

### 8.1 `static/js/main.js` Global Setup

```javascript
//  CSRF Token
function getCookie(name) {
  let val = null;
  if (document.cookie) {
    document.cookie.split(";").forEach((c) => {
      const [k, v] = c.trim().split("=");
      if (k === name) val = decodeURIComponent(v);
    });
  }
  return val;
}
axios.defaults.headers.common["X-CSRFToken"] = getCookie("csrftoken");

//  Axios Interceptors
axios.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    if (status === 403) window.location.href = "/login/";
    else if (status === 500)
      showToast("Terjadi kesalahan server. Coba lagi.", "danger");
    return Promise.reject(err);
  },
);

//  Toast Helper
function showToast(message, type = "success") {
  window.dispatchEvent(
    new CustomEvent("show-toast", {
      detail: { message, type },
    }),
  );
}

//  Confirm Modal Helper
function openConfirmModal({
  title,
  message,
  label = "Hapus",
  btnClass = "btn-danger",
  onConfirm,
}) {
  document.getElementById("confirmTitle").textContent = title;
  document.getElementById("confirmMessage").textContent = message;
  const btn = document.getElementById("confirmActionBtn");
  btn.textContent = label;
  btn.className = `btn ${btnClass}`;
  const newBtn = btn.cloneNode(true);
  btn.parentNode.replaceChild(newBtn, btn);
  newBtn.addEventListener("click", () => {
    bootstrap.Modal.getInstance(document.getElementById("confirmModal")).hide();
    onConfirm();
  });
  new bootstrap.Modal(document.getElementById("confirmModal")).show();
}

//  Select All Checkboxes
document.addEventListener("DOMContentLoaded", () => {
  const selectAll = document.getElementById("selectAll");
  if (selectAll) {
    selectAll.addEventListener("change", () => {
      document.querySelectorAll(".row-check").forEach((cb) => {
        cb.checked = selectAll.checked;
      });
    });
  }
});
```

---

### 8.2 Exam Room JS `static/js/exam-room.js`

```javascript
//  Exam Room Alpine Component
// Usage: <div x-data="examRoom(totalQuestions, attemptId)">
function examRoom(totalQ, attemptId) {
  return {
    currentQ: 1,
    answered: [],
    marked: [],
    totalQ,
    timeLeft: 0,
    timerInterval: null,
    autoSaveTimeout: null,

    //  Init
    init(durationSeconds) {
      this.timeLeft = durationSeconds;
      this.startTimer();
      this.setupAntiCheat();
    },

    //  Timer
    startTimer() {
      this.timerInterval = setInterval(() => {
        if (this.timeLeft <= 0) {
          clearInterval(this.timerInterval);
          this.submitExam();
          return;
        }
        this.timeLeft--;
      }, 1000);
    },

    get formattedTime() {
      const h = Math.floor(this.timeLeft / 3600);
      const m = Math.floor((this.timeLeft % 3600) / 60);
      const s = this.timeLeft % 60;
      if (h > 0)
        return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
      return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    },

    get timerClass() {
      if (this.timeLeft <= 60) return "timer-danger";
      if (this.timeLeft <= 300) return "timer-warning";
      return "";
    },

    //  Navigation
    goTo(num) {
      this.currentQ = num;
      document
        .getElementById(`question-${num}`)
        ?.scrollIntoView({ behavior: "smooth" });
    },

    //  Auto-save
    scheduleAutoSave(questionId, answer) {
      clearTimeout(this.autoSaveTimeout);
      this.autoSaveTimeout = setTimeout(
        () => this.saveAnswer(questionId, answer),
        800,
      );
    },

    async saveAnswer(questionId, answer) {
      const statusEl = document.getElementById("save-status");
      if (statusEl)
        statusEl.innerHTML =
          '<i class="ri-loader-4-line me-1"></i>Menyimpan...';
      try {
        await axios.post(`/api/attempts/${attemptId}/save-answer/`, {
          question_id: questionId,
          answer,
        });
        if (!this.answered.includes(this.currentQ)) {
          this.answered.push(this.currentQ);
        }
        if (statusEl) {
          statusEl.innerHTML =
            '<i class="ri-checkbox-circle-line me-1 text-success"></i>Tersimpan';
        }
      } catch {
        if (statusEl) {
          statusEl.innerHTML =
            '<i class="ri-error-warning-line me-1 text-danger"></i>Gagal menyimpan';
        }
      }
    },

    //  Mark for review
    toggleMark(num) {
      this.marked = this.marked.includes(num)
        ? this.marked.filter((n) => n !== num)
        : [...this.marked, num];
    },

    //  Submit
    openSubmitModal() {
      new bootstrap.Modal(document.getElementById("submitModal")).show();
    },

    async submitExam() {
      const modalEl = document.getElementById("submitModal");
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      try {
        const res = await axios.post(`/api/attempts/${attemptId}/submit/`);
        window.location.href = res.data.redirect_url;
      } catch {
        showToast("Gagal submit. Coba lagi.", "danger");
      }
    },

    //  Anti-cheat
    setupAntiCheat() {
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) this.reportViolation("tab_switch");
      });
      document.addEventListener("fullscreenchange", () => {
        if (!document.fullscreenElement)
          this.reportViolation("fullscreen_exit");
      });
      document.documentElement.requestFullscreen?.().catch(() => {});
    },

    async reportViolation(type) {
      try {
        await axios.post(`/api/attempts/${attemptId}/violation/`, { type });
        showToast(
          `Peringatan: ${type.replace(/_/g, " ")} terdeteksi!`,
          "warning",
        );
      } catch {
        /* silent */
      }
    },
  };
}
```

---

### 8.3 Retake Cooldown Countdown `static/js/retake-cooldown.js`

```javascript
//  Retake Cooldown Countdown
// Usage: <span data-retake-countdown="{{ retake_available_from|date:'c' }}"></span>
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-retake-countdown]").forEach((el) => {
    const target = new Date(el.dataset.retakeCountdown);
    const btn = document.getElementById(el.dataset.retakeBtn);

    function update() {
      const diff = Math.max(0, Math.floor((target - Date.now()) / 1000));
      if (diff === 0) {
        el.textContent = "Tersedia sekarang";
        if (btn) btn.disabled = false;
        return;
      }
      const m = Math.floor(diff / 60);
      const s = diff % 60;
      el.textContent = `Tersedia dalam ${m}m ${s}s`;
      if (btn) btn.disabled = true;
      setTimeout(update, 1000);
    }
    update();
  });
});
```

---

## 9. File Organization

```
cbt_project/
 static/
    css/
       theme.css            Override default Bootstrap (typography, card, table, form, button, modal, pagination)
       custom.css           Custom component styles (sidebar, topbar, badge-status, stat-card, page-header, empty-state)
    js/
       main.js              Global: CSRF, toast, confirmModal, selectAll
       exam-room.js         Alpine component for exam room
       retake-cooldown.js   Retake countdown timer
    images/
        logo.png             Default fallback logo
        favicon.ico          Default fallback favicon

 templates/
    base.html                Root: CDN, Fonts, theme.css, custom.css, JS globals
    base_dashboard.html      Admin & Teacher: sidebar + topbar ({% include %} partials)
    base_admin.html          Extends base_dashboard.html — sets admin sidebar context
    base_teacher.html        Extends base_dashboard.html — sets teacher sidebar context
    base_student.html        Student: topbar-only layout
    base_auth.html           Auth pages (Login) — centered card layout
    landing.html             Public landing page (extends base.html)
    partials/
        _sidebar.html        Server-rendered sidebar navigation (role-based)
        _topbar.html         Dashboard topbar: breadcrumb, notif, user menu
        _student_topbar.html Student horizontal navigation bar
        _messages.html       Flash messages → Bootstrap alerts
        _page_header.html    Page title + subtitle + action buttons
    components/
        pagination.html      Reusable pagination
        confirm_modal.html   Shared confirm/delete modal
        toast.html           Alpine toast notification component
        empty_state.html     Empty table/list state
        footer.html          Shared footer (landing page)

 apps/
     accounts/templates/accounts/
        login.html            Extends base_auth.html
        profile.html          Admin & Teacher profile (extends base_dashboard.html)
        student_profile.html  Student profile (extends base_student.html)
     dashboard/templates/dashboard/
        admin_dashboard.html   Extends base_admin.html
        teacher_dashboard.html Extends base_teacher.html
        student_dashboard.html Extends base_student.html
     users/templates/users/
        user_list.html         Extends base_admin.html
        user_form.html         Extends base_admin.html
     subjects/templates/subjects/
        subject_list.html      Extends base_admin.html
        subject_form.html      Extends base_admin.html
     questions/templates/questions/
        question_list.html     Extends base_teacher.html
        question_form.html     Extends base_teacher.html
     exams/templates/exams/
        exam_list.html         Extends base_teacher.html
        exam_form.html         Extends base_teacher.html — multi-step wizard
        exam_detail.html       Extends base_teacher.html
     attempts/templates/attempts/
        exam_list.html          Student exam list (extends base_student.html)
        exam_room.html          Fullscreen exam room (extends base.html)
        retake_confirm.html
        pre_retake_review.html
     monitoring/templates/monitoring/
        monitoring_dashboard.html  Extends base_teacher.html
     results/templates/results/
        teacher_results.html   Extends base_teacher.html
        student_results.html   Extends base_student.html
     core/templates/core/
        settings.html          System settings (extends base_admin.html)
     analytics/templates/analytics/
         admin_analytics.html  Extends base_admin.html
```

> **File CSS per-app yang DIHAPUS** (styling dipindahkan ke `theme.css` / `custom.css`):
>
> - ~~`apps/dashboard/static/dashboard/css/dashboard_pages.css`~~
> - ~~`apps/questions/static/questions/css/questions.css`~~
> - ~~`apps/exams/static/exams/css/exams.css`~~
> - ~~`static/css/main.css`~~ (kosong)
> - ~~`static/css/components.css`~~ (kosong)
> - ~~`static/css/utilities.css`~~ (kosong)
>
> **File JS yang DIHAPUS** (sidebar/topbar kini server-rendered via partials):
>
> - ~~`apps/dashboard/static/dashboard/js/dashboard_pages.js`~~

---

## 10. Best Practices

### Bootstrap 5

- Gunakan **komponen Bootstrap native** (Modal, Dropdown, Toast, Alert) via `data-bs-*` tidak perlu JS boilerplate
- Gunakan utility Bootstrap sebelum menulis custom CSS
- Selalu tambahkan `role=` dan `aria-*` pada elemen interaktif
- Gunakan `container-fluid` untuk halaman dashboard full-width, `container` untuk form terpusat
- Map Django message tags ke Bootstrap: Django `error` Bootstrap `danger`
- Gunakan `.table-responsive` wrapper untuk semua tabel di mobile

### Remix Icon

- **Jangan gunakan emoji sebagai ikon** selalu gunakan Remix Icon
- Gunakan variant `-line` (outline) untuk ikon navigasi dan aksi umum
- Gunakan variant `-fill` untuk status aktif/selected
- Tambahkan `me-1` atau `me-2` saat ikon diikuti teks dalam button
- Gunakan `ri-lg` atau `ri-xl` untuk ikon standalone (tanpa teks)

### Alpine.js

- Jaga `x-data` state seminimal mungkin
- Semua state modal yang butuh Alpine harus berada dalam root `x-data` yang sama
- Gunakan `@event.debounce.500ms` untuk input pencarian dan auto-save
- Gunakan `window.dispatchEvent(new CustomEvent(...))` untuk komunikasi antar komponen Alpine
- Selalu tambahkan `[x-cloak] { display: none !important; }` di custom CSS
- Gunakan `x-transition` untuk animasi show/hide yang smooth

### Axios

- Set CSRF token secara global di `main.js` jangan diulang per request
- Selalu wrap `await` dalam `try/catch`
- Selalu beri feedback ke user via `showToast()` untuk sukses dan gagal
- Gunakan `params: {}` untuk GET query string (bukan concatenasi URL manual)
- Handle 403 (redirect ke login) dan 500 (toast error) di interceptor global

### CSS Architecture

- **`theme.css`** — Hanya untuk override/customize default Bootstrap (body, card, table, form, button, modal, pagination)
- **`custom.css`** — Hanya untuk komponen custom yang Bootstrap tidak cover (sidebar, topbar, badge-status, stat-card, page-header, empty-state)
- **Jangan buat CSS per-app** — Semua styling global di 2 file di atas
- Gunakan CSS variables (`--cbt-*`) untuk nilai yang dipakai di banyak tempat
- Jangan gunakan `!important` kecuali terpaksa (hanya untuk `[x-cloak]`)
- Gunakan konsisten class prefix `cbt-` untuk semua custom component (e.g. `.cbt-sidebar`, `.cbt-topbar`, `.cbt-page-header`)
- Gunakan `badge-status` class system untuk semua badge (bukan `text-bg-*` atau `btn-outline-*`)

### Konsistensi UI

- Semua halaman dashboard wajib menggunakan **Page Header Pattern** (judul + deskripsi + action buttons)
- Semua halaman dengan list data wajib menggunakan **Search & Filter Bar Pattern**
- Semua konfirmasi hapus wajib menggunakan `openConfirmModal()` bukan `confirm()` native browser
- Semua notifikasi wajib menggunakan `showToast()` bukan `alert()` native browser
- Breadcrumb wajib diisi sebagai array `breadcrumbs` di view context untuk setiap halaman dashboard (lihat Section 5.2)
- Gunakan `.cbt-empty-state` untuk tampilan tabel/list kosong

### Responsivitas

- **Desktop (992px):** Sidebar expanded (260px) + topbar fixed
- **Tablet (768–991px):** Sidebar collapsed (72px, icon only) + topbar full width
- **Mobile (<768px):** Sidebar hidden (offcanvas overlay saat dibuka) + topbar full width
- State sidebar (collapsed/expanded) disimpan di `localStorage` agar persisten antar halaman
- Student layout tidak punya sidebar hanya topbar horizontal di semua ukuran layar

---

## 11. CDN Quick Reference

```html
<!--  Di <head>  -->

<!-- 1. Google Fonts: Inter -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
  rel="stylesheet"
/>

<!-- 2. Bootstrap 5 CSS -->
<link
  href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
  rel="stylesheet"
/>

<!-- 3. Remix Icon -->
<link
  href="https://cdn.jsdelivr.net/npm/remixicon@4.0.0/fonts/remixicon.css"
  rel="stylesheet"
/>

<!-- 4. Custom CSS (selalu terakhir di <head>) -->
<link href="{% static 'css/theme.css' %}" rel="stylesheet" />
<link href="{% static 'css/custom.css' %}" rel="stylesheet" />

<!--  Sebelum </body>  -->

<!-- 5. Bootstrap 5 JS Bundle (Popper.js included) -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

<!-- 6. Axios -->
<script src="https://cdn.jsdelivr.net/npm/axios@1.6.2/dist/axios.min.js"></script>

<!-- 7. Alpine.js (defer  non-blocking) -->
<script
  defer
  src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.5/dist/cdn.min.js"
></script>

<!-- 8. App globals (CSRF, showToast, openConfirmModal) -->
<script src="{% static 'js/main.js' %}"></script>

<!--  Page-specific (di {% block extra_js %})  -->

<!-- Chart.js  analytics & results pages only -->
<!-- <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script> -->

<!-- SortableJS  exam builder / question ordering only -->
<!-- <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"></script> -->

<!-- TinyMCE  question form only -->
<!-- <script src="https://cdn.tiny.cloud/1/YOUR_API_KEY/tinymce/6/tinymce.min.js"></script> -->

<!-- Exam Room JS -->
<!-- <script src="{% static 'js/exam-room.js' %}"></script> -->

<!-- Retake Cooldown JS -->
<!-- <script src="{% static 'js/retake-cooldown.js' %}"></script> -->
```
