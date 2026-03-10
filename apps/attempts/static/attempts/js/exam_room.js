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
                questionMediaLimitNotice: byId("questionMediaLimitNotice"),
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
                antiCheatMediaRule: byId("antiCheatMediaRule"),
                antiCheatTabRule: byId("antiCheatTabRule"),
                antiCheatScreenshotRule: byId("antiCheatScreenshotRule"),
                antiCheatLimitRule: byId("antiCheatLimitRule"),
                permissionOverlay: byId("permissionOverlay"),
                permissionOverlayCameraStatus: byId("permissionOverlayCameraStatus"),
                permissionOverlayMicrophoneStatus: byId("permissionOverlayMicrophoneStatus"),
                permissionOverlayFullscreenStatus: byId("permissionOverlayFullscreenStatus"),
                permissionOverlayMessage: byId("permissionOverlayMessage"),
                requestMediaAccessBtn: byId("requestMediaAccessBtn"),
                requestPermissionFullscreenBtn: byId("requestPermissionFullscreenBtn"),
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

            if (this.elements.markReviewCheckbox) {
                this.elements.markReviewCheckbox.checked = Boolean(question.answer && question.answer.marked_for_review);
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
            const helper = documentObj.createElement("div");
            helper.className = "small text-muted mb-2";
            helper.textContent = "Seret item ke posisi yang benar. Tombol naik/turun tetap tersedia sebagai fallback.";
            this.elements.questionAnswerContainer.appendChild(helper);

            const orderingItems = Array.isArray(question.ordering_items)
                ? question.ordering_items.map((item) => ({
                    id: item.id,
                    text: item.text || "",
                }))
                : [];

            if (!orderingItems.length) {
                const emptyState = documentObj.createElement("div");
                emptyState.className = "alert alert-warning py-2 mb-0";
                emptyState.textContent = "Item ordering untuk soal ini tidak tersedia.";
                this.elements.questionAnswerContainer.appendChild(emptyState);
                return;
            }

            const listWrap = documentObj.createElement("div");
            listWrap.className = "d-grid gap-2 ordering-list-surface";
            this.elements.questionAnswerContainer.appendChild(listWrap);
            let draggedIndex = null;

            const persistOrder = () => {
                this.saveCurrentAnswer({
                    question_number: currentNumber,
                    answer_order_json: orderingItems.map((item) => item.id),
                    is_marked_for_review: this.elements.markReviewCheckbox
                        ? Boolean(this.elements.markReviewCheckbox.checked)
                        : false,
                });
            };

            const moveItem = (fromIndex, toIndex) => {
                if (fromIndex < 0 || fromIndex >= orderingItems.length) {
                    return;
                }
                if (toIndex < 0 || toIndex > orderingItems.length) {
                    return;
                }
                if (fromIndex === toIndex || fromIndex + 1 === toIndex) {
                    return;
                }
                const movedItem = orderingItems.splice(fromIndex, 1)[0];
                const insertionIndex = fromIndex < toIndex ? toIndex - 1 : toIndex;
                orderingItems.splice(insertionIndex, 0, movedItem);
                renderItems();
                persistOrder();
            };

            const clearOrderingDropTargets = () => {
                listWrap.classList.remove("ordering-drop-target");
                Array.from(listWrap.querySelectorAll(".ordering-draggable-card")).forEach((cardEl) => {
                    cardEl.classList.remove("ordering-drop-target", "is-dragging");
                });
            };

            const renderItems = () => {
                listWrap.innerHTML = "";
                orderingItems.forEach((item, index) => {
                    const card = documentObj.createElement("div");
                    card.className = "border rounded-3 p-3 bg-white ordering-draggable-card";
                    card.draggable = true;
                    card.innerHTML = `
                        <div class="d-flex align-items-start gap-3">
                            <div class="rounded-circle bg-warning-subtle text-warning-emphasis fw-semibold d-flex align-items-center justify-content-center flex-shrink-0" style="width: 36px; height: 36px;">
                                ${index + 1}
                            </div>
                            <div class="flex-grow-1 richtext-content">${item.text}</div>
                            <div class="text-muted d-flex align-items-center" title="Seret untuk ubah urutan">
                                <i class="ri-draggable"></i>
                            </div>
                            <div class="d-flex flex-column gap-2">
                                <button type="button" class="btn btn-sm btn-outline-secondary ordering-up-btn" ${index === 0 ? "disabled" : ""} title="Naikkan item ini">
                                    <i class="ri-arrow-up-line"></i>
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-secondary ordering-down-btn" ${index === orderingItems.length - 1 ? "disabled" : ""} title="Turunkan item ini">
                                    <i class="ri-arrow-down-line"></i>
                                </button>
                            </div>
                        </div>
                    `;
                    const upBtn = card.querySelector(".ordering-up-btn");
                    const downBtn = card.querySelector(".ordering-down-btn");
                    if (upBtn) {
                        upBtn.addEventListener("click", () => moveItem(index, index - 1));
                    }
                    if (downBtn) {
                        downBtn.addEventListener("click", () => moveItem(index, index + 1));
                    }
                    card.addEventListener("dragstart", (event) => {
                        draggedIndex = index;
                        card.classList.add("is-dragging");
                        if (event.dataTransfer) {
                            event.dataTransfer.effectAllowed = "move";
                            event.dataTransfer.setData("text/plain", String(index));
                        }
                    });
                    card.addEventListener("dragend", () => {
                        draggedIndex = null;
                        clearOrderingDropTargets();
                    });
                    card.addEventListener("dragover", (event) => {
                        event.preventDefault();
                        card.classList.add("ordering-drop-target");
                    });
                    card.addEventListener("dragleave", () => {
                        card.classList.remove("ordering-drop-target");
                    });
                    card.addEventListener("drop", (event) => {
                        event.preventDefault();
                        const sourceIndex = draggedIndex;
                        draggedIndex = null;
                        clearOrderingDropTargets();
                        if (sourceIndex === null) {
                            return;
                        }
                        moveItem(sourceIndex, index);
                    });
                    listWrap.appendChild(card);
                });
            };

            listWrap.addEventListener("dragover", (event) => {
                if (event.target === listWrap) {
                    event.preventDefault();
                    listWrap.classList.add("ordering-drop-target");
                }
            });
            listWrap.addEventListener("dragleave", (event) => {
                if (event.target === listWrap) {
                    listWrap.classList.remove("ordering-drop-target");
                }
            });
            listWrap.addEventListener("drop", (event) => {
                if (event.target !== listWrap) {
                    return;
                }
                event.preventDefault();
                const sourceIndex = draggedIndex;
                draggedIndex = null;
                clearOrderingDropTargets();
                if (sourceIndex === null) {
                    return;
                }
                moveItem(sourceIndex, orderingItems.length);
            });

            renderItems();
        }

        renderMatchingControl(question, currentNumber) {
            const helper = documentObj.createElement("div");
            helper.className = "small text-muted mb-2";
            helper.textContent = "Seret kartu jawaban ke prompt yang sesuai. Dropdown tetap tersedia sebagai fallback.";
            this.elements.questionAnswerContainer.appendChild(helper);

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
            answerBankWrap.className = "mb-3";
            answerBankWrap.innerHTML = '<div class="small fw-semibold text-muted mb-2">Bank Jawaban</div>';
            const answerBankGrid = documentObj.createElement("div");
            answerBankGrid.className = "d-grid gap-2 matching-board-bank";
            answerBankWrap.appendChild(answerBankGrid);
            this.elements.questionAnswerContainer.appendChild(answerBankWrap);

            const pairsWrap = documentObj.createElement("div");
            pairsWrap.className = "vstack gap-3";
            this.elements.questionAnswerContainer.appendChild(pairsWrap);
            let draggedChoiceId = "";

            const persistMap = () => {
                this.saveCurrentAnswer({
                    question_number: currentNumber,
                    answer_matching_json: workingMap,
                    is_marked_for_review: this.elements.markReviewCheckbox
                        ? Boolean(this.elements.markReviewCheckbox.checked)
                        : false,
                });
            };

            const clearMatchingChoiceAssignment = (choiceId) => {
                Object.keys(workingMap).forEach((promptId) => {
                    if (workingMap[promptId] === choiceId) {
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
                clearMatchingChoiceAssignment(choiceId);
                workingMap[promptId] = choiceId;
            };

            const findChoiceById = (choiceId) => {
                return answerChoices.find((choice) => choice.id === choiceId) || null;
            };

            const clearMatchingDropTargets = () => {
                answerBankGrid.classList.remove("is-active");
                Array.from(pairsWrap.querySelectorAll(".matching-dropzone")).forEach((dropzoneEl) => {
                    dropzoneEl.classList.remove("is-active");
                });
                Array.from(this.elements.questionAnswerContainer.querySelectorAll(".matching-choice-card")).forEach((cardEl) => {
                    cardEl.classList.remove("is-dragging");
                });
            };

            const buildMatchingChoiceCard = (choice, labelText, promptId) => {
                const card = documentObj.createElement("div");
                card.className = "border rounded-3 p-2 bg-light-subtle matching-choice-card";
                card.draggable = true;
                card.dataset.choiceId = choice.id;
                card.innerHTML = `
                    <div class="d-flex align-items-start justify-content-between gap-2">
                        <div class="flex-grow-1">
                            <div class="small text-muted mb-1">${this.escapeHtml(labelText)}</div>
                            <div class="richtext-content">${choice.answer_text || ""}</div>
                        </div>
                        <div class="d-flex align-items-start gap-2">
                            <span class="text-muted" title="Seret kartu jawaban">
                                <i class="ri-draggable"></i>
                            </span>
                            ${promptId ? '<button type="button" class="btn btn-sm btn-outline-danger matching-choice-remove" title="Lepaskan jawaban"><i class="ri-close-line"></i></button>' : ""}
                        </div>
                    </div>
                `;
                card.addEventListener("dragstart", (event) => {
                    draggedChoiceId = choice.id;
                    card.classList.add("is-dragging");
                    if (event.dataTransfer) {
                        event.dataTransfer.effectAllowed = "move";
                        event.dataTransfer.setData("text/plain", choice.id);
                    }
                });
                card.addEventListener("dragend", () => {
                    draggedChoiceId = "";
                    clearMatchingDropTargets();
                });
                const removeBtn = card.querySelector(".matching-choice-remove");
                if (removeBtn && promptId) {
                    removeBtn.addEventListener("click", () => {
                        delete workingMap[promptId];
                        renderMatchingBoard();
                        persistMap();
                    });
                }
                return card;
            };

            const renderMatchingBoard = () => {
                answerBankGrid.innerHTML = "";
                pairsWrap.innerHTML = "";

                const assignedChoiceIds = new Set(Object.values(workingMap));
                const availableChoices = answerChoices.filter((choice) => !assignedChoiceIds.has(choice.id));

                if (!availableChoices.length) {
                    answerBankGrid.innerHTML = '<div class="alert alert-light border mb-0 small">Semua jawaban sudah dipasangkan. Seret kembali ke bank untuk melepas.</div>';
                } else {
                    availableChoices.forEach((choice, index) => {
                        answerBankGrid.appendChild(buildMatchingChoiceCard(choice, `Pilihan ${index + 1}`, ""));
                    });
                }

                matchingPairs.forEach((pair, pairIndex) => {
                    const card = documentObj.createElement("div");
                    card.className = "border rounded-3 p-3 bg-white";

                    const currentAnswerId = workingMap[pair.id] || "";
                    const selectedChoice = findChoiceById(currentAnswerId);
                    const choiceOptionsHtml = answerChoices.map((choice, choiceIndex) => {
                        const label = this.escapeHtml(
                            this.stripRichTextToPlainText(choice.answer_text, `Pilihan ${choiceIndex + 1}`)
                        );
                        const selectedAttr = choice.id === currentAnswerId ? " selected" : "";
                        return `<option value="${choice.id}"${selectedAttr}>${label}</option>`;
                    }).join("");

                    card.innerHTML = `
                        <div class="small text-muted mb-1">Prompt ${pairIndex + 1}</div>
                        <div class="richtext-content mb-3">${pair.prompt_text || ""}</div>
                        <div class="matching-dropzone ${selectedChoice ? "is-filled" : ""}" data-pair-id="${pair.id}">
                            <div class="matching-dropzone-content" data-dropzone-content></div>
                        </div>
                        <div class="matching-dropdown-fallback mt-3">
                            <label class="form-label small text-muted">Pilih jawaban</label>
                            <select class="form-select matching-answer-select" data-pair-id="${pair.id}">
                                <option value="">Pilih pasangan jawaban...</option>
                                ${choiceOptionsHtml}
                            </select>
                        </div>
                    `;

                    const dropzone = card.querySelector(".matching-dropzone");
                    const dropzoneContent = card.querySelector("[data-dropzone-content]");
                    if (dropzoneContent) {
                        if (selectedChoice) {
                            dropzoneContent.appendChild(buildMatchingChoiceCard(selectedChoice, "Jawaban terpasang", pair.id));
                        } else {
                            dropzoneContent.innerHTML = '<div class="matching-dropzone-empty">Lepaskan kartu jawaban di sini.</div>';
                        }
                    }

                    if (dropzone) {
                        dropzone.addEventListener("dragover", (event) => {
                            event.preventDefault();
                            dropzone.classList.add("is-active");
                        });
                        dropzone.addEventListener("dragleave", () => {
                            dropzone.classList.remove("is-active");
                        });
                        dropzone.addEventListener("drop", (event) => {
                            event.preventDefault();
                            const choiceId = draggedChoiceId;
                            draggedChoiceId = "";
                            clearMatchingDropTargets();
                            if (!choiceId) {
                                return;
                            }
                            assignChoiceToPrompt(pair.id, choiceId);
                            renderMatchingBoard();
                            persistMap();
                        });
                    }

                    const selectEl = card.querySelector(".matching-answer-select");
                    if (selectEl) {
                        selectEl.addEventListener("change", (event) => {
                            const nextAnswerId = event.target.value || "";
                            assignChoiceToPrompt(pair.id, nextAnswerId);
                            renderMatchingBoard();
                            persistMap();
                        });
                    }

                    pairsWrap.appendChild(card);
                });
            };

            answerBankGrid.addEventListener("dragover", (event) => {
                event.preventDefault();
                answerBankGrid.classList.add("is-active");
            });
            answerBankGrid.addEventListener("dragleave", (event) => {
                if (event.target === answerBankGrid) {
                    answerBankGrid.classList.remove("is-active");
                }
            });
            answerBankGrid.addEventListener("drop", (event) => {
                event.preventDefault();
                const choiceId = draggedChoiceId;
                draggedChoiceId = "";
                clearMatchingDropTargets();
                if (!choiceId) {
                    return;
                }
                clearMatchingChoiceAssignment(choiceId);
                renderMatchingBoard();
                persistMap();
            });

            renderMatchingBoard();
        }

        renderFillInBlankControl(question, currentNumber) {
            const helper = documentObj.createElement("div");
            helper.className = "small text-muted mb-2";
            helper.textContent = "Isi setiap blank langsung pada teks soal. Jawaban tersimpan otomatis.";
            this.elements.questionAnswerContainer.appendChild(helper);

            const workingAnswers = Object.assign({}, (question.answer && question.answer.answer_blanks_json) || {});
            const placeholderPattern = /\{\{\s*(\d+)\s*\}\}/g;
            const questionHtml = question.question_text || "";
            const renderedHtml = questionHtml.replace(placeholderPattern, (matchValue, rawNumber) => {
                const blankNumber = String(parseInt(rawNumber, 10));
                const currentValue = Object.prototype.hasOwnProperty.call(workingAnswers, blankNumber)
                    ? workingAnswers[blankNumber]
                    : "";
                return (
                    '<span class="d-inline-flex align-items-center mx-1 my-1">' +
                    '<input type="text" class="form-control form-control-sm fill-blank-input" ' +
                    `data-blank-number="${blankNumber}" ` +
                    `value="${this.escapeHtml(currentValue)}" ` +
                    `placeholder="Blank ${blankNumber}" style="min-width: 160px; width: 12rem;">` +
                    "</span>"
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
                        is_marked_for_review: this.elements.markReviewCheckbox
                            ? Boolean(this.elements.markReviewCheckbox.checked)
                            : false,
                    });
                }, 600)
                : ((payloadValue) => {
                    this.saveCurrentAnswer({
                        question_number: currentNumber,
                        answer_blanks_json: payloadValue,
                        is_marked_for_review: this.elements.markReviewCheckbox
                            ? Boolean(this.elements.markReviewCheckbox.checked)
                            : false,
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

                if (question.question_type === "checkbox") {
                    const helper = documentObj.createElement("div");
                    helper.className = "small text-muted mb-2";
                    helper.textContent = `Pilih semua jawaban yang benar. Terpilih: ${selectedOptionIds.length}`;
                    this.elements.questionAnswerContainer.appendChild(helper);
                }

                (question.options || []).forEach((option) => {
                    const btn = documentObj.createElement("button");
                    btn.type = "button";
                    btn.className = "answer-option-item w-100 text-start";
                    const isSelected = question.question_type === "multiple_choice"
                        ? (selectedOptionId && selectedOptionId === option.id)
                        : selectedOptionIds.indexOf(option.id) >= 0;
                    if (isSelected) {
                        btn.classList.add("selected");
                    }
                    btn.innerHTML = `
                        <div class="answer-option-layout">
                            <span class="badge bg-primary answer-option-label">${option.letter}</span>
                            <div class="answer-option-content richtext-content">${this.buildOptionContentHtml(option)}</div>
                        </div>
                    `;
                    btn.addEventListener("click", () => {
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
                                is_marked_for_review: this.elements.markReviewCheckbox
                                    ? Boolean(this.elements.markReviewCheckbox.checked)
                                    : false,
                            });
                            return;
                        }
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
            const antiCheat = this.getAntiCheatConfig();
            if (this.elements.antiCheatMediaRule) {
                if (antiCheat.require_camera && antiCheat.require_microphone) {
                    this.elements.antiCheatMediaRule.textContent = "Perangkat pengawasan: Kamera dan mikrofon wajib";
                } else if (antiCheat.require_camera) {
                    this.elements.antiCheatMediaRule.textContent = "Perangkat pengawasan: Kamera wajib";
                } else if (antiCheat.require_microphone) {
                    this.elements.antiCheatMediaRule.textContent = "Perangkat pengawasan: Mikrofon wajib";
                } else {
                    this.elements.antiCheatMediaRule.textContent = "Perangkat pengawasan: Tidak wajib";
                }
            }
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
