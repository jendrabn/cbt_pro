(function examRoomBootstrap(windowObj, documentObj) {
    function getCookie(name) {
        if (!documentObj.cookie) {
            return "";
        }
        const cookies = documentObj.cookie.split(";");
        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(`${name}=`)) {
                return decodeURIComponent(cookie.slice(name.length + 1));
            }
        }
        return "";
    }

    function setupAxiosCsrf() {
        if (!windowObj.axios) {
            return;
        }
        const token = getCookie("csrftoken");
        if (token) {
            windowObj.axios.defaults.headers.common["X-CSRFToken"] = token;
        }
        windowObj.axios.defaults.headers.common["X-Requested-With"] = "XMLHttpRequest";
    }

    class ExamRoomApp {
        constructor(config) {
            this.config = config || {};
            this.payload = this.config.initialPayload || null;
            this.timer = null;
            this.isSubmitting = false;
            this.proctoringIntervalId = null;
            this.proctoringStream = null;
            this.proctoringVideo = null;
            this.proctoringWarningShown = false;
            this.guard = null;
            this.saveIndicator = (windowObj.ExamRoomAutoSave && windowObj.ExamRoomAutoSave.buildSaveIndicator())
                || {
                    syncing() {},
                    success() {},
                    error() {},
                };
            this.elements = {};
            this.submitModal = null;
            this.violationModal = null;
            this.isReportingViolation = false;
        }

        init() {
            this.cacheElements();
            this.setupModals();
            this.bindEvents();
            this.renderPayload(this.payload);
            this.setupAntiCheat();
            this.setupProctoring();
            windowObj.addEventListener("beforeunload", () => this.destroy());
        }

        destroy() {
            if (this.timer && typeof this.timer.stop === "function") {
                this.timer.stop();
            }
            if (this.proctoringIntervalId) {
                windowObj.clearInterval(this.proctoringIntervalId);
                this.proctoringIntervalId = null;
            }
            if (this.proctoringStream && typeof this.proctoringStream.getTracks === "function") {
                this.proctoringStream.getTracks().forEach((track) => {
                    if (track && typeof track.stop === "function") {
                        track.stop();
                    }
                });
            }
            this.proctoringStream = null;
            if (this.proctoringVideo) {
                this.proctoringVideo.srcObject = null;
                this.proctoringVideo = null;
            }
            if (this.guard && typeof this.guard.destroy === "function") {
                this.guard.destroy();
            }
        }

        cacheElements() {
            const byId = (id) => documentObj.getElementById(id);
            this.elements = {
                alertHost: byId("examRoomAlertHost"),
                restrictionAlert: byId("navigationRestriction"),
                timerDisplay: byId("timerDisplay"),
                timerChip: documentObj.querySelector(".timer-chip"),
                violationCounterChip: byId("violationCounterChip"),
                attemptCounterBadge: byId("attemptCounterBadge"),
                questionIndexLabel: byId("questionIndexLabel"),
                totalQuestionLabel: byId("totalQuestionLabel"),
                autoSaveLabel: byId("autoSaveLabel"),
                questionText: byId("questionText"),
                questionImageWrap: byId("questionImageWrap"),
                questionImage: byId("questionImage"),
                questionAnswerContainer: byId("questionAnswerContainer"),
                markReviewCheckbox: byId("markReviewCheckbox"),
                prevQuestionBtn: byId("prevQuestionBtn"),
                nextQuestionBtn: byId("nextQuestionBtn"),
                clearAnswerBtn: byId("clearAnswerBtn"),
                questionGrid: byId("questionGrid"),
                progressLabel: byId("progressLabel"),
                progressBar: byId("progressBar"),
                summaryAnswered: byId("summaryAnswered"),
                summaryUnanswered: byId("summaryUnanswered"),
                summaryMarked: byId("summaryMarked"),
                antiCheatFullscreenRule: byId("antiCheatFullscreenRule"),
                antiCheatTabRule: byId("antiCheatTabRule"),
                antiCheatScreenshotRule: byId("antiCheatScreenshotRule"),
                antiCheatLimitRule: byId("antiCheatLimitRule"),
                fullscreenOverlay: byId("fullscreenOverlay"),
                returnFullscreenBtn: byId("returnFullscreenBtn"),
                openSubmitModalBtn: byId("openSubmitModalBtn"),
                confirmSubmitBtn: byId("confirmSubmitBtn"),
                submitTotalCount: byId("submitTotalCount"),
                submitAnsweredCount: byId("submitAnsweredCount"),
                submitUnansweredCount: byId("submitUnansweredCount"),
                submitMarkedCount: byId("submitMarkedCount"),
                submitRetakeInfo: byId("submitRetakeInfo"),
                violationMessage: byId("violationMessage"),
                violationCountLabel: byId("violationCountLabel"),
                closeViolationModalBtn: byId("closeViolationModalBtn"),
            };
        }

        setupModals() {
            if (windowObj.bootstrap) {
                const submitModalEl = documentObj.getElementById("submitModal");
                const violationModalEl = documentObj.getElementById("violationModal");
                if (submitModalEl) {
                    this.submitModal = new windowObj.bootstrap.Modal(submitModalEl);
                }
                if (violationModalEl) {
                    this.violationModal = new windowObj.bootstrap.Modal(violationModalEl);
                }
            }
        }

        bindEvents() {
            if (this.elements.prevQuestionBtn) {
                this.elements.prevQuestionBtn.addEventListener("click", () => this.goPrev());
            }
            if (this.elements.nextQuestionBtn) {
                this.elements.nextQuestionBtn.addEventListener("click", () => this.goNext());
            }
            if (this.elements.clearAnswerBtn) {
                this.elements.clearAnswerBtn.addEventListener("click", () => this.clearCurrentAnswer());
            }
            if (this.elements.markReviewCheckbox) {
                this.elements.markReviewCheckbox.addEventListener("change", (event) => {
                    this.saveCurrentAnswer({
                        question_number: this.getCurrentNumber(),
                        is_marked_for_review: Boolean(event.target.checked),
                    });
                });
            }
            if (this.elements.openSubmitModalBtn) {
                this.elements.openSubmitModalBtn.addEventListener("click", () => this.openSubmitModal());
            }
            if (this.elements.confirmSubmitBtn) {
                this.elements.confirmSubmitBtn.addEventListener("click", () => this.submitExam(false));
            }
            if (this.elements.returnFullscreenBtn) {
                this.elements.returnFullscreenBtn.addEventListener("click", () => this.requestFullscreenMode());
            }
            if (this.elements.closeViolationModalBtn) {
                this.elements.closeViolationModalBtn.addEventListener("click", () => {
                    if (this.payload && this.payload.anti_cheat && this.payload.anti_cheat.require_fullscreen) {
                        this.requestFullscreenMode();
                    }
                });
            }
        }

        getCurrentNumber() {
            if (!this.payload) {
                return 1;
            }
            return parseInt(this.payload.current_number || 1, 10);
        }

        getTotalQuestions() {
            if (!this.payload) {
                return 0;
            }
            return parseInt(this.payload.total_questions || 0, 10);
        }

        renderPayload(payload) {
            if (!payload) {
                this.showAlert("Data ruang ujian tidak tersedia.", "danger");
                return;
            }
            this.payload = payload;
            this.renderHeader();
            this.renderRestrictionMessage();
            this.renderQuestion();
            this.renderQuestionMap();
            this.renderSummary();
            this.renderAntiCheatRules();
            this.updateSubmitModalStats();
            this.initOrUpdateTimer();
        }

        renderHeader() {
            const current = this.getCurrentNumber();
            const total = this.getTotalQuestions();
            if (this.elements.questionIndexLabel) {
                this.elements.questionIndexLabel.textContent = String(current);
            }
            if (this.elements.totalQuestionLabel) {
                this.elements.totalQuestionLabel.textContent = String(total);
            }
            if (this.elements.autoSaveLabel) {
                this.elements.autoSaveLabel.textContent = this.payload.last_saved_label || "Belum tersimpan";
            }
            if (this.elements.attemptCounterBadge) {
                var allowRetake = !!this.payload.allow_retake;
                var maxAttempts = parseInt(this.payload.max_attempts || 1, 10);
                var attemptNumber = parseInt(this.payload.attempt_number || 1, 10);
                this.elements.attemptCounterBadge.classList.toggle("d-none", !(allowRetake && maxAttempts > 1));
                this.elements.attemptCounterBadge.textContent = "Attempt " + attemptNumber + " dari " + maxAttempts;
            }
            this.updateViolationChip();
        }

        renderRestrictionMessage() {
            if (!this.elements.restrictionAlert) {
                return;
            }
            const message = (this.payload.navigation && this.payload.navigation.restriction_message)
                || this.payload.notice
                || "";
            if (!message) {
                this.elements.restrictionAlert.classList.add("d-none");
                this.elements.restrictionAlert.textContent = "";
                return;
            }
            this.elements.restrictionAlert.textContent = message;
            this.elements.restrictionAlert.classList.remove("d-none");
        }

        renderQuestion() {
            const question = this.payload.question;
            if (!question) {
                if (this.elements.questionText) {
                    this.elements.questionText.textContent = "Soal tidak tersedia.";
                }
                if (this.elements.questionAnswerContainer) {
                    this.elements.questionAnswerContainer.innerHTML = "";
                }
                return;
            }

            if (this.elements.questionText) {
                this.elements.questionText.innerHTML = question.question_text || "";
            }

            if (this.elements.questionImageWrap && this.elements.questionImage) {
                if (question.question_image_url) {
                    this.elements.questionImage.src = question.question_image_url;
                    this.elements.questionImageWrap.classList.remove("d-none");
                } else {
                    this.elements.questionImage.src = "";
                    this.elements.questionImageWrap.classList.add("d-none");
                }
            }

            if (this.elements.markReviewCheckbox) {
                this.elements.markReviewCheckbox.checked = Boolean(question.answer && question.answer.marked_for_review);
            }

            this.renderAnswerControl(question);
            this.updateNavigationButtons();
        }

        renderAnswerControl(question) {
            if (!this.elements.questionAnswerContainer) {
                return;
            }
            this.elements.questionAnswerContainer.innerHTML = "";

            const currentNumber = this.getCurrentNumber();
            if (question.question_type === "multiple_choice") {
                const selectedOptionId = (question.answer && question.answer.selected_option_id) || "";
                (question.options || []).forEach((option) => {
                    const btn = documentObj.createElement("button");
                    btn.type = "button";
                    btn.className = "answer-option-item w-100 text-start";
                    if (selectedOptionId && selectedOptionId === option.id) {
                        btn.classList.add("selected");
                    }
                    btn.innerHTML = `
                        <span class="badge bg-primary me-2">${option.letter}</span>
                        <span>${option.text || ""}</span>
                    `;
                    btn.addEventListener("click", () => {
                        this.saveCurrentAnswer({
                            question_number: currentNumber,
                            selected_option_id: option.id,
                            is_marked_for_review: this.elements.markReviewCheckbox
                                ? Boolean(this.elements.markReviewCheckbox.checked)
                                : false,
                        });
                    });
                    this.elements.questionAnswerContainer.appendChild(btn);
                });
                return;
            }

            const textWrap = documentObj.createElement("div");
            textWrap.className = "mb-2";
            const inputId = question.question_type === "essay" ? "essayAnswerInput" : "shortAnswerInput";
            const placeholder = question.question_type === "essay"
                ? "Tulis jawaban esai Anda di sini..."
                : "Tulis jawaban singkat di sini...";
            const answerValue = (question.answer && question.answer.answer_text) || "";

            let inputEl = null;
            if (question.question_type === "essay") {
                inputEl = documentObj.createElement("textarea");
                inputEl.rows = 8;
                inputEl.className = "form-control";
            } else {
                inputEl = documentObj.createElement("input");
                inputEl.type = "text";
                inputEl.className = "form-control form-control-lg";
            }
            inputEl.id = inputId;
            inputEl.placeholder = placeholder;
            inputEl.value = answerValue;
            textWrap.appendChild(inputEl);

            const helper = documentObj.createElement("div");
            helper.className = "small text-muted mt-1";
            helper.id = "textAnswerCounter";
            helper.textContent = question.question_type === "essay"
                ? `Karakter: ${answerValue.length}`
                : `Panjang jawaban: ${answerValue.length} karakter`;
            textWrap.appendChild(helper);

            this.elements.questionAnswerContainer.appendChild(textWrap);

            const debouncedSave = (windowObj.ExamRoomAutoSave && windowObj.ExamRoomAutoSave.debounce)
                ? windowObj.ExamRoomAutoSave.debounce((value) => {
                    this.saveCurrentAnswer({
                        question_number: currentNumber,
                        answer_text: value,
                        is_marked_for_review: this.elements.markReviewCheckbox
                            ? Boolean(this.elements.markReviewCheckbox.checked)
                            : false,
                    });
                }, 700)
                : ((value) => {
                    this.saveCurrentAnswer({
                        question_number: currentNumber,
                        answer_text: value,
                        is_marked_for_review: this.elements.markReviewCheckbox
                            ? Boolean(this.elements.markReviewCheckbox.checked)
                            : false,
                    });
                });

            inputEl.addEventListener("input", (event) => {
                const value = event.target.value || "";
                helper.textContent = question.question_type === "essay"
                    ? `Karakter: ${value.length}`
                    : `Panjang jawaban: ${value.length} karakter`;
                debouncedSave(value);
            });
        }

        updateNavigationButtons() {
            if (!this.payload || !this.payload.navigation) {
                return;
            }
            const nav = this.payload.navigation;
            const current = this.getCurrentNumber();
            const total = this.getTotalQuestions();

            if (this.elements.prevQuestionBtn) {
                this.elements.prevQuestionBtn.disabled = !nav.can_previous || current <= 1;
            }
            if (this.elements.nextQuestionBtn) {
                if (nav.is_last || current >= total) {
                    this.elements.nextQuestionBtn.innerHTML = '<i class="ri-send-plane-fill me-1"></i>Kirim Ujian';
                } else {
                    this.elements.nextQuestionBtn.innerHTML = 'Berikutnya<i class="ri-arrow-right-line ms-1"></i>';
                }
                if (!nav.is_last && !nav.can_next) {
                    this.elements.nextQuestionBtn.disabled = true;
                } else {
                    this.elements.nextQuestionBtn.disabled = false;
                }
            }
        }

        renderQuestionMap() {
            if (!this.elements.questionGrid) {
                return;
            }
            this.elements.questionGrid.innerHTML = "";
            const mapRows = this.payload.question_map || [];
            mapRows.forEach((item) => {
                const btn = documentObj.createElement("button");
                btn.type = "button";
                btn.className = "btn btn-sm question-nav-btn";
                btn.textContent = item.number;
                btn.title = `Ke soal nomor ${item.number}`;

                if (item.locked) {
                    btn.classList.add("is-locked");
                    btn.disabled = true;
                    btn.title = `Soal ${item.number} terkunci`;
                } else if (item.current) {
                    btn.classList.add("is-current");
                } else if (item.answered) {
                    btn.classList.add("is-answered");
                } else if (item.marked) {
                    btn.classList.add("is-marked");
                } else {
                    btn.classList.add("is-empty");
                }

                btn.addEventListener("click", () => {
                    this.loadQuestion(item.number);
                });
                this.elements.questionGrid.appendChild(btn);
            });
        }

        renderSummary() {
            const summary = this.payload && this.payload.summary ? this.payload.summary : {};
            const total = parseInt(summary.total_questions || 0, 10);
            const answered = parseInt(summary.answered_count || 0, 10);
            const unanswered = parseInt(summary.unanswered_count || 0, 10);
            const marked = parseInt(summary.marked_count || 0, 10);
            const percentage = total > 0 ? Math.min(Math.round((answered / total) * 100), 100) : 0;

            if (this.elements.progressLabel) {
                this.elements.progressLabel.textContent = `${answered} / ${total}`;
            }
            if (this.elements.progressBar) {
                this.elements.progressBar.style.width = `${percentage}%`;
            }
            if (this.elements.summaryAnswered) {
                this.elements.summaryAnswered.textContent = String(answered);
            }
            if (this.elements.summaryUnanswered) {
                this.elements.summaryUnanswered.textContent = String(unanswered);
            }
            if (this.elements.summaryMarked) {
                this.elements.summaryMarked.textContent = String(marked);
            }
        }

        updateSubmitModalStats() {
            const summary = this.payload && this.payload.summary ? this.payload.summary : {};
            if (this.elements.submitTotalCount) {
                this.elements.submitTotalCount.textContent = String(summary.total_questions || 0);
            }
            if (this.elements.submitAnsweredCount) {
                this.elements.submitAnsweredCount.textContent = String(summary.answered_count || 0);
            }
            if (this.elements.submitUnansweredCount) {
                this.elements.submitUnansweredCount.textContent = String(summary.unanswered_count || 0);
            }
            if (this.elements.submitMarkedCount) {
                this.elements.submitMarkedCount.textContent = String(summary.marked_count || 0);
            }
            if (this.elements.submitRetakeInfo) {
                var allowRetake = !!this.payload.allow_retake;
                var maxAttempts = parseInt(this.payload.max_attempts || 1, 10);
                var attemptNumber = parseInt(this.payload.attempt_number || 1, 10);
                var remainingAttempts = Math.max(maxAttempts - attemptNumber, 0);
                if (allowRetake && remainingAttempts > 0) {
                    this.elements.submitRetakeInfo.classList.remove("d-none");
                    this.elements.submitRetakeInfo.textContent =
                        "Setelah submit, kamu masih punya " + remainingAttempts + " kesempatan ujian ulang.";
                } else {
                    this.elements.submitRetakeInfo.classList.add("d-none");
                    this.elements.submitRetakeInfo.textContent = "";
                }
            }
        }

        renderAntiCheatRules() {
            const antiCheat = this.payload && this.payload.anti_cheat ? this.payload.anti_cheat : {};
            if (this.elements.antiCheatFullscreenRule) {
                this.elements.antiCheatFullscreenRule.textContent = `Mode fullscreen: ${antiCheat.require_fullscreen ? "Wajib" : "Tidak wajib"}`;
            }
            if (this.elements.antiCheatTabRule) {
                this.elements.antiCheatTabRule.textContent = `Deteksi perpindahan tab: ${antiCheat.detect_tab_switch ? "Aktif" : "Tidak aktif"}`;
            }
            if (this.elements.antiCheatScreenshotRule) {
                this.elements.antiCheatScreenshotRule.textContent = antiCheat.enable_screenshot_proctoring
                    ? `Screenshot berkala: Aktif setiap ${antiCheat.screenshot_interval_seconds} detik`
                    : "Screenshot berkala: Tidak aktif";
            }
            if (this.elements.antiCheatLimitRule) {
                this.elements.antiCheatLimitRule.textContent = `Batas pelanggaran: ${antiCheat.max_violations_allowed}`;
            }
        }

        initOrUpdateTimer() {
            if (!windowObj.ExamRoomTimer || !this.payload || !this.payload.timer) {
                return;
            }

            const remainingSeconds = parseInt(this.payload.timer.remaining_seconds || 0, 10);
            if (!this.timer) {
                this.timer = windowObj.ExamRoomTimer.createTimer({
                    initialSeconds: remainingSeconds,
                    onTick: (seconds, label) => this.renderTimer(seconds, label),
                    onFinish: () => this.submitExam(true),
                });
                this.timer.start();
                return;
            }
            this.timer.setRemaining(remainingSeconds);
        }

        renderTimer(seconds, label) {
            if (this.elements.timerDisplay) {
                this.elements.timerDisplay.textContent = label;
            }
            if (!this.elements.timerChip) {
                return;
            }
            this.elements.timerChip.classList.remove("timer-warning", "timer-danger");
            if (seconds <= 300 && seconds > 60) {
                this.elements.timerChip.classList.add("timer-warning");
            }
            if (seconds <= 60) {
                this.elements.timerChip.classList.add("timer-danger");
            }
        }

        updateViolationChip() {
            if (!this.elements.violationCounterChip || !this.payload || !this.payload.anti_cheat) {
                return;
            }
            const count = parseInt(this.payload.anti_cheat.current_violations || 0, 10);
            this.elements.violationCounterChip.textContent = `Pelanggaran: ${count}`;
        }

        showAlert(message, type = "info", timeoutMs = 4200) {
            if (!this.elements.alertHost || !message) {
                return;
            }
            const alert = documentObj.createElement("div");
            alert.className = `alert alert-${type} py-2`;
            alert.textContent = message;
            this.elements.alertHost.appendChild(alert);

            if (timeoutMs > 0) {
                windowObj.setTimeout(() => {
                    if (alert.parentElement) {
                        alert.parentElement.removeChild(alert);
                    }
                }, timeoutMs);
            }
        }

        openSubmitModal() {
            this.updateSubmitModalStats();
            if (this.submitModal) {
                this.submitModal.show();
            }
        }

        async goPrev() {
            const current = this.getCurrentNumber();
            if (current <= 1) {
                return;
            }
            await this.loadQuestion(current - 1);
        }

        async goNext() {
            const current = this.getCurrentNumber();
            const total = this.getTotalQuestions();
            const nav = this.payload && this.payload.navigation ? this.payload.navigation : {};

            if (nav.is_last || current >= total) {
                this.openSubmitModal();
                return;
            }
            if (!nav.can_next) {
                this.showAlert(nav.restriction_message || "Navigasi ke soal berikutnya tidak diizinkan.", "warning");
                return;
            }
            await this.loadQuestion(current + 1);
        }

        async clearCurrentAnswer() {
            await this.saveCurrentAnswer({
                question_number: this.getCurrentNumber(),
                clear_answer: true,
                is_marked_for_review: this.elements.markReviewCheckbox
                    ? Boolean(this.elements.markReviewCheckbox.checked)
                    : false,
            });
        }

        async loadQuestion(number) {
            const current = this.getCurrentNumber();
            const url = (this.config.questionUrlTemplate || "").replace("__number__", String(number));
            if (!url) {
                return;
            }
            try {
                const response = await windowObj.axios.get(url, {
                    params: { current_number: current },
                });
                if (response.data && response.data.payload) {
                    this.renderPayload(response.data.payload);
                }
                if (response.data && response.data.message) {
                    this.showAlert(response.data.message, "warning");
                }
            } catch (error) {
                const redirectUrl = error && error.response && error.response.data
                    ? error.response.data.redirect_url
                    : "";
                if (redirectUrl) {
                    windowObj.location.href = redirectUrl;
                    return;
                }
                const message = error && error.response && error.response.data
                    ? error.response.data.message
                    : "Gagal memuat soal.";
                this.showAlert(message, "danger");
            }
        }

        async saveCurrentAnswer(payload) {
            if (!this.config.saveAnswerUrl) {
                return;
            }
            this.saveIndicator.syncing(this.elements.autoSaveLabel);
            try {
                const response = await windowObj.axios.post(this.config.saveAnswerUrl, payload);
                const data = response.data || {};
                if (data.payload) {
                    this.renderPayload(data.payload);
                }
                if (data.auto_submitted && data.redirect_url) {
                    windowObj.location.href = data.redirect_url;
                    return;
                }
                const hasSavedFlag = Object.prototype.hasOwnProperty.call(data, "saved");
                const isSaved = hasSavedFlag ? Boolean(data.saved) : true;
                if (isSaved) {
                    this.saveIndicator.success(this.elements.autoSaveLabel, "Tersimpan otomatis");
                    return;
                }
                this.saveIndicator.error(this.elements.autoSaveLabel, "Menunggu sinkronisasi");
                if (data.message) {
                    this.showAlert(data.message, "warning");
                }
            } catch (error) {
                const responseData = error && error.response ? error.response.data : null;
                if (responseData && responseData.redirect_url) {
                    windowObj.location.href = responseData.redirect_url;
                    return;
                }
                const message = responseData && responseData.message ? responseData.message : "Gagal menyimpan jawaban.";
                this.saveIndicator.error(this.elements.autoSaveLabel, "Gagal menyimpan");
                this.showAlert(message, "danger");
            }
        }

        async submitExam(fromTimer) {
            if (this.isSubmitting || !this.config.submitUrl) {
                return;
            }
            this.isSubmitting = true;
            try {
                const response = await windowObj.axios.post(this.config.submitUrl, {
                    auto: Boolean(fromTimer),
                });
                const redirectUrl = response.data && response.data.redirect_url
                    ? response.data.redirect_url
                    : this.config.submitRedirectUrl;
                if (redirectUrl) {
                    windowObj.location.href = redirectUrl;
                    return;
                }
                this.showAlert("Ujian berhasil dikirim.", "success");
            } catch (error) {
                const responseData = error && error.response ? error.response.data : null;
                if (responseData && responseData.redirect_url) {
                    windowObj.location.href = responseData.redirect_url;
                    return;
                }
                const message = responseData && responseData.message ? responseData.message : "Gagal mengirim ujian.";
                this.showAlert(message, "danger");
            } finally {
                this.isSubmitting = false;
                if (this.submitModal) {
                    this.submitModal.hide();
                }
            }
        }

        async reportViolation(type, description) {
            if (!this.config.violationUrl) {
                return;
            }
            if (this.isSubmitting || this.isReportingViolation) {
                return;
            }
            this.isReportingViolation = true;
            try {
                const response = await windowObj.axios.post(this.config.violationUrl, {
                    type,
                    description,
                });
                const data = response.data || {};
                if (this.payload && this.payload.anti_cheat) {
                    this.payload.anti_cheat.current_violations = data.violations_count || this.payload.anti_cheat.current_violations;
                    this.updateViolationChip();
                }
                this.showViolationModal(description, data.violations_count || 0);
                if (data.auto_submitted && data.redirect_url) {
                    windowObj.location.href = data.redirect_url;
                }
            } catch (error) {
                const responseData = error && error.response ? error.response.data : null;
                if (responseData && responseData.redirect_url) {
                    windowObj.location.href = responseData.redirect_url;
                }
            } finally {
                this.isReportingViolation = false;
            }
        }

        showViolationModal(message, count) {
            if (this.elements.violationMessage) {
                this.elements.violationMessage.textContent = message || "Pelanggaran terdeteksi selama ujian.";
            }
            if (this.elements.violationCountLabel) {
                this.elements.violationCountLabel.textContent = String(count || 0);
            }
            if (this.violationModal) {
                this.violationModal.show();
            }
        }

        setupAntiCheat() {
            const anti = this.payload && this.payload.anti_cheat ? this.payload.anti_cheat : {};
            if (!windowObj.ExamRoomAntiCheat) {
                return;
            }
            this.guard = windowObj.ExamRoomAntiCheat.installGuards({
                detectTabSwitch: Boolean(anti.detect_tab_switch),
                requireFullscreen: Boolean(anti.require_fullscreen),
                onViolation: (type, description) => this.reportViolation(type, description),
                onFullscreenStateChange: (active) => this.onFullscreenStateChange(active),
            });

            if (anti.require_fullscreen) {
                this.requestFullscreenMode();
            }
        }

        onFullscreenStateChange(active) {
            if (!this.elements.fullscreenOverlay) {
                return;
            }
            if (active) {
                this.elements.fullscreenOverlay.classList.add("d-none");
            } else {
                this.elements.fullscreenOverlay.classList.remove("d-none");
            }
        }

        requestFullscreenMode() {
            if (!windowObj.ExamRoomAntiCheat) {
                return;
            }
            windowObj.ExamRoomAntiCheat.requestFullscreen().then((active) => {
                this.onFullscreenStateChange(active || windowObj.ExamRoomAntiCheat.isFullscreen());
            });
        }

        async setupProctoring() {
            const anti = this.payload && this.payload.anti_cheat ? this.payload.anti_cheat : {};
            if (!anti.enable_screenshot_proctoring || !this.config.proctoringUrl) {
                return;
            }
            await this.prepareProctoringSource();
            const intervalSeconds = Math.max(parseInt(anti.screenshot_interval_seconds || 300, 10), 30);
            this.captureAndSendProctoring("startup");
            this.proctoringIntervalId = windowObj.setInterval(() => {
                this.captureAndSendProctoring("interval");
            }, intervalSeconds * 1000);
        }

        async prepareProctoringSource() {
            if (!windowObj.navigator || !windowObj.navigator.mediaDevices || typeof windowObj.navigator.mediaDevices.getUserMedia !== "function") {
                return;
            }
            try {
                const stream = await windowObj.navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: "user",
                        width: { ideal: 640 },
                        height: { ideal: 360 },
                    },
                    audio: false,
                });
                this.proctoringStream = stream;
                const video = documentObj.createElement("video");
                video.autoplay = true;
                video.muted = true;
                video.playsInline = true;
                video.srcObject = stream;
                this.proctoringVideo = video;
                if (typeof video.play === "function") {
                    await video.play().catch(() => {});
                }
            } catch (error) {
                if (!this.proctoringWarningShown) {
                    this.proctoringWarningShown = true;
                    this.showAlert("Akses kamera tidak tersedia. Sistem memakai snapshot fallback.", "warning");
                }
            }
        }

        buildProctoringFrame(label) {
            const width = 640;
            const height = 360;
            const canvas = documentObj.createElement("canvas");
            canvas.width = width;
            canvas.height = height;

            const context = canvas.getContext("2d");
            if (!context) {
                return "";
            }

            const videoReady = this.proctoringVideo
                && this.proctoringVideo.videoWidth > 0
                && this.proctoringVideo.videoHeight > 0;

            if (videoReady) {
                context.drawImage(this.proctoringVideo, 0, 0, width, height);
            } else {
                context.fillStyle = "#0f172a";
                context.fillRect(0, 0, width, height);
                context.fillStyle = "#e2e8f0";
                context.font = "600 22px Arial";
                context.fillText("CBT Proctoring Fallback", 20, 48);
                context.font = "16px Arial";
                context.fillText("Kamera tidak aktif / izin ditolak", 20, 84);
                context.fillText("Attempt: " + String(this.config.attemptId || "-"), 20, 116);
                context.fillText("Label: " + String(label || "capture"), 20, 146);
                context.fillText("Captured: " + (new Date()).toLocaleString("id-ID", { hour12: false }), 20, 176);
            }

            try {
                return canvas.toDataURL("image/jpeg", 0.72);
            } catch (error) {
                return "";
            }
        }

        captureAndSendProctoring(label) {
            if (!windowObj.axios || !this.config.proctoringUrl) {
                return;
            }
            const screenshotDataUrl = this.buildProctoringFrame(label);
            if (!screenshotDataUrl) {
                return;
            }
            windowObj.axios.post(this.config.proctoringUrl, {
                label: label || "capture",
                screenshot_data_url: screenshotDataUrl,
            }).catch(() => {});
        }
    }

    function bootstrapExamRoom() {
        const configEl = documentObj.getElementById("exam-room-config");
        if (!configEl) {
            return;
        }
        let parsedConfig = {};
        try {
            parsedConfig = JSON.parse(configEl.textContent || "{}");
        } catch (error) {
            parsedConfig = {};
        }
        setupAxiosCsrf();
        const app = new ExamRoomApp(parsedConfig);
        app.init();
        windowObj.examRoomApp = app;
    }

    if (documentObj.readyState === "loading") {
        documentObj.addEventListener("DOMContentLoaded", bootstrapExamRoom);
    } else {
        bootstrapExamRoom();
    }
})(window, document);
