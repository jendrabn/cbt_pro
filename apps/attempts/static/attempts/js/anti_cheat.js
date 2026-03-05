(function attachExamRoomAntiCheat(windowObj, documentObj) {
    function requestFullscreen() {
        const element = documentObj.documentElement;
        if (!element) {
            return Promise.resolve(false);
        }
        const method = element.requestFullscreen || element.webkitRequestFullscreen || element.msRequestFullscreen;
        if (!method) {
            return Promise.resolve(false);
        }
        try {
            const result = method.call(element);
            if (result && typeof result.then === "function") {
                return result.then(() => true).catch(() => false);
            }
            return Promise.resolve(true);
        } catch (error) {
            return Promise.resolve(false);
        }
    }

    function isFullscreen() {
        return Boolean(
            documentObj.fullscreenElement ||
            documentObj.webkitFullscreenElement ||
            documentObj.msFullscreenElement
        );
    }

    function createViolationThrottle(intervalMs = 3000) {
        const lastSentAt = {};
        return (type) => {
            const now = Date.now();
            const last = lastSentAt[type] || 0;
            if ((now - last) < intervalMs) {
                return false;
            }
            lastSentAt[type] = now;
            return true;
        };
    }

    function installGuards({
        detectTabSwitch = true,
        requireFullscreen = true,
        onViolation = () => {},
        onFullscreenStateChange = () => {},
    }) {
        const shouldReport = createViolationThrottle();
        const listeners = [];

        const bind = (target, event, handler) => {
            target.addEventListener(event, handler);
            listeners.push(() => target.removeEventListener(event, handler));
        };

        if (detectTabSwitch) {
            bind(documentObj, "visibilitychange", () => {
                if (documentObj.hidden && shouldReport("tab_switch")) {
                    onViolation("tab_switch", "Sistem mendeteksi perpindahan tab atau jendela.");
                }
            });

            bind(windowObj, "blur", () => {
                if (shouldReport("tab_switch")) {
                    onViolation("tab_switch", "Fokus jendela ujian terdeteksi berpindah.");
                }
            });
        }

        bind(documentObj, "copy", () => {
            if (shouldReport("copy_attempt")) {
                onViolation("copy_attempt", "Aksi salin terdeteksi saat ujian berlangsung.");
            }
        });

        bind(documentObj, "paste", () => {
            if (shouldReport("paste_attempt")) {
                onViolation("paste_attempt", "Aksi tempel terdeteksi saat ujian berlangsung.");
            }
        });

        bind(documentObj, "contextmenu", (event) => {
            event.preventDefault();
            if (shouldReport("right_click")) {
                onViolation("right_click", "Klik kanan diblokir selama ujian.");
            }
        });

        if (requireFullscreen) {
            bind(documentObj, "fullscreenchange", () => {
                const active = isFullscreen();
                onFullscreenStateChange(active);
                if (!active && shouldReport("fullscreen_exit")) {
                    onViolation("fullscreen_exit", "Anda keluar dari mode fullscreen.");
                }
            });
        }

        return {
            destroy() {
                listeners.forEach((remove) => remove());
            },
            requestFullscreen,
            isFullscreen,
        };
    }

    windowObj.ExamRoomAntiCheat = {
        installGuards,
        requestFullscreen,
        isFullscreen,
    };
})(window, document);
