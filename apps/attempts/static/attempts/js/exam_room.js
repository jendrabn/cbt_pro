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
            this.requiredMediaReady = false;
            this.mediaViolationLogged = false;
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
            this.setupRequiredMedia().then(() => this.setupProctoring());
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
            this.stopProctoringStream();
            if (this.guard && typeof this.guard.destroy === "function") {
                this.guard.destroy();
            }
        }

        cacheElements() {
            const byId = (id) => documentObj.getElementById(id);
            const byIds = (...ids) => ids.map((id) => byId(id)).find(Boolean) || null;
            this.elements = {
                alertHost: byId("examRoomAlertHost"),
                restrictionAlert: byId("navigationRestriction"),
                timerDisplay: byIds("timer", "timerDisplay"),
                timerChip: documentObj.querySelector(".timer-chip, .badge-timer"),
                violationCounterChip: byId("violationCounterChip"),
                attemptCounterBadge: byId("attemptCounterBadge"),
                questionNumberPill: byIds("qNum", "questionNumberPill"),
                questionTypeBadge: byIds("qType", "questionTypeBadge"),
                questionPointsLabel: byIds("qPoints", "questionPointsLabel"),
                questionTypeHint: byId("questionTypeHint"),
                footerCounter: byId("footerCounter"),
                autoSaveLabel: byId("autoSaveLabel"),
                questionPanel: byId("questionPanel"),
                questionText: byId("questionText"),
                questionImageWrap: byId("questionImageWrap"),
                questionImage: byId("questionImage"),
                questionMediaLimitNotice: byId("questionMediaLimitNotice"),
                questionAnswerContainer: byId("questionAnswerContainer"),
                flagQuestionBtn: byId("flagQuestionBtn"),
                prevQuestionBtn: byId("prevQuestionBtn"),
                nextQuestionBtn: byId("nextQuestionBtn"),
                clearAnswerBtn: byId("clearAnswerBtn"),
                questionGrid: byIds("navGrid", "questionGrid"),
                questionGridMobile: byIds("navGridMob", "questionGridMobile"),
                progressLabel: byIds("progLabel", "progressLabel"),
                progressBar: byIds("progBar", "progressBar"),
                summaryAnswered: byIds("statAns", "summaryAnswered"),
                summaryUnanswered: byIds("statUnans", "summaryUnanswered"),
                summaryMarked: byIds("statFlag", "summaryMarked"),
                progressLabelMobile: byIds("mProg", "progressLabelMobile"),
                progressBarMobile: byIds("mProgBar", "progressBarMobile"),
                summaryAnsweredMobile: byIds("mAns", "summaryAnsweredMobile"),
                summaryUnansweredMobile: byIds("mUnans", "summaryUnansweredMobile"),
                summaryMarkedMobile: byIds("mFlag", "summaryMarkedMobile"),
                antiCheatFullscreenRule: byId("antiCheatFullscreenRule"),
                antiCheatMediaRule: byId("antiCheatMediaRule"),
                antiCheatTabRule: byId("antiCheatTabRule"),
                antiCheatScreenshotRule: byId("antiCheatScreenshotRule"),
                antiCheatLimitRule: byId("antiCheatLimitRule"),
                antiCheatFullscreenRuleMobile: byId("antiCheatFullscreenRuleMobile"),
                antiCheatMediaRuleMobile: byId("antiCheatMediaRuleMobile"),
                antiCheatTabRuleMobile: byId("antiCheatTabRuleMobile"),
                antiCheatScreenshotRuleMobile: byId("antiCheatScreenshotRuleMobile"),
                antiCheatLimitRuleMobile: byId("antiCheatLimitRuleMobile"),
                permissionOverlay: byId("permissionOverlay"),
                permissionOverlayCameraStatus: byId("permissionOverlayCameraStatus"),
                permissionOverlayMicrophoneStatus: byId("permissionOverlayMicrophoneStatus"),
                permissionOverlayFullscreenStatus: byId("permissionOverlayFullscreenStatus"),
                permissionOverlayMessage: byId("permissionOverlayMessage"),
                requestMediaAccessBtn: byId("requestMediaAccessBtn"),
                requestPermissionFullscreenBtn: byId("requestPermissionFullscreenBtn"),
                fullscreenOverlay: byId("fullscreenOverlay"),
                returnFullscreenBtn: byId("returnFullscreenBtn"),
                mobileNav: byId("mobNav"),
                mobileNavBackdrop: documentObj.querySelector("#mobNav .mob-backdrop"),
                openMobileNavBtn: byId("openMobileNavBtn"),
                closeMobileNavBtn: byId("closeMobileNavBtn"),
                openSubmitModalBtn: byId("openSubmitModalBtn"),
                openSubmitModalBtnMobile: byId("openSubmitModalBtnMobile"),
                confirmSubmitBtn: byId("confirmSubmitBtn"),
                submitTotalCount: byId("submitTotalCount"),
                submitAnsweredCount: byIds("modalAns", "submitAnsweredCount"),
                submitUnansweredCount: byIds("modalUnans", "submitUnansweredCount"),
                submitMarkedCount: byIds("modalFlag", "submitMarkedCount"),
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
            if (this.elements.flagQuestionBtn) {
                this.elements.flagQuestionBtn.addEventListener("click", () => this.toggleReviewFlag());
            }
            if (this.elements.openMobileNavBtn) {
                this.elements.openMobileNavBtn.addEventListener("click", () => this.openMobileNav());
            }
            if (this.elements.closeMobileNavBtn) {
                this.elements.closeMobileNavBtn.addEventListener("click", () => this.closeMobileNav());
            }
            if (this.elements.mobileNavBackdrop) {
                this.elements.mobileNavBackdrop.addEventListener("click", () => this.closeMobileNav());
            }
            if (this.elements.openSubmitModalBtn) {
                this.elements.openSubmitModalBtn.addEventListener("click", () => this.openSubmitModal());
            }
            if (this.elements.openSubmitModalBtnMobile) {
                this.elements.openSubmitModalBtnMobile.addEventListener("click", () => this.openSubmitModal());
            }
            if (this.elements.confirmSubmitBtn) {
                this.elements.confirmSubmitBtn.addEventListener("click", () => this.submitExam(false));
            }
            if (this.elements.returnFullscreenBtn) {
                this.elements.returnFullscreenBtn.addEventListener("click", () => this.requestFullscreenMode());
            }
            if (this.elements.requestMediaAccessBtn) {
                this.elements.requestMediaAccessBtn.addEventListener("click", () => {
                    this.requestRequiredMediaPermissions();
                });
            }
            if (this.elements.requestPermissionFullscreenBtn) {
                this.elements.requestPermissionFullscreenBtn.addEventListener("click", () => this.requestFullscreenMode());
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

        getAntiCheatConfig() {
            return this.payload && this.payload.anti_cheat ? this.payload.anti_cheat : {};
        }

        getMarkedForReviewState() {
            const question = this.payload && this.payload.question ? this.payload.question : null;
            return Boolean(question && question.answer && question.answer.marked_for_review);
        }

        getQuestionTypeMeta(questionType) {
            const metaMap = {
                short_answer: {
                    label: "Jawaban Singkat",
                    hint: "",
                },
                multiple_choice: {
                    label: "Pilihan Ganda",
                    hint: "",
                },
                essay: {
                    label: "Esai",
                    hint: "",
                },
                checkbox: {
                    label: "Checkbox",
                    hint: "* Pilih satu atau lebih jawaban yang benar",
                },
                matching: {
                    label: "Matching",
                    hint: "",
                },
                ordering: {
                    label: "Ordering",
                    hint: "* Gunakan tombol panah untuk mengubah urutan",
                },
                fill_in_blank: {
                    label: "Fill In Blank",
                    hint: "",
                },
            };
            return metaMap[questionType] || {
                label: "Soal",
                hint: "",
            };
        }

        formatPoints(pointsValue) {
            const points = Number(pointsValue || 0);
            if (!Number.isFinite(points)) {
                return "0 poin";
            }
            return `${new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 }).format(points)} poin`;
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
            const question = this.payload && this.payload.question ? this.payload.question : null;
            const questionMeta = this.getQuestionTypeMeta(question ? question.question_type : "");

            if (this.elements.questionNumberPill) {
                this.elements.questionNumberPill.textContent = String(current);
            }
            if (this.elements.footerCounter) {
                this.elements.footerCounter.textContent = `${current} dari ${total}`;
            }
            if (this.elements.questionTypeBadge) {
                this.elements.questionTypeBadge.textContent = questionMeta.label;
                this.elements.questionTypeBadge.dataset.questionType = question ? (question.question_type || "") : "";
            }
            if (this.elements.questionPointsLabel) {
                this.elements.questionPointsLabel.textContent = this.formatPoints(question ? question.points : 0);
            }
            if (this.elements.questionTypeHint) {
                this.elements.questionTypeHint.textContent = questionMeta.hint;
                this.elements.questionTypeHint.classList.toggle("d-none", !questionMeta.hint);
            }
            if (this.elements.autoSaveLabel) {
                this.elements.autoSaveLabel.textContent = this.payload.last_saved_label || "Belum tersimpan";
            }
            if (this.elements.questionPanel) {
                this.elements.questionPanel.classList.add("active");
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
                    this.elements.questionText.classList.remove("fib-text");
                }
                if (this.elements.questionTypeHint) {
                    this.elements.questionTypeHint.textContent = "";
                    this.elements.questionTypeHint.classList.add("d-none");
                }
                if (this.elements.questionAnswerContainer) {
                    this.elements.questionAnswerContainer.innerHTML = "";
                    this.elements.questionAnswerContainer.dataset.questionType = "";
                }
                if (this.elements.questionMediaLimitNotice) {
                    this.elements.questionMediaLimitNotice.textContent = "";
                    this.elements.questionMediaLimitNotice.classList.add("d-none");
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

            if (this.elements.flagQuestionBtn) {
                this.elements.flagQuestionBtn.classList.toggle(
                    "is-active",
                    Boolean(question.answer && question.answer.marked_for_review)
                );
            }
            if (this.elements.questionAnswerContainer) {
                this.elements.questionAnswerContainer.dataset.questionType = question.question_type || "";
            }
            if (this.elements.questionText) {
                this.elements.questionText.dataset.questionType = question.question_type || "";
                this.elements.questionText.classList.toggle("fib-text", question.question_type === "fill_in_blank");
            }

            this.renderAnswerControl(question);
            this.applyMediaPlayLimits(question);
            this.updateNavigationButtons();
        }

        buildOptionContentHtml(option) {
            var optionHtml = option && option.text ? option.text : "";
            var legacyImageHtml = "";
            if (option && option.image_url && optionHtml.toLowerCase().indexOf("<img") === -1) {
                legacyImageHtml =
                    '<div class="mt-2"><img src="' + option.image_url + '" alt="Media opsi ' + option.letter + '" class="img-fluid rounded border"></div>';
            }
            return optionHtml + legacyImageHtml;
        }

        stripRichTextToPlainText(html, fallbackLabel) {
            const wrap = documentObj.createElement("div");
            wrap.innerHTML = html || "";
            const textValue = (wrap.textContent || wrap.innerText || "").replace(/\s+/g, " ").trim();
            return textValue || fallbackLabel || "";
        }

        escapeHtml(value) {
            return String(value || "")
                .replace(/&/g, "&amp;")
                .replace(/"/g, "&quot;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
        }

        normalizePlayLimit(value) {
            const parsed = parseInt(value || 0, 10);
            return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
        }

        getMediaPlayStorageKey(questionId, mediaType) {
            const attemptId = this.payload && this.payload.attempt_id ? this.payload.attempt_id : "attempt";
            return `play_${attemptId}_${questionId}_${mediaType}`;
        }

        getMediaPlayCount(questionId, mediaType) {
            if (!questionId || !windowObj.sessionStorage) {
                return 0;
            }
            try {
                const rawValue = windowObj.sessionStorage.getItem(this.getMediaPlayStorageKey(questionId, mediaType));
                const parsed = parseInt(rawValue || "0", 10);
                return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
            } catch (error) {
                return 0;
            }
        }

        setMediaPlayCount(questionId, mediaType, nextCount) {
            if (!questionId || !windowObj.sessionStorage) {
                return;
            }
            try {
                const normalizedCount = parseInt(nextCount || 0, 10);
                windowObj.sessionStorage.setItem(
                    this.getMediaPlayStorageKey(questionId, mediaType),
                    String(Number.isFinite(normalizedCount) && normalizedCount > 0 ? normalizedCount : 0)
                );
            } catch (error) {
                return;
            }
        }

        getQuestionMediaElements(mediaType) {
            const containers = [this.elements.questionText, this.elements.questionAnswerContainer].filter(Boolean);
            return containers.reduce((accumulator, container) => {
                return accumulator.concat(Array.from(container.querySelectorAll(mediaType)));
            }, []);
        }

        setMediaBlockedState(mediaElement, blocked) {
            if (!mediaElement) {
                return;
            }
            mediaElement.dataset.playLimitBlocked = blocked ? "1" : "0";
            if (blocked) {
                mediaElement.setAttribute("title", "Batas pemutaran tercapai");
            } else {
                mediaElement.removeAttribute("title");
            }
        }

        pauseMediaElement(mediaElement) {
            if (!mediaElement) {
                return;
            }
            if (typeof mediaElement.pause === "function") {
                mediaElement.pause();
            }
            try {
                mediaElement.currentTime = 0;
            } catch (error) {
                return;
            }
        }

        updateMediaLimitNotice(question) {
            if (!this.elements.questionMediaLimitNotice || !question) {
                return;
            }
            const questionId = question.question_id || "";
            const audioLimit = this.normalizePlayLimit(question.audio_play_limit);
            const videoLimit = this.normalizePlayLimit(question.video_play_limit);
            const messages = [];

            if (audioLimit) {
                const usedAudio = this.getMediaPlayCount(questionId, "audio");
                messages.push(`Audio tersisa ${Math.max(audioLimit - usedAudio, 0)} dari ${audioLimit} kali`);
            }
            if (videoLimit) {
                const usedVideo = this.getMediaPlayCount(questionId, "video");
                messages.push(`Video tersisa ${Math.max(videoLimit - usedVideo, 0)} dari ${videoLimit} kali`);
            }

            if (!messages.length) {
                this.elements.questionMediaLimitNotice.textContent = "";
                this.elements.questionMediaLimitNotice.classList.add("d-none");
                return;
            }

            this.elements.questionMediaLimitNotice.textContent = messages.join(" | ");
            this.elements.questionMediaLimitNotice.classList.remove("d-none");
        }

        enforceMediaPlayLimit(question, mediaType) {
            if (!question || !question.question_id) {
                return;
            }
            const limit = this.normalizePlayLimit(question[`${mediaType}_play_limit`]);
            const mediaElements = this.getQuestionMediaElements(mediaType);
            if (!limit || !mediaElements.length) {
                mediaElements.forEach((mediaElement) => this.setMediaBlockedState(mediaElement, false));
                return;
            }

            const syncBlockedState = () => {
                const isBlocked = this.getMediaPlayCount(question.question_id, mediaType) >= limit;
                mediaElements.forEach((mediaElement) => this.setMediaBlockedState(mediaElement, isBlocked));
            };

            syncBlockedState();
            mediaElements.forEach((mediaElement) => {
                mediaElement.addEventListener("play", () => {
                    const usedCount = this.getMediaPlayCount(question.question_id, mediaType);
                    if (usedCount >= limit) {
                        this.pauseMediaElement(mediaElement);
                        this.updateMediaLimitNotice(question);
                        syncBlockedState();
                        this.showAlert(
                            `Batas pemutaran ${mediaType === "audio" ? "audio" : "video"} untuk soal ini sudah tercapai.`,
                            "warning",
                            2800
                        );
                        return;
                    }

                    this.setMediaPlayCount(question.question_id, mediaType, usedCount + 1);
                    this.updateMediaLimitNotice(question);
                    syncBlockedState();
                });
            });
        }

        applyMediaPlayLimits(question) {
            this.updateMediaLimitNotice(question);
            this.enforceMediaPlayLimit(question, "audio");
            this.enforceMediaPlayLimit(question, "video");
        }

        renderOrderingControl(question, currentNumber) {
            const rawItems = Array.isArray(question.ordering_items)
                ? question.ordering_items.map((item) => ({
                    id: String(item.id),
                    text: item.text || "",
                }))
                : [];
            const savedOrder = Array.isArray(question.answer && question.answer.answer_order_json)
                ? question.answer.answer_order_json.map((itemId) => String(itemId))
                : [];
            const itemMap = new Map(rawItems.map((item) => [item.id, item]));
            const orderingItems = [];

            savedOrder.forEach((itemId) => {
                if (itemMap.has(itemId)) {
                    orderingItems.push(itemMap.get(itemId));
                    itemMap.delete(itemId);
                }
            });
            rawItems.forEach((item) => {
                if (itemMap.has(item.id)) {
                    orderingItems.push(itemMap.get(item.id));
                    itemMap.delete(item.id);
                }
            });

            if (!orderingItems.length) {
                const emptyState = documentObj.createElement("div");
                emptyState.className = "alert alert-warning py-2 mb-0";
                emptyState.textContent = "Item ordering untuk soal ini tidak tersedia.";
                this.elements.questionAnswerContainer.appendChild(emptyState);
                return;
            }

            const listWrap = documentObj.createElement("div");
            listWrap.id = "order-list";
            this.elements.questionAnswerContainer.appendChild(listWrap);
            let draggedIndex = null;

            const persistOrder = () => {
                this.saveCurrentAnswer({
                    question_number: currentNumber,
                    answer_order_json: orderingItems.map((item) => item.id),
                    is_marked_for_review: this.getMarkedForReviewState(),
                });
            };

            const moveItem = (fromIndex, toIndex) => {
                if (fromIndex < 0 || fromIndex >= orderingItems.length) {
                    return;
                }
                if (toIndex < 0 || toIndex >= orderingItems.length) {
                    return;
                }
                if (fromIndex === toIndex) {
                    return;
                }
                const movedItem = orderingItems.splice(fromIndex, 1)[0];
                orderingItems.splice(toIndex, 0, movedItem);
                renderItems();
                persistOrder();
            };

            const renderItems = () => {
                listWrap.innerHTML = "";
                orderingItems.forEach((item, index) => {
                    const card = documentObj.createElement("div");
                    card.className = "order-item";
                    card.draggable = true;
                    card.innerHTML = `
                        <i class="ri-draggable drag-handle" aria-hidden="true"></i>
                        <div class="order-num">${index + 1}</div>
                        <span class="order-text richtext-content">${item.text}</span>
                        <div class="order-arrows">
                            <button type="button" class="btn-arrow" data-direction="up" ${index === 0 ? "disabled" : ""} title="Naikkan urutan">
                                <i class="ri-arrow-up-s-line" aria-hidden="true"></i>
                            </button>
                            <button type="button" class="btn-arrow" data-direction="down" ${index === orderingItems.length - 1 ? "disabled" : ""} title="Turunkan urutan">
                                <i class="ri-arrow-down-s-line" aria-hidden="true"></i>
                            </button>
                        </div>
                    `;
                    card.addEventListener("dragstart", (event) => {
                        draggedIndex = index;
                        card.classList.add("dragging");
                        if (event.dataTransfer) {
                            event.dataTransfer.effectAllowed = "move";
                            event.dataTransfer.setData("text/plain", String(index));
                        }
                    });
                    card.addEventListener("dragend", () => {
                        draggedIndex = null;
                        card.classList.remove("dragging");
                    });
                    card.addEventListener("dragover", (event) => {
                        event.preventDefault();
                    });
                    card.addEventListener("drop", (event) => {
                        event.preventDefault();
                        const sourceIndex = draggedIndex;
                        draggedIndex = null;
                        if (sourceIndex === null) {
                            return;
                        }
                        moveItem(sourceIndex, index);
                    });
                    const moveUpBtn = card.querySelector('[data-direction="up"]');
                    const moveDownBtn = card.querySelector('[data-direction="down"]');
                    if (moveUpBtn) {
                        moveUpBtn.addEventListener("click", () => {
                            moveItem(index, index - 1);
                        });
                    }
                    if (moveDownBtn) {
                        moveDownBtn.addEventListener("click", () => {
                            moveItem(index, index + 1);
                        });
                    }
                    listWrap.appendChild(card);
                });
            };

            renderItems();
        }

        renderMatchingControl(question, currentNumber) {
            const matchingPairs = Array.isArray(question.matching_pairs) ? question.matching_pairs.slice() : [];
            const answerChoices = Array.isArray(question.matching_answer_choices)
                ? question.matching_answer_choices.slice()
                : [];
            const workingMap = Object.assign({}, (question.answer && question.answer.answer_matching_json) || {});

            if (!matchingPairs.length || !answerChoices.length) {
                const emptyState = documentObj.createElement("div");
                emptyState.className = "alert alert-warning py-2 mb-0";
                emptyState.textContent = "Data matching untuk soal ini belum lengkap.";
                this.elements.questionAnswerContainer.appendChild(emptyState);
                return;
            }

            const answerBankWrap = documentObj.createElement("div");
            answerBankWrap.className = "answer-bank";
            const answerBankItemsHtml = answerChoices.map((choice, index) => {
                const label = this.escapeHtml(
                    this.stripRichTextToPlainText(choice.answer_text, `Pilihan ${index + 1}`)
                );
                return label;
            }).join(" • ");
            answerBankWrap.innerHTML = `
                <i class="ri-list-check-3"></i>&nbsp;<strong>Bank Jawaban:</strong> ${answerBankItemsHtml}
            `;
            const normalizedAnswerBankItemsHtml = answerChoices.map((choice, index) => {
                return this.escapeHtml(
                    this.stripRichTextToPlainText(choice.answer_text, `Pilihan ${index + 1}`)
                );
            }).join(" &bull; ");
            answerBankWrap.innerHTML = `
                <i class="ri-list-check-3"></i>&nbsp;<strong>Bank Jawaban:</strong> ${normalizedAnswerBankItemsHtml}
            `;
            this.elements.questionAnswerContainer.appendChild(answerBankWrap);

            const pairsWrap = documentObj.createElement("div");
            pairsWrap.className = "vstack gap-3 matching-inline-list";
            this.elements.questionAnswerContainer.appendChild(pairsWrap);

            const persistMap = () => {
                this.saveCurrentAnswer({
                    question_number: currentNumber,
                    answer_matching_json: workingMap,
                    is_marked_for_review: this.getMarkedForReviewState(),
                });
            };

            const clearMatchingChoiceAssignment = (choiceId, excludedPromptId) => {
                Object.keys(workingMap).forEach((promptId) => {
                    if (promptId !== excludedPromptId && workingMap[promptId] === choiceId) {
                        delete workingMap[promptId];
                    }
                });
            };

            const assignChoiceToPrompt = (promptId, choiceId) => {
                if (!promptId) {
                    return;
                }
                delete workingMap[promptId];
                if (!choiceId) {
                    return;
                }
                clearMatchingChoiceAssignment(choiceId, promptId);
                workingMap[promptId] = choiceId;
            };

            const renderMatchingRows = () => {
                pairsWrap.innerHTML = "";

                matchingPairs.forEach((pair, pairIndex) => {
                    const card = documentObj.createElement("div");
                    card.className = "match-row matching-inline-row";
                    const currentAnswerId = workingMap[pair.id] || "";
                    const usedChoiceIds = new Set(
                        Object.keys(workingMap)
                            .filter((promptId) => promptId !== pair.id && workingMap[promptId])
                            .map((promptId) => workingMap[promptId])
                    );
                    const choiceOptionsHtml = answerChoices.map((choice, choiceIndex) => {
                        const label = this.escapeHtml(
                            this.stripRichTextToPlainText(choice.answer_text, `Pilihan ${choiceIndex + 1}`)
                        );
                        const selectedAttr = choice.id === currentAnswerId ? " selected" : "";
                        const disabledAttr = choice.id !== currentAnswerId && usedChoiceIds.has(choice.id) ? " disabled" : "";
                        return `<option value="${choice.id}"${selectedAttr}${disabledAttr}>${label}</option>`;
                    }).join("");

                    card.innerHTML = `
                        <div class="match-term matching-inline-row__label">
                            <div class="richtext-content mb-0">${pair.prompt_text || ""}</div>
                        </div>
                        <div class="match-arrow matching-inline-row__arrow" aria-hidden="true">
                            <i class="ri-arrow-right-line"></i>
                        </div>
                        <div class="matching-inline-row__control">
                            <label class="visually-hidden" for="matching-answer-${pair.id}">Pilih jawaban untuk pasangan ${pairIndex + 1}</label>
                            <select id="matching-answer-${pair.id}" class="match-select matching-answer-select" data-pair-id="${pair.id}">
                                <option value="">Pilih jawaban...</option>
                                ${choiceOptionsHtml}
                            </select>
                        </div>
                    `;

                    const selectEl = card.querySelector(".matching-answer-select");
                    if (selectEl) {
                        selectEl.addEventListener("change", (event) => {
                            const nextAnswerId = event.target.value || "";
                            assignChoiceToPrompt(pair.id, nextAnswerId);
                            renderMatchingRows();
                            persistMap();
                        });
                    }

                    pairsWrap.appendChild(card);
                });
            };

            renderMatchingRows();
        }

        renderFillInBlankControl(question, currentNumber) {
            const workingAnswers = Object.assign({}, (question.answer && question.answer.answer_blanks_json) || {});
            const placeholderPattern = /\{\{\s*(\d+)\s*\}\}/g;
            const questionHtml = question.question_text || "";
            const renderedHtml = questionHtml.replace(placeholderPattern, (matchValue, rawNumber) => {
                const blankNumber = String(parseInt(rawNumber, 10));
                const currentValue = Object.prototype.hasOwnProperty.call(workingAnswers, blankNumber)
                    ? workingAnswers[blankNumber]
                    : "";
                return (
                    '<input type="text" class="fib-input fill-blank-input" ' +
                    `data-blank-number="${blankNumber}" ` +
                    `value="${this.escapeHtml(currentValue)}" ` +
                    'placeholder="...">'
                );
            });

            if (this.elements.questionText) {
                this.elements.questionText.innerHTML = renderedHtml;
            }

            const blankInputs = this.elements.questionText
                ? Array.from(this.elements.questionText.querySelectorAll(".fill-blank-input"))
                : [];

            if (!blankInputs.length) {
                const emptyState = documentObj.createElement("div");
                emptyState.className = "alert alert-warning py-2 mb-0";
                emptyState.textContent = "Placeholder blank tidak ditemukan pada teks soal.";
                this.elements.questionAnswerContainer.appendChild(emptyState);
                return;
            }

            const debouncedSave = (windowObj.ExamRoomAutoSave && windowObj.ExamRoomAutoSave.debounce)
                ? windowObj.ExamRoomAutoSave.debounce((payloadValue) => {
                    this.saveCurrentAnswer({
                        question_number: currentNumber,
                        answer_blanks_json: payloadValue,
                        is_marked_for_review: this.getMarkedForReviewState(),
                    });
                }, 600)
                : ((payloadValue) => {
                    this.saveCurrentAnswer({
                        question_number: currentNumber,
                        answer_blanks_json: payloadValue,
                        is_marked_for_review: this.getMarkedForReviewState(),
                    });
                });

            blankInputs.forEach((inputEl) => {
                inputEl.addEventListener("input", (event) => {
                    const blankNumber = event.target.dataset.blankNumber || "";
                    if (!blankNumber) {
                        return;
                    }
                    workingAnswers[blankNumber] = event.target.value || "";
                    debouncedSave(Object.assign({}, workingAnswers));
                });
            });
        }

        renderAnswerControl(question) {
            if (!this.elements.questionAnswerContainer) {
                return;
            }
            this.elements.questionAnswerContainer.innerHTML = "";

            const currentNumber = this.getCurrentNumber();
            if (question.question_type === "multiple_choice" || question.question_type === "checkbox") {
                const selectedOptionId = (question.answer && question.answer.selected_option_id) || "";
                const selectedOptionIds = Array.isArray(question.answer && question.answer.selected_option_ids)
                    ? question.answer.selected_option_ids
                    : [];

                (question.options || []).forEach((option) => {
                    const optionCard = documentObj.createElement("div");
                    optionCard.className = question.question_type === "checkbox"
                        ? "cb-option"
                        : "mc-option";
                    const isSelected = question.question_type === "multiple_choice"
                        ? (selectedOptionId && selectedOptionId === option.id)
                        : selectedOptionIds.indexOf(option.id) >= 0;
                    if (isSelected) {
                        optionCard.classList.add(question.question_type === "checkbox" ? "checked" : "selected");
                    }
                    optionCard.setAttribute("role", "button");
                    optionCard.setAttribute("tabindex", "0");
                    optionCard.setAttribute("aria-pressed", String(isSelected));
                    if (question.question_type === "checkbox") {
                        optionCard.innerHTML = `
                            <input type="checkbox" tabindex="-1" aria-hidden="true">
                            <div class="cb-box" aria-hidden="true"></div>
                            <span class="cb-text richtext-content">${option.letter}.&nbsp;${this.buildOptionContentHtml(option)}</span>
                        `;
                    } else {
                        optionCard.innerHTML = `
                            <input type="radio" tabindex="-1" aria-hidden="true">
                            <div class="mc-label">${option.letter}</div>
                            <span class="mc-text richtext-content">${this.buildOptionContentHtml(option)}</span>
                        `;
                    }
                    const saveSelection = () => {
                        if (question.question_type === "checkbox") {
                            const nextSelectedIds = selectedOptionIds.slice();
                            const selectedIndex = nextSelectedIds.indexOf(option.id);
                            if (selectedIndex >= 0) {
                                nextSelectedIds.splice(selectedIndex, 1);
                            } else {
                                nextSelectedIds.push(option.id);
                            }
                            this.saveCurrentAnswer({
                                question_number: currentNumber,
                                selected_option_ids: nextSelectedIds,
                                is_marked_for_review: this.getMarkedForReviewState(),
                            });
                            return;
                        }
                        this.saveCurrentAnswer({
                            question_number: currentNumber,
                            selected_option_id: option.id,
                            is_marked_for_review: this.getMarkedForReviewState(),
                        });
                    };
                    optionCard.addEventListener("click", saveSelection);
                    optionCard.addEventListener("keydown", (event) => {
                        if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            saveSelection();
                        }
                    });
                    this.elements.questionAnswerContainer.appendChild(optionCard);
                });
                return;
            }

            if (question.question_type === "ordering") {
                this.renderOrderingControl(question, currentNumber);
                return;
            }

            if (question.question_type === "matching") {
                this.renderMatchingControl(question, currentNumber);
                return;
            }

            if (question.question_type === "fill_in_blank") {
                this.renderFillInBlankControl(question, currentNumber);
                return;
            }

            const textWrap = documentObj.createElement("div");
            textWrap.className = question.question_type === "essay" ? "essay-wrap" : "short-wrap";
            const inputId = question.question_type === "essay" ? "essayAnswerInput" : "shortAnswerInput";
            const placeholder = question.question_type === "essay"
                ? "Jawaban Esai"
                : "Ketik jawaban singkat Anda di sini...";
            const answerValue = (question.answer && question.answer.answer_text) || "";

            let inputEl = null;
            if (question.question_type === "essay") {
                inputEl = documentObj.createElement("textarea");
                inputEl.rows = 10;
                inputEl.className = "essay-textarea";
            } else {
                inputEl = documentObj.createElement("input");
                inputEl.type = "text";
                inputEl.className = "short-input";
            }
            inputEl.id = inputId;
            inputEl.placeholder = placeholder;
            inputEl.value = answerValue;
            inputEl.autocomplete = "off";
            textWrap.appendChild(inputEl);

            const helper = documentObj.createElement("div");
            helper.className = "char-counter";
            helper.id = "textAnswerCounter";
            helper.textContent = question.question_type === "essay"
                ? `${answerValue.length}/1000 karakter`
                : `${answerValue.length}/200 karakter`;
            textWrap.appendChild(helper);

            this.elements.questionAnswerContainer.appendChild(textWrap);

            const debouncedSave = (windowObj.ExamRoomAutoSave && windowObj.ExamRoomAutoSave.debounce)
                ? windowObj.ExamRoomAutoSave.debounce((value) => {
                    this.saveCurrentAnswer({
                        question_number: currentNumber,
                        answer_text: value,
                        is_marked_for_review: this.getMarkedForReviewState(),
                    });
                }, 700)
                : ((value) => {
                    this.saveCurrentAnswer({
                        question_number: currentNumber,
                        answer_text: value,
                        is_marked_for_review: this.getMarkedForReviewState(),
                    });
                });

            inputEl.addEventListener("input", (event) => {
                const value = event.target.value || "";
                helper.textContent = question.question_type === "essay"
                    ? `${value.length}/1000 karakter`
                    : `${value.length}/200 karakter`;
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
            const isLastQuestion = Boolean(nav.is_last || current >= total);

            if (this.elements.prevQuestionBtn) {
                this.elements.prevQuestionBtn.disabled = !nav.can_previous || current <= 1;
            }
            if (this.elements.nextQuestionBtn) {
                this.elements.nextQuestionBtn.innerHTML = isLastQuestion
                    ? '<span class="lbl">Kirim Ujian</span><i class="ri-send-plane-line"></i>'
                    : '<span class="lbl">Selanjutnya</span><i class="ri-arrow-right-s-line"></i>';
                this.elements.nextQuestionBtn.disabled = !isLastQuestion && !nav.can_next;
            }
        }

        renderQuestionMap() {
            const mapRows = this.payload.question_map || [];
            const grids = [
                { element: this.elements.questionGrid, baseClass: "nav-btn" },
                { element: this.elements.questionGridMobile, baseClass: "nav-btn-mob" },
            ].filter((grid) => grid.element);

            if (!grids.length) {
                return;
            }

            const resolveMapState = (item) => {
                if (item.locked) {
                    return "locked";
                }
                if (item.current) {
                    return "current";
                }
                if (item.marked) {
                    return "flagged";
                }
                if (item.answered) {
                    return "answered";
                }
                return "empty";
            };

            grids.forEach((grid) => {
                grid.element.innerHTML = "";
                mapRows.forEach((item) => {
                    const btn = documentObj.createElement("button");
                    const stateClass = resolveMapState(item);
                    btn.type = "button";
                    btn.className = grid.baseClass;
                    btn.classList.add(stateClass);
                    btn.textContent = item.number;
                    btn.title = item.locked
                        ? `Soal ${item.number} terkunci`
                        : `Ke soal nomor ${item.number}`;
                    btn.disabled = Boolean(item.locked);
                    btn.setAttribute("aria-current", item.current ? "page" : "false");
                    btn.addEventListener("click", () => {
                        if (grid.element === this.elements.questionGridMobile) {
                            this.closeMobileNav();
                        }
                        this.loadQuestion(item.number);
                    });
                    grid.element.appendChild(btn);
                });
            });
        }

        renderSummary() {
            const summary = this.payload && this.payload.summary ? this.payload.summary : {};
            const total = parseInt(summary.total_questions || 0, 10);
            const answered = parseInt(summary.answered_count || 0, 10);
            const unanswered = parseInt(summary.unanswered_count || 0, 10);
            const marked = parseInt(summary.marked_count || 0, 10);
            const percentage = total > 0 ? Math.min(Math.round((answered / total) * 100), 100) : 0;

            [
                this.elements.progressLabel,
                this.elements.progressLabelMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = `${answered}/${total}`;
            });
            [
                this.elements.progressBar,
                this.elements.progressBarMobile,
            ].filter(Boolean).forEach((element) => {
                element.style.width = `${percentage}%`;
            });
            [
                this.elements.summaryAnswered,
                this.elements.summaryAnsweredMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = String(answered);
            });
            [
                this.elements.summaryUnanswered,
                this.elements.summaryUnansweredMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = String(unanswered);
            });
            [
                this.elements.summaryMarked,
                this.elements.summaryMarkedMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = String(marked);
            });
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
            const antiCheat = this.getAntiCheatConfig();
            let mediaRuleText = "Perangkat pengawasan: Tidak wajib";
            if (antiCheat.require_camera && antiCheat.require_microphone) {
                mediaRuleText = "Perangkat pengawasan: Kamera dan mikrofon wajib";
            } else if (antiCheat.require_camera) {
                mediaRuleText = "Perangkat pengawasan: Kamera wajib";
            } else if (antiCheat.require_microphone) {
                mediaRuleText = "Perangkat pengawasan: Mikrofon wajib";
            }
            const fullscreenRuleText = `Mode fullscreen: ${antiCheat.require_fullscreen ? "Wajib" : "Tidak wajib"}`;
            const tabRuleText = `Deteksi perpindahan tab: ${antiCheat.detect_tab_switch ? "Aktif" : "Tidak aktif"}`;
            const screenshotRuleText = antiCheat.enable_screenshot_proctoring
                ? `Screenshot berkala: Aktif setiap ${antiCheat.screenshot_interval_seconds} detik`
                : "Screenshot berkala: Tidak aktif";
            const limitRuleText = `Batas pelanggaran: ${antiCheat.max_violations_allowed}`;

            [
                this.elements.antiCheatMediaRule,
                this.elements.antiCheatMediaRuleMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = mediaRuleText;
            });
            [
                this.elements.antiCheatFullscreenRule,
                this.elements.antiCheatFullscreenRuleMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = fullscreenRuleText;
            });
            [
                this.elements.antiCheatTabRule,
                this.elements.antiCheatTabRuleMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = tabRuleText;
            });
            [
                this.elements.antiCheatScreenshotRule,
                this.elements.antiCheatScreenshotRuleMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = screenshotRuleText;
            });
            [
                this.elements.antiCheatLimitRule,
                this.elements.antiCheatLimitRuleMobile,
            ].filter(Boolean).forEach((element) => {
                element.textContent = limitRuleText;
            });
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
            this.elements.violationCounterChip.textContent = `${count} Pelanggaran`;
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

        openMobileNav() {
            if (this.elements.mobileNav) {
                this.elements.mobileNav.classList.add("open");
            }
        }

        closeMobileNav() {
            if (this.elements.mobileNav) {
                this.elements.mobileNav.classList.remove("open");
            }
        }

        toggleReviewFlag() {
            this.saveCurrentAnswer({
                question_number: this.getCurrentNumber(),
                is_marked_for_review: !this.getMarkedForReviewState(),
            });
        }

        openSubmitModal() {
            this.closeMobileNav();
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
                is_marked_for_review: this.getMarkedForReviewState(),
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
                this.renderPermissionOverlayState();
                return;
            }
            if (active) {
                this.elements.fullscreenOverlay.classList.add("d-none");
            } else {
                this.elements.fullscreenOverlay.classList.remove("d-none");
            }
            this.renderPermissionOverlayState();
        }

        requestFullscreenMode() {
            if (!windowObj.ExamRoomAntiCheat) {
                return;
            }
            windowObj.ExamRoomAntiCheat.requestFullscreen().then((active) => {
                this.onFullscreenStateChange(active || windowObj.ExamRoomAntiCheat.isFullscreen());
            });
        }

        stopProctoringStream() {
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
        }

        setProctoringStream(stream) {
            this.stopProctoringStream();
            this.proctoringStream = stream;
            if (!stream) {
                this.requiredMediaReady = false;
                this.renderPermissionOverlayState();
                return;
            }

            this.requiredMediaReady = true;
            this.mediaViolationLogged = false;
            this.renderPermissionOverlayState();
            if (typeof stream.getVideoTracks === "function" && stream.getVideoTracks().length > 0) {
                const video = documentObj.createElement("video");
                video.autoplay = true;
                video.muted = true;
                video.playsInline = true;
                video.srcObject = stream;
                this.proctoringVideo = video;
                if (typeof video.play === "function") {
                    video.play().catch(() => {});
                }
            }

            stream.getTracks().forEach((track) => {
                if (track && typeof track.addEventListener === "function") {
                    track.addEventListener("ended", () => {
                        const anti = this.getAntiCheatConfig();
                        let message = "Akses perangkat pengawasan terputus di tengah ujian.";
                        if (anti.require_camera && anti.require_microphone) {
                            message = "Akses kamera atau mikrofon terputus di tengah ujian.";
                        } else if (anti.require_camera) {
                            message = "Akses kamera terputus di tengah ujian.";
                        } else if (anti.require_microphone) {
                            message = "Akses mikrofon terputus di tengah ujian.";
                        }
                        this.handleRequiredMediaLoss(message);
                    });
                }
            });
        }

        handleRequiredMediaLoss(message) {
            if (this.proctoringIntervalId) {
                windowObj.clearInterval(this.proctoringIntervalId);
                this.proctoringIntervalId = null;
            }
            this.requiredMediaReady = false;
            this.showPermissionOverlay(`${message} Izinkan kembali untuk melanjutkan ujian.`);
            if (!this.mediaViolationLogged) {
                this.mediaViolationLogged = true;
                this.reportViolation(
                    "suspicious_activity",
                    message || "Akses perangkat pengawasan dicabut atau terputus saat ujian berlangsung."
                );
            }
        }

        setPermissionOverlayMessage(message, tone = "warning") {
            if (!this.elements.permissionOverlayMessage) {
                return;
            }
            this.elements.permissionOverlayMessage.className = `alert alert-${tone} py-2 small`;
            this.elements.permissionOverlayMessage.textContent = message;
            this.elements.permissionOverlayMessage.classList.remove("d-none");
        }

        clearPermissionOverlayMessage() {
            if (!this.elements.permissionOverlayMessage) {
                return;
            }
            this.elements.permissionOverlayMessage.textContent = "";
            this.elements.permissionOverlayMessage.classList.add("d-none");
        }

        renderPermissionOverlayState() {
            const anti = this.getAntiCheatConfig();
            const fullscreenRequired = Boolean(anti.require_fullscreen);
            if (this.elements.permissionOverlayCameraStatus) {
                this.elements.permissionOverlayCameraStatus.textContent = this.requiredMediaReady ? "Diizinkan" : "Belum diizinkan";
            }
            if (this.elements.permissionOverlayMicrophoneStatus) {
                this.elements.permissionOverlayMicrophoneStatus.textContent = this.requiredMediaReady ? "Diizinkan" : "Belum diizinkan";
            }
            if (this.elements.permissionOverlayFullscreenStatus) {
                this.elements.permissionOverlayFullscreenStatus.textContent = fullscreenRequired
                    ? (windowObj.ExamRoomAntiCheat && windowObj.ExamRoomAntiCheat.isFullscreen() ? "Aktif" : "Belum aktif")
                    : "Tidak wajib";
            }
        }

        showPermissionOverlay(message) {
            this.renderPermissionOverlayState();
            if (message) {
                this.setPermissionOverlayMessage(message, "warning");
            }
            if (this.elements.permissionOverlay) {
                this.elements.permissionOverlay.classList.remove("d-none");
            }
        }

        hidePermissionOverlay() {
            this.clearPermissionOverlayMessage();
            if (this.elements.permissionOverlay) {
                this.elements.permissionOverlay.classList.add("d-none");
            }
        }

        async setupRequiredMedia() {
            const anti = this.getAntiCheatConfig();
            if (!anti.require_camera && !anti.require_microphone) {
                this.requiredMediaReady = true;
                this.hidePermissionOverlay();
                return true;
            }
            const granted = await this.requestRequiredMediaPermissions();
            if (!granted) {
                if (anti.require_camera && anti.require_microphone) {
                    this.showPermissionOverlay("Kamera dan mikrofon wajib diizinkan sebelum ujian dapat dilanjutkan.");
                } else if (anti.require_camera) {
                    this.showPermissionOverlay("Kamera wajib diizinkan sebelum ujian dapat dilanjutkan.");
                } else {
                    this.showPermissionOverlay("Mikrofon wajib diizinkan sebelum ujian dapat dilanjutkan.");
                }
                return false;
            }
            this.hidePermissionOverlay();
            return true;
        }

        async requestRequiredMediaPermissions() {
            const anti = this.getAntiCheatConfig();
            const requireCamera = Boolean(anti.require_camera);
            const requireMicrophone = Boolean(anti.require_microphone);
            if (!requireCamera && !requireMicrophone) {
                this.requiredMediaReady = true;
                return true;
            }
            if (!windowObj.navigator || !windowObj.navigator.mediaDevices || typeof windowObj.navigator.mediaDevices.getUserMedia !== "function") {
                this.requiredMediaReady = false;
                this.showPermissionOverlay("Browser ini tidak mendukung akses perangkat yang diwajibkan ujian.");
                return false;
            }
            try {
                const stream = await windowObj.navigator.mediaDevices.getUserMedia({
                    video: requireCamera ? {
                        facingMode: "user",
                        width: { ideal: 640 },
                        height: { ideal: 360 },
                    } : false,
                    audio: requireMicrophone,
                });
                this.setProctoringStream(stream);
                this.hidePermissionOverlay();
                this.setupProctoring();
                return true;
            } catch (error) {
                this.requiredMediaReady = false;
                if (requireCamera && requireMicrophone) {
                    this.showPermissionOverlay("Izin kamera dan mikrofon ditolak. Silakan izinkan dulu untuk melanjutkan ujian.");
                } else if (requireCamera) {
                    this.showPermissionOverlay("Izin kamera ditolak. Silakan izinkan dulu untuk melanjutkan ujian.");
                } else {
                    this.showPermissionOverlay("Izin mikrofon ditolak. Silakan izinkan dulu untuk melanjutkan ujian.");
                }
                return false;
            }
        }

        async setupProctoring() {
            const anti = this.payload && this.payload.anti_cheat ? this.payload.anti_cheat : {};
            if (!anti.enable_screenshot_proctoring || !this.config.proctoringUrl || !this.requiredMediaReady) {
                return;
            }
            if (this.proctoringIntervalId) {
                return;
            }
            const intervalSeconds = Math.max(parseInt(anti.screenshot_interval_seconds || 300, 10), 30);
            this.captureAndSendProctoring("startup");
            this.proctoringIntervalId = windowObj.setInterval(() => {
                this.captureAndSendProctoring("interval");
            }, intervalSeconds * 1000);
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
