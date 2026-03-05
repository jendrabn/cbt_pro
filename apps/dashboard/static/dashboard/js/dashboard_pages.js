const SIDEBAR_COLLAPSE_KEY = "cbt.sidebar.collapsed";

function parseJsonScript(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
        return JSON.parse(el.textContent);
    } catch {
        return null;
    }
}

function initSidebarShell() {
    const body = document.body;
    if (!body || !body.classList.contains("dashboard-body")) return;

    const sidebar = document.querySelector(".cbt-sidebar");
    const toggleBtn = document.querySelector(".cbt-sidebar-toggle");
    const overlay = document.querySelector(".cbt-sidebar-overlay");
    const hasSidebar = !!sidebar && body.classList.contains("cbt-has-sidebar");

    if (!hasSidebar || !toggleBtn) return;

    const isMobile = () => window.innerWidth < 768;
    const isTablet = () => window.innerWidth >= 768 && window.innerWidth < 992;
    const stored = localStorage.getItem(SIDEBAR_COLLAPSE_KEY);
    const shouldCollapse = stored === null ? isTablet() : stored === "1";

    if (shouldCollapse && !isMobile()) {
        body.classList.add("cbt-sidebar-collapsed");
    }

    const updateIcon = () => {
        const icon = toggleBtn.querySelector("i");
        if (!icon) return;
        const expanded = !body.classList.contains("cbt-sidebar-collapsed") && !isMobile();
        icon.className = expanded ? "ri-menu-fold-line" : "ri-menu-unfold-line";
    };

    toggleBtn.addEventListener("click", () => {
        if (isMobile()) {
            body.classList.toggle("cbt-mobile-sidebar-open");
            return;
        }

        body.classList.toggle("cbt-sidebar-collapsed");
        localStorage.setItem(
            SIDEBAR_COLLAPSE_KEY,
            body.classList.contains("cbt-sidebar-collapsed") ? "1" : "0",
        );
        updateIcon();
    });

    if (overlay) {
        overlay.addEventListener("click", () => body.classList.remove("cbt-mobile-sidebar-open"));
    }

    window.addEventListener("resize", () => {
        if (!isMobile()) body.classList.remove("cbt-mobile-sidebar-open");
        updateIcon();
    });

    updateIcon();
}

function initActivityFilter() {
    const input = document.getElementById("activityFilterInput");
    const table = document.getElementById("activityTable");
    if (!input || !table) return;

    const rows = table.querySelectorAll("tbody tr");
    input.addEventListener("input", () => {
        const keyword = input.value.trim().toLowerCase();
        rows.forEach((row) => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(keyword) ? "" : "none";
        });
    });
}

function initAdminCharts() {
    if (!window.Chart) return;

    const growthCtx = document.getElementById("adminUserGrowthChart");
    const growthData = parseJsonScript("admin-user-growth-data");
    if (growthCtx && growthData) {
        new Chart(growthCtx, {
            type: "line",
            data: {
                labels: growthData.labels || [],
                datasets: [{
                    label: "Pengguna Baru",
                    data: growthData.values || [],
                    borderColor: "#0d6efd",
                    backgroundColor: "rgba(13,110,253,0.1)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, precision: 0 } },
            },
        });
    }

    const statusCtx = document.getElementById("adminExamStatusChart");
    const statusData = parseJsonScript("admin-exam-status-data");
    if (statusCtx && statusData) {
        new Chart(statusCtx, {
            type: "doughnut",
            data: {
                labels: statusData.labels || [],
                datasets: [{
                    data: statusData.values || [],
                    backgroundColor: ["#94a3b8", "#3b82f6", "#22c55e", "#0ea5e9", "#ef4444"],
                }],
            },
            options: {
                responsive: true,
                cutout: "64%",
                plugins: { legend: { position: "bottom" } },
            },
        });
    }
}

function initTeacherChart() {
    if (!window.Chart) return;
    const ctx = document.getElementById("teacherExamPerformanceChart");
    const data = parseJsonScript("teacher-exam-performance-data");
    if (!ctx || !data) return;

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.labels || [],
            datasets: [{
                label: "Rata-rata Nilai (%)",
                data: data.values || [],
                backgroundColor: "rgba(13,110,253,0.8)",
                borderRadius: 8,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, suggestedMax: 100 },
            },
        },
    });
}

function initStudentTrendChart() {
    if (!window.Chart) return;
    const ctx = document.getElementById("studentTrendChart");
    const data = parseJsonScript("student-trend-data");
    if (!ctx || !data) return;

    new Chart(ctx, {
        type: "line",
        data: {
            labels: data.labels || [],
            datasets: [{
                label: "Nilai (%)",
                data: data.values || [],
                borderColor: "#10b981",
                backgroundColor: "rgba(16,185,129,0.12)",
                tension: 0.35,
                fill: true,
                pointRadius: 3,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, suggestedMax: 100 } },
        },
    });
}

function initCountdowns() {
    const countdownEls = document.querySelectorAll("[data-countdown]");
    if (!countdownEls.length) return;

    const updateCountdown = () => {
        const now = Date.now();
        countdownEls.forEach((el) => {
            const startRaw = el.getAttribute("data-start-time");
            const endRaw = el.getAttribute("data-end-time");
            const startTime = startRaw ? new Date(startRaw).getTime() : NaN;
            const endTime = endRaw ? new Date(endRaw).getTime() : NaN;

            if (Number.isNaN(startTime) || Number.isNaN(endTime)) {
                el.textContent = "Jadwal belum valid";
                return;
            }

            if (now < startTime) {
                const diff = startTime - now;
                const hours = Math.floor(diff / 3600000);
                const minutes = Math.floor((diff % 3600000) / 60000);
                el.textContent = `Mulai dalam ${hours}j ${minutes}m`;
                return;
            }

            if (now >= startTime && now <= endTime) {
                const diff = endTime - now;
                const hours = Math.floor(diff / 3600000);
                const minutes = Math.floor((diff % 3600000) / 60000);
                el.textContent = `Sedang berlangsung (${hours}j ${minutes}m tersisa)`;
                return;
            }

            el.textContent = "Periode ujian telah berakhir";
        });
    };

    updateCountdown();
    window.setInterval(updateCountdown, 30000);
}

document.addEventListener("DOMContentLoaded", () => {
    initSidebarShell();
    initActivityFilter();
    initAdminCharts();
    initTeacherChart();
    initStudentTrendChart();
    initCountdowns();
});
