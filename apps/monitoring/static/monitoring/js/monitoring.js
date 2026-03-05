(function () {
    function parseJSONScript(id, fallback) {
        var node = document.getElementById(id);
        if (!node) {
            return fallback;
        }
        try {
            return JSON.parse(node.textContent || "");
        } catch (err) {
            return fallback;
        }
    }

    function getCookie(name) {
        var cookieValue = null;
        if (!document.cookie) {
            return cookieValue;
        }
        document.cookie.split(";").forEach(function (cookie) {
            var item = cookie.trim();
            if (item.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(item.substring(name.length + 1));
            }
        });
        return cookieValue;
    }

    function asNumber(value, fallback) {
        var parsed = parseInt(value, 10);
        return Number.isNaN(parsed) ? fallback : parsed;
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function badgeClassByIndicator(indicator) {
        if (indicator === "success") {
            return "text-bg-success";
        }
        if (indicator === "warning") {
            return "text-bg-warning";
        }
        if (indicator === "danger") {
            return "text-bg-danger";
        }
        if (indicator === "primary") {
            return "text-bg-primary";
        }
        return "text-bg-secondary";
    }

    document.addEventListener("DOMContentLoaded", function () {
        var config = parseJSONScript("monitoring-config-data", {});
        var initialSnapshot = parseJSONScript("monitoring-snapshot-data", {});
        if (!config.examId) {
            return;
        }

        if (window.axios) {
            window.axios.defaults.headers.common["X-CSRFToken"] = getCookie("csrftoken");
            window.axios.defaults.headers.common["X-Requested-With"] = "XMLHttpRequest";
        }

        var alertEl = document.getElementById("monitoringAlert");
        var totalParticipantsValue = document.getElementById("totalParticipantsValue");
        var currentlyActiveValue = document.getElementById("currentlyActiveValue");
        var completedValue = document.getElementById("completedValue");
        var averageProgressValue = document.getElementById("averageProgressValue");
        var studentsGridEl = document.getElementById("studentsMonitoringGrid");
        var violationTypeFilter = document.getElementById("violationTypeFilter");
        var violationsFeedEl = document.getElementById("violationsFeed");
        var announcementTargetType = document.getElementById("announcementTargetType");
        var announcementStudentId = document.getElementById("announcementStudentId");
        var announcementTitle = document.getElementById("announcementTitle");
        var announcementMessage = document.getElementById("announcementMessage");
        var announcementResult = document.getElementById("announcementResult");
        var announcementForm = document.getElementById("announcementForm");
        var sendAnnouncementBtn = document.getElementById("sendAnnouncementBtn");
        var refreshIntervalSelect = document.getElementById("refreshIntervalSelect");
        var manualRefreshBtn = document.getElementById("manualRefreshBtn");
        var monitorLastUpdateAt = document.getElementById("monitorLastUpdateAt");

        var studentDetailModalEl = document.getElementById("studentDetailModal");
        var studentDetailModal = studentDetailModalEl && window.bootstrap
            ? new window.bootstrap.Modal(studentDetailModalEl)
            : null;
        var detailStudentName = document.getElementById("detailStudentName");
        var detailStudentMeta = document.getElementById("detailStudentMeta");
        var detailAttemptStatus = document.getElementById("detailAttemptStatus");
        var detailProgress = document.getElementById("detailProgress");
        var detailTimeRemaining = document.getElementById("detailTimeRemaining");
        var detailViolationsCount = document.getElementById("detailViolationsCount");
        var detailExtendMinutes = document.getElementById("detailExtendMinutes");
        var detailExtendBtn = document.getElementById("detailExtendBtn");
        var detailForceSubmitBtn = document.getElementById("detailForceSubmitBtn");
        var detailActionResult = document.getElementById("detailActionResult");
        var detailAnswersTableBody = document.getElementById("detailAnswersTableBody");
        var detailAttemptHistoryTableBody = document.getElementById("detailAttemptHistoryTableBody");
        var detailScreenshotsGrid = document.getElementById("detailScreenshotsGrid");
        var detailViolationsList = document.getElementById("detailViolationsList");

        var currentViolationType = "";
        var refreshTimer = null;
        var detailState = {
            studentId: "",
            attemptId: "",
            canIntervene: false
        };

        function setAlert(type, message) {
            if (!alertEl) {
                return;
            }
            if (!message) {
                alertEl.classList.add("d-none");
                alertEl.innerHTML = "";
                return;
            }
            alertEl.classList.remove("d-none");
            alertEl.innerHTML = '<div class="alert alert-' + type + ' py-2 mb-0">' + escapeHtml(message) + "</div>";
        }

        function setDetailActionResult(type, message) {
            if (!detailActionResult) {
                return;
            }
            if (!message) {
                detailActionResult.className = "small text-muted mt-2 mb-0";
                detailActionResult.textContent = "";
                return;
            }
            detailActionResult.className = "small mt-2 mb-0 text-" + (type === "danger" ? "danger" : "success");
            detailActionResult.textContent = message;
        }

        function updateLastRefreshLabel(snapshot) {
            if (!monitorLastUpdateAt) {
                return;
            }
            var label = snapshot && snapshot.generated_at_label ? snapshot.generated_at_label : "-";
            monitorLastUpdateAt.textContent = "Update terakhir: " + label;
        }

        function renderStats(snapshot) {
            var stats = snapshot && snapshot.stats ? snapshot.stats : {};
            totalParticipantsValue.textContent = String(stats.total_participants || 0);
            currentlyActiveValue.textContent = String(stats.currently_active || 0);
            completedValue.textContent = String(stats.completed || 0);
            averageProgressValue.textContent = String(stats.average_progress_percent || 0) + "%";
        }

        function renderStudents(snapshot) {
            var students = snapshot && Array.isArray(snapshot.students) ? snapshot.students : [];
            if (!students.length) {
                studentsGridEl.innerHTML = (
                    '<div class="col-12">' +
                        '<div class="border rounded p-3 text-muted">Belum ada peserta yang dapat dimonitor pada ujian ini.</div>' +
                    "</div>"
                );
                return;
            }

            studentsGridEl.innerHTML = students.map(function (student) {
                var photoHtml = "";
                if (student.photo_url) {
                    photoHtml = '<img src="' + escapeHtml(student.photo_url) + '" alt="Foto siswa" class="monitor-student-avatar">';
                } else {
                    var initial = escapeHtml((student.student_name || "S").charAt(0).toUpperCase());
                    photoHtml = '<div class="monitor-student-avatar fallback">' + initial + "</div>";
                }

                var progressWidth = Math.max(0, Math.min(100, Number(student.progress_percent || 0)));
                return (
                    '<div class="col-md-6">' +
                        '<article class="monitor-student-card indicator-' + escapeHtml(student.indicator) + ' p-3 h-100">' +
                            '<div class="d-flex align-items-start justify-content-between gap-2 mb-2">' +
                                '<div class="d-flex align-items-center gap-2">' +
                                    photoHtml +
                                    '<div>' +
                                        '<p class="fw-semibold mb-0">' + escapeHtml(student.student_name) + "</p>" +
                                        '<p class="small text-muted mb-0">@' + escapeHtml(student.username) + "</p>" +
                                    "</div>" +
                                "</div>" +
                                '<span class="badge ' + badgeClassByIndicator(student.indicator) + '">' + escapeHtml(student.status_label) + "</span>" +
                            "</div>" +
                            '<div class="small text-muted mb-2">Indikator: ' + escapeHtml(student.indicator_label || "-") + "</div>" +
                            '<div class="small mb-1 d-flex justify-content-between"><span>Progress</span><span>' + escapeHtml(String(student.progress_percent)) + "%</span></div>" +
                            '<div class="progress mb-2" role="progressbar" aria-label="Progress siswa">' +
                                '<div class="progress-bar ' + (student.indicator === "danger" ? "bg-danger" : (student.indicator === "warning" ? "bg-warning" : "bg-success")) + '" style="width:' + progressWidth + '%;"></div>' +
                            "</div>" +
                            '<ul class="list-unstyled small mb-3">' +
                                "<li>Soal saat ini: <strong>" + escapeHtml(String(student.current_question || 0)) + "</strong></li>" +
                                "<li>Sisa waktu: <strong>" + escapeHtml(student.time_remaining_label || "-") + "</strong></li>" +
                                "<li>Jawaban: <strong>" + escapeHtml(String(student.answered_count || 0)) + " / " + escapeHtml(String(student.total_questions || 0)) + "</strong></li>" +
                                "<li>Pelanggaran: <strong>" + escapeHtml(String(student.violations_count || 0)) + "</strong></li>" +
                                "<li>Last seen: <strong>" + escapeHtml(student.last_seen_label || "-") + "</strong></li>" +
                                (student.show_attempt_badge
                                    ? ("<li>Attempt: <strong>" + escapeHtml(String(student.attempt_number || 0)) + "/" + escapeHtml(String(student.max_attempts || 1)) + "</strong></li>")
                                    : "") +
                            "</ul>" +
                            '<div class="d-grid">' +
                                '<button type="button" class="btn btn-sm btn-outline-primary open-student-detail-btn" data-student-id="' + escapeHtml(student.student_id) + '" title="Lihat detail siswa dan intervensi">' +
                                    '<i class="ri-eye-line me-1"></i>Detail' +
                                "</button>" +
                            "</div>" +
                        "</article>" +
                    "</div>"
                );
            }).join("");
        }

        function renderViolations(snapshot) {
            var violations = snapshot && Array.isArray(snapshot.violations) ? snapshot.violations : [];
            if (!violations.length) {
                violationsFeedEl.innerHTML = '<li class="list-group-item px-0 text-muted small">Belum ada pelanggaran.</li>';
                return;
            }

            violationsFeedEl.innerHTML = violations.map(function (item) {
                return (
                    '<li class="list-group-item px-0 py-1 border-0">' +
                        '<div class="violation-feed-item">' +
                            '<div class="d-flex justify-content-between align-items-center mb-1">' +
                                '<strong class="small">' + escapeHtml(item.student_name) + "</strong>" +
                                '<span class="badge text-bg-' + escapeHtml(item.severity_badge || "secondary") + '">' + escapeHtml(item.severity_label || "-") + "</span>" +
                            "</div>" +
                            '<p class="small mb-1">' + escapeHtml(item.violation_label || "-") + "</p>" +
                            '<p class="small text-muted mb-0">' + escapeHtml(item.detected_at_label || "-") + "</p>" +
                        "</div>" +
                    "</li>"
                );
            }).join("");
        }

        function renderAnnouncementTargets(snapshot) {
            var targets = snapshot && Array.isArray(snapshot.announcement_targets) ? snapshot.announcement_targets : [];
            announcementStudentId.innerHTML = '<option value="">Pilih siswa...</option>' + targets.map(function (target) {
                return '<option value="' + escapeHtml(target.id) + '">' + escapeHtml(target.name) + " (" + escapeHtml(target.username) + ")</option>";
            }).join("");
        }

        function renderSnapshot(snapshot) {
            renderStats(snapshot);
            renderStudents(snapshot);
            renderViolations(snapshot);
            renderAnnouncementTargets(snapshot);
            updateLastRefreshLabel(snapshot);
        }

        function buildSnapshotUrl() {
            if (!currentViolationType) {
                return config.snapshotUrl;
            }
            return config.snapshotUrl + "?violation_type=" + encodeURIComponent(currentViolationType);
        }

        async function fetchSnapshot(showError) {
            try {
                var response = await window.axios.get(buildSnapshotUrl());
                renderSnapshot(response.data || {});
                if (showError) {
                    setAlert("", "");
                }
            } catch (err) {
                if (showError) {
                    setAlert("danger", "Gagal memuat data monitoring terbaru.");
                }
            }
        }

        function scheduleAutoRefresh() {
            if (refreshTimer) {
                window.clearInterval(refreshTimer);
            }
            var intervalSeconds = asNumber(refreshIntervalSelect.value, 30);
            if (intervalSeconds <= 0) {
                refreshTimer = null;
                return;
            }
            refreshTimer = window.setInterval(function () {
                fetchSnapshot(false);
            }, intervalSeconds * 1000);
        }

        function studentDetailUrl(studentId) {
            return String(config.studentDetailUrlTemplate || "").replace("__student_id__", studentId);
        }

        function forceSubmitUrl(attemptId) {
            return String(config.forceSubmitUrlTemplate || "").replace("__attempt_id__", attemptId);
        }

        function resetDetailModal() {
            detailState.studentId = "";
            detailState.attemptId = "";
            detailState.canIntervene = false;
            detailStudentName.textContent = "Detail Siswa";
            detailStudentMeta.textContent = "-";
            detailAttemptStatus.textContent = "-";
            detailProgress.textContent = "-";
            detailTimeRemaining.textContent = "-";
            detailViolationsCount.textContent = "-";
            detailAnswersTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Belum ada data jawaban.</td></tr>';
            if (detailAttemptHistoryTableBody) {
                detailAttemptHistoryTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Belum ada riwayat attempt.</td></tr>';
            }
            detailScreenshotsGrid.innerHTML = '<div class="col-12"><p class="text-muted mb-0">Belum ada screenshot untuk attempt ini.</p></div>';
            detailViolationsList.innerHTML = '<p class="text-muted mb-0">Belum ada log pelanggaran.</p>';
            setDetailActionResult("", "");
        }

        function renderDetailAnswers(answers) {
            if (!answers || !answers.length) {
                detailAnswersTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Belum ada data jawaban.</td></tr>';
                return;
            }
            detailAnswersTableBody.innerHTML = answers.map(function (answer) {
                var markedLabel = answer.is_marked_for_review ? " (Ditandai review)" : "";
                var truncatedId = answer.id.length > 8 ? answer.id.substring(0, 8) + "..." : answer.id;
                return (
                    "<tr>" +
                        '<td class="ps-3"><small class="text-muted" title="' + escapeHtml(answer.id) + '">' + escapeHtml(truncatedId) + "</small></td>" +
                        "<td>" + escapeHtml(answer.question_text || "-") + "</td>" +
                        "<td>" + escapeHtml(answer.answer_value || "-") + markedLabel + "</td>" +
                        "<td>" + escapeHtml(answer.time_spent_label || "-") + "</td>" +
                        "<td>" + escapeHtml(String(answer.points_earned || 0)) + " / " + escapeHtml(String(answer.points_possible || 0)) + "</td>" +
                        '<td class="pe-3">' + escapeHtml(answer.updated_at_label || "-") + "</td>" +
                    "</tr>"
                );
            }).join("");
        }

        function renderDetailScreenshots(items) {
            if (!items || !items.length) {
                detailScreenshotsGrid.innerHTML = '<div class="col-12"><p class="text-muted mb-0">Belum ada screenshot untuk attempt ini.</p></div>';
                return;
            }
            detailScreenshotsGrid.innerHTML = items.map(function (item) {
                var flaggedBadge = item.is_flagged
                    ? '<span class="badge text-bg-danger">Flagged</span>'
                    : '<span class="badge text-bg-secondary">Normal</span>';
                var reason = item.flag_reason ? '<p class="small text-danger mb-0">Alasan: ' + escapeHtml(item.flag_reason) + "</p>" : "";
                return (
                    '<div class="col-md-4">' +
                        '<div class="screenshot-card">' +
                            '<img src="' + escapeHtml(item.url) + '" alt="Screenshot proctoring">' +
                            '<div class="meta">' +
                                '<p class="small text-muted mb-1">' + escapeHtml(item.capture_time_label || "-") + "</p>" +
                                flaggedBadge +
                                reason +
                            "</div>" +
                        "</div>" +
                    "</div>"
                );
            }).join("");
        }

        function renderDetailViolations(items) {
            if (!items || !items.length) {
                detailViolationsList.innerHTML = '<p class="text-muted mb-0">Belum ada log pelanggaran.</p>';
                return;
            }
            detailViolationsList.innerHTML = items.map(function (item) {
                return (
                    '<article class="detail-violation-item">' +
                        '<div class="d-flex align-items-center justify-content-between mb-1">' +
                            "<strong>" + escapeHtml(item.violation_label || "-") + "</strong>" +
                            '<span class="badge text-bg-' + escapeHtml(item.severity_badge || "secondary") + '">' + escapeHtml(item.severity_label || "-") + "</span>" +
                        "</div>" +
                        '<p class="small text-muted mb-1">' + escapeHtml(item.detected_at_label || "-") + "</p>" +
                        '<p class="small mb-0">' + escapeHtml(item.description || "-") + "</p>" +
                    "</article>"
                );
            }).join("");
        }

        function renderDetailAttemptHistory(items) {
            if (!detailAttemptHistoryTableBody) {
                return;
            }
            if (!items || !items.length) {
                detailAttemptHistoryTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Belum ada riwayat attempt.</td></tr>';
                return;
            }
            detailAttemptHistoryTableBody.innerHTML = items.map(function (item) {
                return (
                    "<tr>" +
                        '<td class="ps-3">' + escapeHtml(String(item.attempt_number || 0)) + "</td>" +
                        "<td>" + escapeHtml(item.start_time_label || "-") + "</td>" +
                        "<td>" + escapeHtml(item.submit_time_label || "-") + "</td>" +
                        "<td>" + escapeHtml(String(item.total_score || 0)) + "</td>" +
                        '<td class="pe-3">' + escapeHtml(item.status_label || "-") + "</td>" +
                    "</tr>"
                );
            }).join("");
        }

        function renderDetail(payload) {
            var student = payload.student || {};
            var attempt = payload.attempt || null;
            var summary = payload.summary || {};
            detailStudentName.textContent = student.name || "Detail Siswa";
            detailStudentMeta.textContent = student.username ? ("@" + student.username) : "-";
            detailAttemptStatus.textContent = attempt ? (attempt.status_label || "-") : "Belum ada attempt";
            detailProgress.textContent = String(summary.progress_percent || 0) + "% (" + String(summary.answered_count || 0) + "/" + String(summary.total_questions || 0) + ")";
            detailTimeRemaining.textContent = summary.time_remaining_label || "-";
            detailViolationsCount.textContent = String(summary.violations_count || 0);
            renderDetailAnswers(payload.answers || []);
            renderDetailAttemptHistory(payload.attempt_history || []);
            renderDetailScreenshots(payload.screenshots || []);
            renderDetailViolations(payload.violations || []);

            detailState.studentId = student.id || "";
            detailState.attemptId = attempt && attempt.id ? attempt.id : "";
            detailState.canIntervene = !!(attempt && attempt.can_intervene);
            detailExtendBtn.disabled = !detailState.studentId || !detailState.canIntervene;
            detailForceSubmitBtn.disabled = !detailState.attemptId || !detailState.canIntervene;
        }

        async function openStudentDetail(studentId) {
            try {
                resetDetailModal();
                var response = await window.axios.get(studentDetailUrl(studentId));
                renderDetail(response.data || {});
                if (studentDetailModal) {
                    studentDetailModal.show();
                }
            } catch (err) {
                setAlert("danger", "Gagal memuat detail siswa.");
            }
        }

        async function handleExtendTime() {
            if (!detailState.studentId) {
                return;
            }
            var minutes = asNumber(detailExtendMinutes.value, 0);
            if (minutes <= 0) {
                setDetailActionResult("danger", "Masukkan jumlah menit yang valid.");
                return;
            }
            try {
                detailExtendBtn.disabled = true;
                var response = await window.axios.post(config.extendTimeUrl, {
                    student_id: detailState.studentId,
                    minutes: minutes
                });
                if (response.data && response.data.success) {
                    setDetailActionResult("success", response.data.message || "Waktu berhasil ditambah.");
                    await fetchSnapshot(false);
                    detailTimeRemaining.textContent = response.data.data.time_remaining_label || detailTimeRemaining.textContent;
                } else {
                    setDetailActionResult("danger", "Gagal menambah waktu.");
                }
            } catch (err) {
                var message = (err.response && err.response.data && err.response.data.message)
                    ? err.response.data.message
                    : "Gagal menambah waktu.";
                setDetailActionResult("danger", message);
            } finally {
                detailExtendBtn.disabled = !detailState.studentId || !detailState.canIntervene;
            }
        }

        async function handleForceSubmit() {
            if (!detailState.attemptId) {
                return;
            }
            var confirmed = window.confirm("Paksa submit attempt siswa ini sekarang?");
            if (!confirmed) {
                return;
            }
            try {
                detailForceSubmitBtn.disabled = true;
                var response = await window.axios.post(forceSubmitUrl(detailState.attemptId), {});
                if (response.data && response.data.success) {
                    setDetailActionResult("success", response.data.message || "Attempt berhasil dipaksa submit.");
                    await fetchSnapshot(false);
                    detailState.canIntervene = false;
                    detailForceSubmitBtn.disabled = true;
                    detailExtendBtn.disabled = true;
                    detailAttemptStatus.textContent = "Sudah Submit";
                    detailTimeRemaining.textContent = "00:00";
                } else {
                    setDetailActionResult("danger", "Gagal memaksa submit attempt.");
                }
            } catch (err) {
                var message = (err.response && err.response.data && err.response.data.message)
                    ? err.response.data.message
                    : "Gagal memaksa submit attempt.";
                setDetailActionResult("danger", message);
            } finally {
                detailForceSubmitBtn.disabled = !detailState.attemptId || !detailState.canIntervene;
            }
        }

        function toggleAnnouncementTarget() {
            var target = announcementTargetType.value;
            announcementStudentId.disabled = target !== "student";
        }

        async function handleAnnouncementSubmit(event) {
            event.preventDefault();
            var target = announcementTargetType.value;
            var message = (announcementMessage.value || "").trim();
            if (!message) {
                announcementResult.className = "small text-danger mt-2 mb-0";
                announcementResult.textContent = "Isi pesan pengumuman wajib diisi.";
                return;
            }
            var payload = {
                target: target,
                title: announcementTitle.value || "",
                message: message
            };
            if (target === "student") {
                if (!announcementStudentId.value) {
                    announcementResult.className = "small text-danger mt-2 mb-0";
                    announcementResult.textContent = "Pilih siswa tujuan pengumuman.";
                    return;
                }
                payload.student_id = announcementStudentId.value;
            }

            try {
                sendAnnouncementBtn.disabled = true;
                var response = await window.axios.post(config.announcementUrl, payload);
                if (response.data && response.data.success) {
                    announcementResult.className = "small text-success mt-2 mb-0";
                    announcementResult.textContent = response.data.message || "Pengumuman berhasil dikirim.";
                    announcementMessage.value = "";
                    announcementTitle.value = "";
                } else {
                    announcementResult.className = "small text-danger mt-2 mb-0";
                    announcementResult.textContent = "Gagal mengirim pengumuman.";
                }
            } catch (err) {
                var messageText = (err.response && err.response.data && err.response.data.message)
                    ? err.response.data.message
                    : "Gagal mengirim pengumuman.";
                announcementResult.className = "small text-danger mt-2 mb-0";
                announcementResult.textContent = messageText;
            } finally {
                sendAnnouncementBtn.disabled = false;
            }
        }

        manualRefreshBtn.addEventListener("click", function () {
            fetchSnapshot(true);
        });

        refreshIntervalSelect.addEventListener("change", function () {
            scheduleAutoRefresh();
        });

        violationTypeFilter.addEventListener("change", function () {
            currentViolationType = violationTypeFilter.value || "";
            fetchSnapshot(false);
        });

        studentsGridEl.addEventListener("click", function (event) {
            var button = event.target.closest(".open-student-detail-btn");
            if (!button) {
                return;
            }
            var studentId = button.getAttribute("data-student-id");
            if (!studentId) {
                return;
            }
            openStudentDetail(studentId);
        });

        detailExtendBtn.addEventListener("click", function () {
            handleExtendTime();
        });

        detailForceSubmitBtn.addEventListener("click", function () {
            handleForceSubmit();
        });

        announcementTargetType.addEventListener("change", toggleAnnouncementTarget);
        announcementForm.addEventListener("submit", handleAnnouncementSubmit);

        if (initialSnapshot && initialSnapshot.exam) {
            renderSnapshot(initialSnapshot);
        } else {
            fetchSnapshot(false);
        }

        toggleAnnouncementTarget();
        scheduleAutoRefresh();
    });
})();
