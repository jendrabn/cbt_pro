(function examStartPreflight(windowObj, documentObj) {
    function setBadgeState(element, state, label) {
        if (!element) {
            return;
        }
        const classMap = {
            pending: "badge text-bg-secondary",
            success: "badge text-bg-success",
            warning: "badge text-bg-warning",
            danger: "badge text-bg-danger",
        };
        element.className = classMap[state] || classMap.pending;
        element.textContent = label;
    }

    function requestFullscreen(element) {
        if (!element || typeof element.requestFullscreen !== "function") {
            return Promise.reject(new Error("fullscreen_not_supported"));
        }
        return element.requestFullscreen();
    }

    function stopStream(stream) {
        if (!stream || typeof stream.getTracks !== "function") {
            return;
        }
        stream.getTracks().forEach((track) => {
            if (track && typeof track.stop === "function") {
                track.stop();
            }
        });
    }

    function bootstrapExamStart() {
        const form = documentObj.getElementById("examStartForm");
        const modalEl = documentObj.getElementById("permissionPreflightModal");
        const openBtn = documentObj.getElementById("openPermissionPreflightBtn");
        const checkMediaBtn = documentObj.getElementById("checkMediaPermissionBtn");
        const fullscreenBtn = documentObj.getElementById("requestFullscreenPermissionBtn");
        const submitBtn = documentObj.getElementById("submitExamAfterChecksBtn");
        const feedbackEl = documentObj.getElementById("permissionFeedback");
        const cameraStatusEl = documentObj.getElementById("cameraPermissionStatus");
        const microphoneStatusEl = documentObj.getElementById("microphonePermissionStatus");
        const fullscreenStatusEl = documentObj.getElementById("fullscreenPermissionStatus");

        if (!form || !submitBtn || !windowObj.bootstrap) {
            return;
        }

        const requireFullscreen = form.getAttribute("data-require-fullscreen") === "true";
        const requireCamera = form.getAttribute("data-require-camera") === "true";
        const requireMicrophone = form.getAttribute("data-require-microphone") === "true";
        const requirePreflight = form.getAttribute("data-require-preflight") === "true";
        const requiresMedia = requireCamera || requireMicrophone;
        const modal = modalEl ? new windowObj.bootstrap.Modal(modalEl) : null;
        let mediaGranted = !requiresMedia;
        let fullscreenGranted = !requireFullscreen;
        let mediaStream = null;

        if (requirePreflight && (!modalEl || !openBtn)) {
            return;
        }

        function showFeedback(message, tone) {
            if (!feedbackEl) {
                return;
            }
            feedbackEl.className = `alert alert-${tone || "warning"} py-2 small`;
            feedbackEl.textContent = message;
            feedbackEl.classList.remove("d-none");
        }

        function hideFeedback() {
            if (!feedbackEl) {
                return;
            }
            feedbackEl.textContent = "";
            feedbackEl.classList.add("d-none");
        }

        function syncSubmitState() {
            submitBtn.disabled = !(mediaGranted && fullscreenGranted);
        }

        function syncFullscreenStatus() {
            if (!requireFullscreen) {
                fullscreenGranted = true;
                syncSubmitState();
                return;
            }
            fullscreenGranted = Boolean(documentObj.fullscreenElement);
            setBadgeState(
                fullscreenStatusEl,
                fullscreenGranted ? "success" : "warning",
                fullscreenGranted ? "Aktif" : "Belum aktif"
            );
            syncSubmitState();
        }

        async function requestMediaPermissions() {
            if (!requiresMedia) {
                mediaGranted = true;
                syncSubmitState();
                return;
            }
            if (!windowObj.navigator || !windowObj.navigator.mediaDevices || typeof windowObj.navigator.mediaDevices.getUserMedia !== "function") {
                mediaGranted = false;
                if (requireCamera) {
                    setBadgeState(cameraStatusEl, "danger", "Tidak didukung");
                }
                if (requireMicrophone) {
                    setBadgeState(microphoneStatusEl, "danger", "Tidak didukung");
                }
                showFeedback("Browser tidak mendukung akses perangkat yang diwajibkan ujian.", "danger");
                syncSubmitState();
                return;
            }

            hideFeedback();
            if (requireCamera) {
                setBadgeState(cameraStatusEl, "warning", "Meminta izin...");
            }
            if (requireMicrophone) {
                setBadgeState(microphoneStatusEl, "warning", "Meminta izin...");
            }

            try {
                stopStream(mediaStream);
                mediaStream = await windowObj.navigator.mediaDevices.getUserMedia({
                    video: requireCamera ? {
                        facingMode: "user",
                        width: { ideal: 640 },
                        height: { ideal: 360 },
                    } : false,
                    audio: requireMicrophone,
                });
                mediaGranted = true;
                if (requireCamera) {
                    setBadgeState(cameraStatusEl, "success", "Diizinkan");
                }
                if (requireMicrophone) {
                    setBadgeState(microphoneStatusEl, "success", "Diizinkan");
                }
                hideFeedback();
            } catch (error) {
                mediaGranted = false;
                if (requireCamera) {
                    setBadgeState(cameraStatusEl, "danger", "Ditolak");
                }
                if (requireMicrophone) {
                    setBadgeState(microphoneStatusEl, "danger", "Ditolak");
                }
                if (requireCamera && requireMicrophone) {
                    showFeedback("Kamera dan mikrofon wajib diizinkan sebelum ujian dapat dimulai.", "warning");
                } else if (requireCamera) {
                    showFeedback("Kamera wajib diizinkan sebelum ujian dapat dimulai.", "warning");
                } else {
                    showFeedback("Mikrofon wajib diizinkan sebelum ujian dapat dimulai.", "warning");
                }
            }
            syncSubmitState();
        }

        async function enableFullscreen() {
            if (!requireFullscreen) {
                fullscreenGranted = true;
                syncSubmitState();
                return;
            }

            try {
                await requestFullscreen(documentObj.documentElement);
                hideFeedback();
            } catch (error) {
                showFeedback("Fullscreen wajib aktif. Klik tombol fullscreen lagi jika browser belum menyalakan fullscreen.", "warning");
            }
            syncFullscreenStatus();
        }

        if (openBtn && modal) {
            openBtn.addEventListener("click", () => {
                modal.show();
                syncFullscreenStatus();
            });
        }

        if (checkMediaBtn) {
            checkMediaBtn.addEventListener("click", () => {
                requestMediaPermissions();
            });
        }

        if (fullscreenBtn) {
            fullscreenBtn.addEventListener("click", () => {
                enableFullscreen();
            });
        }

        submitBtn.addEventListener("click", () => {
            stopStream(mediaStream);
            mediaStream = null;
            form.setAttribute("data-submitting", "true");
            if (typeof form.requestSubmit === "function") {
                form.requestSubmit();
                return;
            }
            form.submit();
        });

        if (modalEl) {
            modalEl.addEventListener("hidden.bs.modal", () => {
                if (!form.matches("[data-submitting='true']")) {
                    stopStream(mediaStream);
                    mediaStream = null;
                    mediaGranted = !requiresMedia;
                    if (requireCamera) {
                        setBadgeState(cameraStatusEl, "pending", "Belum dicek");
                    }
                    if (requireMicrophone) {
                        setBadgeState(microphoneStatusEl, "pending", "Belum dicek");
                    }
                    if (requireFullscreen) {
                        syncFullscreenStatus();
                    }
                    hideFeedback();
                    syncSubmitState();
                }
            });
        }

        form.addEventListener("submit", () => {
            form.setAttribute("data-submitting", "true");
            stopStream(mediaStream);
            mediaStream = null;
        });

        documentObj.addEventListener("fullscreenchange", syncFullscreenStatus);
        syncFullscreenStatus();
        syncSubmitState();
    }

    if (documentObj.readyState === "loading") {
        documentObj.addEventListener("DOMContentLoaded", bootstrapExamStart);
    } else {
        bootstrapExamStart();
    }
})(window, document);
