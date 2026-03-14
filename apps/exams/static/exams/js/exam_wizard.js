(function () {
    function parseJSONScript(id, fallback) {
        const node = document.getElementById(id);
        if (!node) {
            return fallback;
        }
        try {
            return JSON.parse(node.textContent || "");
        } catch (err) {
            return fallback;
        }
    }

    function normalizeArrayPayload(value) {
        if (Array.isArray(value)) {
            return value;
        }
        if (!value) {
            return [];
        }
        if (typeof value === "string") {
            try {
                const parsed = JSON.parse(value);
                return Array.isArray(parsed) ? parsed : [];
            } catch (err) {
                return [];
            }
        }
        return [];
    }

    function boolFromOverride(value) {
        if (value === true || value === false) {
            return value;
        }
        if (value === "true") {
            return true;
        }
        if (value === "false") {
            return false;
        }
        return null;
    }

    function hasNavigationOverride(model) {
        if (!model) {
            return false;
        }
        return model.allow_previous_override !== null
            || model.allow_next_override !== null
            || model.force_sequential_override !== null;
    }

    document.addEventListener("DOMContentLoaded", function () {
        const form = document.getElementById("examWizardForm");
        if (!form) {
            return;
        }

        const questionPickerConfig = parseJSONScript("question-picker-config", {});
        const assignmentData = parseJSONScript("available-assignment-data", { classes: [], students: [] });
        let initialSelected = normalizeArrayPayload(parseJSONScript("initial-selected-questions", []));
        const initialAssignments = normalizeArrayPayload(parseJSONScript("initial-assignment-payload", []));

        const selectedPayloadInput = document.getElementById("id_selected_questions_payload");
        const assignmentPayloadInput = document.getElementById("id_assignment_payload");
        const statusActionInput = document.getElementById("id_status_action");

        const selectedListEl = document.getElementById("selectedQuestionList");
        const selectedCountEl = document.getElementById("selectedQuestionCount");
        const selectedPointsEl = document.getElementById("selectedQuestionTotalPoints");
        const selectedCountTopEl = document.getElementById("selectedQuestionCountTop");
        const selectedPointsTopEl = document.getElementById("selectedQuestionTotalPointsTop");
        const selectedCountModalEl = document.getElementById("selectedQuestionCountModal");
        const selectedPointsModalEl = document.getElementById("selectedQuestionTotalPointsModal");
        const availableListEl = document.getElementById("availableQuestionList");
        const availableLoadMoreBtn = document.getElementById("availableQuestionLoadMoreBtn");
        const availableModalEl = document.getElementById("availableQuestionModal");
        const assignmentSummaryEl = document.getElementById("assignmentSummaryList");
        const reviewSummaryEl = document.getElementById("reviewSummary");
        const studentAssignmentListEl = document.getElementById("studentAssignmentList");
        const studentAssignmentToggleBtn = document.getElementById("studentAssignmentToggleSelectBtn");
        const studentAssignmentToggleLabel = studentAssignmentToggleBtn ? studentAssignmentToggleBtn.querySelector(".student-toggle-select-label") : null;

        const addCategoryBtn = document.getElementById("addCategoryQuestionsBtn");
        const categorySelector = document.getElementById("bulkCategorySelector");
        const filterSearchInput = document.getElementById("questionFilterSearch");
        const filterSubjectSelect = document.getElementById("questionFilterSubject");
        const filterTypeSelect = document.getElementById("questionFilterType");
        const filterCategorySelect = document.getElementById("questionFilterCategory");
        const filterResetBtn = document.getElementById("questionFilterResetBtn");

        const availableToggleSelectBtn = document.getElementById("availableToggleSelectBtn");
        const selectedToggleSelectBtn = document.getElementById("selectedToggleSelectBtn");
        const bulkPointsInput = document.getElementById("bulkPointsOverride");
        const bulkAllowPrevSelect = document.getElementById("bulkAllowPrevious");
        const bulkAllowNextSelect = document.getElementById("bulkAllowNext");
        const bulkForceSeqSelect = document.getElementById("bulkForceSequential");
        const applyBulkSelectedBtn = document.getElementById("applyBulkSelectedBtn");
        const deleteBulkSelectedBtn = document.getElementById("deleteBulkSelectedBtn");
        const availableToggleSelectLabel = availableToggleSelectBtn ? availableToggleSelectBtn.querySelector(".available-toggle-select-label") : null;
        const selectedToggleSelectLabel = selectedToggleSelectBtn ? selectedToggleSelectBtn.querySelector(".selected-toggle-select-label") : null;

        const stepIndicators = Array.from(document.querySelectorAll("[data-step-indicator]"));
        const stepCards = Array.from(document.querySelectorAll("[data-step]"));
        const prevBtn = document.getElementById("wizardPrevBtn");
        const nextBtn = document.getElementById("wizardNextBtn");
        const submitButtons = Array.from(document.querySelectorAll(".wizard-submit-btn"));
        let currentStep = 1;
        const allowRetakeField = document.getElementById("id_allow_retake");
        const retakeSettingsFields = document.getElementById("retakeSettingsFields");
        const maxRetakeAttemptsField = document.getElementById("id_max_retake_attempts");
        const retakeCooldownField = document.getElementById("id_retake_cooldown_minutes");
        const retakeShowReviewField = document.getElementById("id_retake_show_review");
        const certificateEnabledField = document.getElementById("id_certificate_enabled");
        const certificateSettingsFields = document.getElementById("certificateSettingsFields");
        const certificateTemplateField = document.getElementById("id_certificate_template");

        if (!initialSelected.length && selectedPayloadInput && selectedPayloadInput.value) {
            initialSelected = normalizeArrayPayload(selectedPayloadInput.value);
        }

        const questionSearchUrl = questionPickerConfig.search_url || "";
        let questionPageSize = parseInt(questionPickerConfig.page_size || 50, 10);
        if (isNaN(questionPageSize) || questionPageSize < 10) {
            questionPageSize = 50;
        }
        const availableState = {
            page: 1,
            hasNext: false,
            totalItems: 0,
            isLoading: false
        };
        let filterDebounceTimer = null;

        const availableById = {};
        const selectedQuestions = {};

        function normalizeQuestionFromAvailable(item) {
            return {
                question_id: item.id,
                question_text: item.text,
                subject_name: item.subject_name || "",
                category_name: item.category_name || "Tanpa kategori",
                question_type: item.question_type || "",
                default_points: parseFloat(item.points || 0) || 0,
                display_order: 1,
                points_override: "",
                override_navigation: false,
                allow_previous_override: null,
                allow_next_override: null,
                force_sequential_override: null,
                default_allow_previous: !!item.allow_previous,
                default_allow_next: !!item.allow_next,
                default_force_sequential: !!item.force_sequential
            };
        }

        function loadInitialSelected() {
            initialSelected.forEach(function (item, index) {
                const questionId = item.question_id || item.id;
                if (!questionId) {
                    return;
                }
                const fromAvailable = availableById[questionId];
                const base = fromAvailable ? normalizeQuestionFromAvailable(fromAvailable) : {
                    question_id: questionId,
                    question_text: item.question_text || item.text || "Soal tidak ditemukan",
                    subject_name: item.subject_name || "",
                    category_name: item.category_name || "Tanpa kategori",
                    question_type: item.question_type || "",
                    default_points: parseFloat(item.default_points || item.points || 0) || 0,
                    display_order: index + 1,
                    points_override: "",
                    override_navigation: false,
                    allow_previous_override: null,
                    allow_next_override: null,
                    force_sequential_override: null,
                    default_allow_previous: item.default_allow_previous !== false,
                    default_allow_next: item.default_allow_next !== false,
                    default_force_sequential: !!item.default_force_sequential
                };

                base.display_order = parseInt(item.display_order || index + 1, 10);
                base.points_override = item.points_override !== null && item.points_override !== undefined ? String(item.points_override) : "";
                base.allow_previous_override = boolFromOverride(item.allow_previous_override);
                base.allow_next_override = boolFromOverride(item.allow_next_override);
                base.force_sequential_override = boolFromOverride(item.force_sequential_override);
                base.override_navigation = hasNavigationOverride(base);

                selectedQuestions[questionId] = base;
            });
        }

        function normalizeFilterText(value) {
            return String(value || "").toLowerCase().trim();
        }

        function hideModal(modalEl) {
            if (!modalEl || !window.bootstrap || !window.bootstrap.Modal) {
                return;
            }
            let modalInstance = window.bootstrap.Modal.getInstance(modalEl);
            if (!modalInstance) {
                modalInstance = new window.bootstrap.Modal(modalEl);
            }
            modalInstance.hide();
        }

        function escapeHTML(value) {
            return String(value || "")
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/\"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        function buildSafeDomId(prefix, value) {
            return prefix + String(value || "").replace(/[^A-Za-z0-9_-]/g, "-");
        }

        function questionTypeLabel(value) {
            const labels = {
                multiple_choice: "Pilihan Ganda",
                checkbox: "Checkbox",
                ordering: "Ordering",
                matching: "Matching",
                fill_in_blank: "Fill In Blank",
                essay: "Esai",
                short_answer: "Jawaban Singkat"
            };
            return labels[value] || value || "-";
        }

        function questionTypeBadgeClass(value) {
            const classes = {
                multiple_choice: "badge-soft-primary",
                checkbox: "badge-soft-success",
                ordering: "badge-soft-warning",
                matching: "badge-soft-warning",
                fill_in_blank: "badge-soft-secondary",
                essay: "badge-soft-info",
                short_answer: "badge-soft-primary"
            };
            return classes[value] || "badge-soft-secondary";
        }

        function formatPointsValue(value) {
            let parsed = parseFloat(value);
            if (isNaN(parsed)) {
                parsed = 0;
            }
            return parsed.toFixed(2);
        }

        function buildQuestionMetaBadges(subjectName, categoryName, pointsValue, questionType) {
            const badges = [];

            if (subjectName) {
                badges.push(`<span class="badge-soft-info text-nowrap">${escapeHTML(subjectName)}</span>`);
            }

            if (categoryName) {
                badges.push(`<span class="badge-soft-secondary text-nowrap">${escapeHTML(categoryName)}</span>`);
            }

            badges.push(`<span class="badge-soft-warning text-nowrap">${escapeHTML(formatPointsValue(pointsValue))} poin</span>`);
            badges.push(
                `<span class="${questionTypeBadgeClass(questionType)} text-nowrap">${escapeHTML(questionTypeLabel(questionType))}</span>`
            );

            return badges.join("");
        }

        function buildQuestionQueryParams(page, extraFilters) {
            const params = new URLSearchParams();
            params.set("page", String(page || 1));
            params.set("page_size", String(questionPageSize));

            const keyword = normalizeFilterText(filterSearchInput && filterSearchInput.value);
            const subject = String((filterSubjectSelect && filterSubjectSelect.value) || "").trim();
            const questionType = String((filterTypeSelect && filterTypeSelect.value) || "").trim();
            const category = String((filterCategorySelect && filterCategorySelect.value) || "").trim();

            if (keyword) {
                params.set("q", keyword);
            }
            if (subject) {
                params.set("subject", subject);
            }
            if (questionType) {
                params.set("question_type", questionType);
            }
            if (category) {
                params.set("category", category);
            }

            if (extraFilters) {
                Object.keys(extraFilters).forEach(function (key) {
                    const val = extraFilters[key];
                    if (val === null || val === undefined || val === "") {
                        return;
                    }
                    params.set(key, String(val));
                });
            }
            return params;
        }

        function renderAvailableQuestionItems(items, appendMode) {
            if (!availableListEl) {
                return;
            }
            if (!appendMode) {
                availableListEl.innerHTML = "";
            }
            if (!items.length && !appendMode) {
                availableListEl.innerHTML = '<div class="list-group-item text-muted">Tidak ada soal ditemukan.</div>';
                syncAvailableToggleState();
                return;
            }

            const rowsHTML = items.map(function (item) {
                const safeText = escapeHTML(item.text || "");
                const checkboxId = buildSafeDomId("available-question-", item.id);
                const titleId = buildSafeDomId("available-question-title-", item.id);
                const metaBadges = buildQuestionMetaBadges(
                    item.subject_name || "",
                    item.category_name || "Tanpa kategori",
                    item.points || 0,
                    item.question_type || ""
                );
                return `<div class="list-group-item list-group-item-action question-picker-item" data-question-id="${item.id}" data-category-id="${escapeHTML(item.category_id || "")}"><div class="d-flex align-items-center gap-3"><div class="question-picker-check d-flex align-items-center flex-shrink-0"><input type="checkbox" class="form-check-input question-picker-checkbox m-0" id="${checkboxId}" value="${item.id}" title="Pilih soal" aria-label="Pilih soal: ${safeText}" aria-labelledby="${titleId}"></div><div class="flex-grow-1 min-w-0"><p class="question-picker-title mb-2 fw-semibold" id="${titleId}">${safeText}</p><div class="d-flex flex-wrap gap-2 mb-0">${metaBadges}</div></div></div></div>`;
            }).join("");

            if (appendMode) {
                availableListEl.insertAdjacentHTML("beforeend", rowsHTML);
            } else {
                availableListEl.innerHTML = rowsHTML;
            }
            syncAvailableCheckboxState();
        }

        function updateAvailablePaginationUI() {
            if (availableLoadMoreBtn) {
                availableLoadMoreBtn.classList.toggle("d-none", !availableState.hasNext);
                availableLoadMoreBtn.disabled = !!availableState.isLoading;
                availableLoadMoreBtn.innerHTML = availableState.isLoading ? "Memuat..." : "Muat lebih banyak";
            }
        }

        function fetchAvailableQuestions(options) {
            if (!questionSearchUrl || !availableListEl) {
                return;
            }
            options = options || {};
            const appendMode = !!options.append;
            if (availableState.isLoading) {
                return;
            }
            if (appendMode && !availableState.hasNext) {
                return;
            }

            const page = appendMode ? (availableState.page + 1) : 1;
            const params = buildQuestionQueryParams(page, options.extraFilters || null);
            availableState.isLoading = true;
            updateAvailablePaginationUI();

            if (!appendMode) {
                availableListEl.innerHTML = '<div class="list-group-item text-muted small">Memuat daftar soal...</div>';
            }

            fetch(`${questionSearchUrl}?${params.toString()}`, {
                method: "GET",
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("Gagal memuat bank soal.");
                    }
                    return response.json();
                })
                .then(function (payload) {
                    const items = Array.isArray(payload.items) ? payload.items : [];
                    items.forEach(function (item) {
                        availableById[item.id] = item;
                    });
                    renderAvailableQuestionItems(items, appendMode);
                    const pagination = payload.pagination || {};
                    availableState.page = pagination.page || page;
                    availableState.hasNext = !!pagination.has_next;
                    availableState.totalItems = parseInt(pagination.total_items || 0, 10) || 0;
                })
                .catch(function () {
                    if (!appendMode && availableListEl) {
                        availableListEl.innerHTML = '<div class="list-group-item text-danger">Gagal memuat soal. Coba lagi.</div>';
                        syncAvailableToggleState();
                    }
                })
                .finally(function () {
                    availableState.isLoading = false;
                    updateAvailablePaginationUI();
                });
        }

        function applyQuestionFilters() {
            if (filterDebounceTimer) {
                window.clearTimeout(filterDebounceTimer);
            }
            filterDebounceTimer = window.setTimeout(function () {
                fetchAvailableQuestions({ append: false });
            }, 250);
        }

        function syncAvailableToggleState() {
            if (!availableToggleSelectLabel || !availableListEl) {
                return;
            }
            const checkboxes = Array.from(availableListEl.querySelectorAll(".question-picker-checkbox"));
            const allChecked = !!checkboxes.length && checkboxes.every(function (checkbox) { return checkbox.checked; });
            availableToggleSelectLabel.textContent = allChecked ? "Batal Pilih" : "Pilih Semua";
        }

        function syncAvailableCheckboxState() {
            if (!availableListEl) {
                return;
            }
            availableListEl.querySelectorAll(".question-picker-checkbox").forEach(function (checkbox) {
                checkbox.checked = !!selectedQuestions[checkbox.value];
                const item = checkbox.closest(".question-picker-item");
                if (item) {
                    item.classList.toggle("list-group-item-primary", checkbox.checked);
                }
            });
            syncAvailableToggleState();
        }

        function serializeSelectedQuestions() {
            const idsInOrder = Array.from(selectedListEl.querySelectorAll(".selected-question-item"))
                .map(function (el) { return el.getAttribute("data-question-id"); })
                .filter(Boolean);

            const payload = idsInOrder.map(function (questionId, index) {
                const item = selectedQuestions[questionId];
                if (!item) {
                    return null;
                }
                item.display_order = index + 1;
                const overrideNavigation = hasNavigationOverride(item);
                item.override_navigation = overrideNavigation;
                return {
                    question_id: item.question_id,
                    display_order: item.display_order,
                    points_override: item.points_override === "" ? "" : Number(item.points_override),
                    override_navigation: overrideNavigation,
                    allow_previous_override: item.allow_previous_override,
                    allow_next_override: item.allow_next_override,
                    force_sequential_override: item.force_sequential_override
                };
            }).filter(Boolean);

            selectedPayloadInput.value = JSON.stringify(payload);
            return payload;
        }

        function renderSelectedQuestions() {
            const items = Object.values(selectedQuestions).sort(function (a, b) {
                return a.display_order - b.display_order;
            });

            if (!items.length) {
                selectedListEl.innerHTML = '<div class="list-group-item text-muted small">Belum ada soal dipilih.</div>';
                selectedCountEl.textContent = "0";
                selectedPointsEl.textContent = "0";
                if (selectedCountTopEl) {
                    selectedCountTopEl.textContent = "0";
                }
                if (selectedPointsTopEl) {
                    selectedPointsTopEl.textContent = "0";
                }
                if (selectedCountModalEl) {
                    selectedCountModalEl.textContent = "0";
                }
                if (selectedPointsModalEl) {
                    selectedPointsModalEl.textContent = "0.00";
                }
                selectedPayloadInput.value = "[]";
                syncSelectedBulkCheckAllState();
                return;
            }

            selectedListEl.innerHTML = items.map(function (item) {
                function selectValue(val) {
                    if (val === true) {
                        return "true";
                    }
                    if (val === false) {
                        return "false";
                    }
                    return "inherit";
                }
                const safeQuestionText = escapeHTML(item.question_text || "");
                const safeDefaultPoints = escapeHTML(formatPointsValue(item.default_points || 0));
                const safePointsOverride = escapeHTML(item.points_override || "");
                const bulkCheckId = buildSafeDomId("selected-question-bulk-", item.question_id);
                const titleId = buildSafeDomId("selected-question-title-", item.question_id);
                const effectivePoints = item.points_override !== "" ? item.points_override : item.default_points;
                const metaBadges = buildQuestionMetaBadges(
                    item.subject_name || "",
                    item.category_name || "Tanpa kategori",
                    effectivePoints,
                    item.question_type || ""
                );
                return `<div class="selected-question-item list-group-item" data-question-id="${item.question_id}"><div class="d-flex align-items-center gap-3"><div class="question-picker-check d-flex align-items-center flex-shrink-0"><input type="checkbox" class="form-check-input selected-question-bulk-check m-0" id="${bulkCheckId}" title="Pilih untuk bulk action" aria-labelledby="${titleId}"></div><div class="flex-grow-1 min-w-0"><p class="question-picker-title mb-2 fw-semibold" id="${titleId}">${safeQuestionText}</p><div class="d-flex flex-wrap gap-2 mb-0">${metaBadges}</div><div class="row g-2 mt-1 question-picker-controls"><div class="col-12 col-md-4 col-xl-2"><input type="number" min="0.01" step="0.01" class="form-control form-control-sm selected-question-points" value="${safePointsOverride}" placeholder="Poin (${safeDefaultPoints})" aria-label="Timpa poin untuk soal ini"></div><div class="col-12 col-md-4 col-xl-2"><select class="form-select form-select-sm selected-question-allow-prev" aria-label="Override navigasi sebelumnya"><option value="inherit" ${selectValue(item.allow_previous_override) === "inherit" ? "selected" : ""}>Prev: Ikuti</option><option value="true" ${selectValue(item.allow_previous_override) === "true" ? "selected" : ""}>Prev: Ya</option><option value="false" ${selectValue(item.allow_previous_override) === "false" ? "selected" : ""}>Prev: Tidak</option></select></div><div class="col-12 col-md-4 col-xl-2"><select class="form-select form-select-sm selected-question-allow-next" aria-label="Override navigasi berikutnya"><option value="inherit" ${selectValue(item.allow_next_override) === "inherit" ? "selected" : ""}>Next: Ikuti</option><option value="true" ${selectValue(item.allow_next_override) === "true" ? "selected" : ""}>Next: Ya</option><option value="false" ${selectValue(item.allow_next_override) === "false" ? "selected" : ""}>Next: Tidak</option></select></div><div class="col-12 col-md-4 col-xl-3"><select class="form-select form-select-sm selected-question-force-seq" aria-label="Override aturan berurutan"><option value="inherit" ${selectValue(item.force_sequential_override) === "inherit" ? "selected" : ""}>Berurutan: Ikuti</option><option value="true" ${selectValue(item.force_sequential_override) === "true" ? "selected" : ""}>Berurutan: Ya</option><option value="false" ${selectValue(item.force_sequential_override) === "false" ? "selected" : ""}>Berurutan: Tidak</option></select></div></div></div><div class="d-flex align-items-center gap-2 flex-shrink-0 ms-auto"><button type="button" class="icon-only-btn drag-handle" title="Geser untuk ubah urutan" aria-label="Geser untuk ubah urutan: ${safeQuestionText}"><i class="ri-draggable fs-5"></i></button><button type="button" class="icon-only-btn is-danger remove-selected-question-btn" title="Hapus soal dari pilihan" aria-label="Hapus soal dari pilihan: ${safeQuestionText}"><i class="ri-delete-bin-line"></i></button></div></div></div>`;
            }).join("");

            let totalPoints = 0;
            items.forEach(function (item) {
                const points = item.points_override !== "" ? parseFloat(item.points_override) : parseFloat(item.default_points || 0);
                totalPoints += isNaN(points) ? 0 : points;
            });
            selectedCountEl.textContent = String(items.length);
            selectedPointsEl.textContent = totalPoints.toFixed(2);
            if (selectedCountTopEl) {
                selectedCountTopEl.textContent = String(items.length);
            }
            if (selectedPointsTopEl) {
                selectedPointsTopEl.textContent = totalPoints.toFixed(2);
            }
            if (selectedCountModalEl) {
                selectedCountModalEl.textContent = String(items.length);
            }
            if (selectedPointsModalEl) {
                selectedPointsModalEl.textContent = totalPoints.toFixed(2);
            }
            serializeSelectedQuestions();
            bindSelectedQuestionEvents();
        }

        function syncSelectedBulkCheckAllState() {
            if (!selectedToggleSelectLabel) {
                return;
            }
            const bulkChecks = Array.from(selectedListEl.querySelectorAll(".selected-question-bulk-check"));
            bulkChecks.forEach(function (checkbox) {
                const item = checkbox.closest(".selected-question-item");
                if (item) {
                    item.classList.toggle("list-group-item-primary", checkbox.checked);
                }
            });
            const allChecked = !!bulkChecks.length && bulkChecks.every(function (checkbox) { return checkbox.checked; });
            selectedToggleSelectLabel.textContent = allChecked ? "Batal Pilih" : "Pilih Semua";
        }

        function getSelectedBulkQuestionIds() {
            return Array.from(selectedListEl.querySelectorAll(".selected-question-item"))
                .filter(function (item) {
                    const bulkCheck = item.querySelector(".selected-question-bulk-check");
                    return bulkCheck && bulkCheck.checked;
                })
                .map(function (item) { return item.getAttribute("data-question-id"); })
                .filter(Boolean);
        }

        function bindSelectedQuestionEvents() {
            selectedListEl.querySelectorAll(".selected-question-item").forEach(function (card) {
                const questionId = card.getAttribute("data-question-id");
                const model = selectedQuestions[questionId];
                if (!model) {
                    return;
                }
                const allowPrevSelect = card.querySelector(".selected-question-allow-prev");
                const allowNextSelect = card.querySelector(".selected-question-allow-next");
                const forceSeqSelect = card.querySelector(".selected-question-force-seq");
                model.override_navigation = hasNavigationOverride(model);

                card.querySelector(".remove-selected-question-btn").addEventListener("click", function () {
                    delete selectedQuestions[questionId];
                    syncAvailableCheckboxState();
                    renderSelectedQuestions();
                    renderReviewSummary();
                });

                const bulkCheck = card.querySelector(".selected-question-bulk-check");
                if (bulkCheck) {
                    bulkCheck.addEventListener("change", syncSelectedBulkCheckAllState);
                }

                card.querySelector(".selected-question-points").addEventListener("input", function (event) {
                    model.points_override = event.target.value.trim();
                    serializeSelectedQuestions();
                    renderReviewSummary();
                });

                allowPrevSelect.addEventListener("change", function (event) {
                    model.allow_previous_override = boolFromOverride(event.target.value);
                    model.override_navigation = hasNavigationOverride(model);
                    serializeSelectedQuestions();
                });

                allowNextSelect.addEventListener("change", function (event) {
                    model.allow_next_override = boolFromOverride(event.target.value);
                    model.override_navigation = hasNavigationOverride(model);
                    serializeSelectedQuestions();
                });

                forceSeqSelect.addEventListener("change", function (event) {
                    model.force_sequential_override = boolFromOverride(event.target.value);
                    model.override_navigation = hasNavigationOverride(model);
                    serializeSelectedQuestions();
                });
            });
            syncSelectedBulkCheckAllState();
        }

        function getCheckedAssignments() {
            return Array.from(document.querySelectorAll(".assignment-checkbox"))
                .filter(function (checkbox) { return checkbox.checked; })
                .map(function (checkbox) {
                    return {
                        type: checkbox.getAttribute("data-type"),
                        id: checkbox.value
                    };
                });
        }

        function syncAssignmentPayload() {
            const payload = getCheckedAssignments();
            assignmentPayloadInput.value = JSON.stringify(payload);
            renderAssignmentSummary(payload);
            syncStudentAssignmentToggleState();
            return payload;
        }

        function renderAssignmentSummary(payload) {
            if (!payload.length) {
                assignmentSummaryEl.innerHTML = '<li class="text-muted">Belum ada penugasan dipilih.</li>';
                return;
            }
            const classMap = {};
            assignmentData.classes.forEach(function (c) { classMap[c.id] = c.name; });
            const studentMap = {};
            assignmentData.students.forEach(function (s) { studentMap[s.id] = `${s.name} (${s.username})`; });

            assignmentSummaryEl.innerHTML = payload.map(function (item) {
                const label = item.type === "class" ? (classMap[item.id] || item.id) : (studentMap[item.id] || item.id);
                return `<li>${item.type === "class" ? "Kelas: " : "Siswa: "}${label}</li>`;
            }).join("");
        }

        function getStudentAssignmentCheckboxes() {
            if (!studentAssignmentListEl) {
                return [];
            }
            return Array.from(studentAssignmentListEl.querySelectorAll('.assignment-checkbox[data-type="student"]'));
        }

        function syncStudentAssignmentToggleState() {
            if (!studentAssignmentToggleBtn || !studentAssignmentToggleLabel) {
                return;
            }
            const checkboxes = getStudentAssignmentCheckboxes();
            const hasStudents = checkboxes.length > 0;
            const allChecked = hasStudents && checkboxes.every(function (checkbox) { return checkbox.checked; });
            studentAssignmentToggleBtn.disabled = !hasStudents;
            studentAssignmentToggleLabel.textContent = allChecked ? "Batal Pilih" : "Pilih Semua";
        }

        function setStep(stepNumber) {
            currentStep = Math.max(1, Math.min(7, stepNumber));
            stepCards.forEach(function (card) {
                const step = parseInt(card.getAttribute("data-step"), 10);
                const isActive = step === currentStep;
                card.classList.toggle("d-none", !isActive);
                card.toggleAttribute("hidden", !isActive);
                card.setAttribute("aria-hidden", isActive ? "false" : "true");
            });
            stepIndicators.forEach(function (indicator) {
                const step = parseInt(indicator.getAttribute("data-step-indicator"), 10);
                const isActive = step === currentStep;
                indicator.classList.toggle("active", isActive);
                indicator.setAttribute("aria-selected", isActive ? "true" : "false");
                indicator.setAttribute("tabindex", isActive ? "0" : "-1");
                if (isActive) {
                    indicator.setAttribute("aria-current", "step");
                } else {
                    indicator.removeAttribute("aria-current");
                }
            });
            prevBtn.disabled = currentStep === 1;
            nextBtn.classList.toggle("d-none", currentStep === 7);
            submitButtons.forEach(function (btn) {
                btn.classList.toggle("d-none", currentStep !== 7);
            });
            if (currentStep === 7) {
                renderReviewSummary();
            }
        }

        function canMoveToStep(targetStep) {
            const desiredStep = Math.max(1, Math.min(7, targetStep));
            if (desiredStep <= currentStep) {
                return true;
            }

            for (let step = currentStep; step < desiredStep; step += 1) {
                if (step === 3 && Object.keys(selectedQuestions).length === 0) {
                    window.alert("Pilih minimal satu soal sebelum lanjut.");
                    return false;
                }
                if (step === 4 && allowRetakeField && allowRetakeField.checked) {
                    const attemptsValue = parseInt((maxRetakeAttemptsField && maxRetakeAttemptsField.value) || "0", 10);
                    if (isNaN(attemptsValue) || attemptsValue < 2 || attemptsValue > 10) {
                        window.alert("Maksimal percobaan retake harus berada di rentang 2 sampai 10.");
                        return false;
                    }
                }
                if (step === 6 && getCheckedAssignments().length === 0) {
                    window.alert("Pilih minimal satu penugasan kelas atau siswa sebelum lanjut.");
                    return false;
                }
            }

            return true;
        }

        function findInitialStepFromErrors() {
            const stepWithError = stepCards.find(function (card) {
                return !!card.querySelector(".text-danger, .alert-danger");
            });
            if (!stepWithError) {
                return 1;
            }
            const parsed = parseInt(stepWithError.getAttribute("data-step"), 10);
            return isNaN(parsed) ? 1 : parsed;
        }

        function renderReviewSummary() {
            if (!reviewSummaryEl) {
                return;
            }
            const selectedCount = Object.keys(selectedQuestions).length;
            const assignments = getCheckedAssignments();
            const title = (document.getElementById("id_title") || {}).value || "-";
            let subjectText = (document.getElementById("id_subject") || {}).selectedOptions;
            subjectText = subjectText && subjectText.length ? subjectText[0].textContent : "-";
            const startTime = (document.getElementById("id_start_time") || {}).value || "-";
            const endTime = (document.getElementById("id_end_time") || {}).value || "-";
            const passingScore = (document.getElementById("id_passing_score") || {}).value || "-";
            const randomizeQ = (document.getElementById("id_randomize_questions") || {}).checked ? "Ya" : "Tidak";
            const randomizeOpt = (document.getElementById("id_randomize_options") || {}).checked ? "Ya" : "Tidak";
            const overrideGlobal = (document.getElementById("id_override_question_navigation") || {}).checked ? "Ya" : "Tidak";
            const certificateEnabled = !!(certificateEnabledField && certificateEnabledField.checked);
            let certificateTemplateText = "-";
            if (certificateTemplateField && certificateTemplateField.selectedOptions && certificateTemplateField.selectedOptions.length) {
                certificateTemplateText = certificateTemplateField.selectedOptions[0].textContent || "-";
            }
            const allowRetake = !!(allowRetakeField && allowRetakeField.checked);
            const retakePolicy = (document.querySelector('input[name="retake_score_policy"]:checked') || {}).value || "highest";
            const retakePolicyLabelMap = {
                highest: "Nilai Tertinggi",
                latest: "Nilai Terbaru",
                average: "Nilai Rata-rata"
            };
            let retakeSummary = "Nonaktif";
            if (allowRetake) {
                const maxAttemptsValue = (maxRetakeAttemptsField && maxRetakeAttemptsField.value) || "2";
                const cooldownValue = (retakeCooldownField && retakeCooldownField.value) || "0";
                const reviewBeforeRetake = (retakeShowReviewField && retakeShowReviewField.checked) ? "Ya" : "Tidak";
                retakeSummary =
                    `Aktif | Maks. ${maxAttemptsValue} percobaan | Nilai: ${retakePolicyLabelMap[retakePolicy] || "Nilai Tertinggi"} | Jeda: ${cooldownValue} menit | Review sebelum retake: ${reviewBeforeRetake}`;
            }

            reviewSummaryEl.innerHTML = [
                ["Judul Ujian", title],
                ["Mata Pelajaran", subjectText],
                ["Waktu Mulai", startTime],
                ["Waktu Selesai", endTime],
                ["Jumlah Soal Dipilih", String(selectedCount)],
                ["Jumlah Penugasan", String(assignments.length)],
                ["Nilai Kelulusan", `${passingScore}%`],
                ["Acak Soal", randomizeQ],
                ["Acak Opsi", randomizeOpt],
                ["Timpa Navigasi Global", overrideGlobal],
                ["Sertifikat", certificateEnabled ? (`Aktif | ${certificateTemplateText}`) : "Nonaktif"],
                ["Retake", retakeSummary]
            ].map(function (row) {
                return `<div class="list-group-item d-flex justify-content-between gap-2"><span>${row[0]}</span><strong class="text-end">${row[1]}</strong></div>`;
            }).join("");
        }

        function toggleRetakeSettings() {
            if (!retakeSettingsFields || !allowRetakeField) {
                return;
            }
            const enabled = !!allowRetakeField.checked;
            retakeSettingsFields.classList.toggle("d-none", !enabled);
            retakeSettingsFields.toggleAttribute("hidden", !enabled);
            if (!enabled && maxRetakeAttemptsField && maxRetakeAttemptsField.value === "") {
                maxRetakeAttemptsField.value = "1";
            }
            if (enabled && maxRetakeAttemptsField && parseInt(maxRetakeAttemptsField.value || "0", 10) < 2) {
                maxRetakeAttemptsField.value = "2";
            }
            if (enabled && retakeCooldownField && retakeCooldownField.value === "") {
                retakeCooldownField.value = "0";
            }
        }

        function toggleCertificateSettings() {
            if (!certificateSettingsFields || !certificateEnabledField) {
                return;
            }
            const enabled = !!certificateEnabledField.checked;
            certificateSettingsFields.classList.toggle("d-none", !enabled);
            certificateSettingsFields.toggleAttribute("hidden", !enabled);
            if (!enabled && certificateTemplateField) {
                certificateTemplateField.value = "";
            }
        }

        function addQuestionToSelection(questionId) {
            if (!selectedQuestions[questionId] && availableById[questionId]) {
                const item = normalizeQuestionFromAvailable(availableById[questionId]);
                item.display_order = Object.keys(selectedQuestions).length + 1;
                selectedQuestions[questionId] = item;
            }
        }

        function removeQuestionFromSelection(questionId) {
            delete selectedQuestions[questionId];
        }

        function fetchAllByCategoryAndSelect(categoryId) {
            if (!questionSearchUrl || !categoryId) {
                return;
            }
            let page = 1;
            let hasNext = true;
            let addedCount = 0;
            let hasFailed = false;

            function finishCategoryLoad() {
                if (addCategoryBtn) {
                    addCategoryBtn.disabled = false;
                    addCategoryBtn.innerHTML = '<i class="ri-add-line me-1"></i>Tambah Kategori';
                }
                if (hasFailed) {
                    window.alert("Gagal menambahkan soal dari kategori terpilih.");
                }
                renderSelectedQuestions();
                syncAvailableCheckboxState();
                renderReviewSummary();
                if (addedCount > 0) {
                    fetchAvailableQuestions({ append: false });
                }
            }

            function loadNextPage() {
                if (!hasNext) {
                    finishCategoryLoad();
                    return;
                }
                const params = new URLSearchParams();
                params.set("page", String(page));
                params.set("page_size", String(Math.max(questionPageSize, 100)));
                params.set("category", categoryId);

                fetch(`${questionSearchUrl}?${params.toString()}`, {
                    method: "GET",
                    headers: { "X-Requested-With": "XMLHttpRequest" }
                })
                    .then(function (response) {
                        if (!response.ok) {
                            throw new Error("Gagal memuat soal kategori.");
                        }
                        return response.json();
                    })
                    .then(function (payload) {
                        const items = Array.isArray(payload.items) ? payload.items : [];
                        items.forEach(function (item) {
                            availableById[item.id] = item;
                            if (!selectedQuestions[item.id]) {
                                addQuestionToSelection(item.id);
                                addedCount += 1;
                            }
                        });
                        const pagination = payload.pagination || {};
                        hasNext = !!pagination.has_next;
                        page += 1;
                        loadNextPage();
                    })
                    .catch(function () {
                        hasFailed = true;
                        hasNext = false;
                        finishCategoryLoad();
                    });
            }

            if (addCategoryBtn) {
                addCategoryBtn.disabled = true;
                addCategoryBtn.textContent = "Memuat...";
            }

            loadNextPage();
        }

        if (availableListEl) {
            availableListEl.addEventListener("change", function (event) {
                const checkbox = event.target;
                if (!checkbox || !checkbox.classList.contains("question-picker-checkbox")) {
                    return;
                }
                const questionId = checkbox.value;
                if (checkbox.checked) {
                    addQuestionToSelection(questionId);
                } else {
                    removeQuestionFromSelection(questionId);
                }
                renderSelectedQuestions();
                renderReviewSummary();
                syncAvailableToggleState();
            });
        }

        if (availableToggleSelectBtn) {
            availableToggleSelectBtn.addEventListener("click", function () {
                if (!availableListEl) {
                    return;
                }
                const checkboxes = Array.from(availableListEl.querySelectorAll(".question-picker-checkbox"));
                if (!checkboxes.length) {
                    return;
                }
                const shouldSelectAll = checkboxes.some(function (checkbox) { return !checkbox.checked; });
                checkboxes.forEach(function (checkbox) {
                    checkbox.checked = shouldSelectAll;
                    if (shouldSelectAll) {
                        addQuestionToSelection(checkbox.value);
                    } else {
                        removeQuestionFromSelection(checkbox.value);
                    }
                });
                renderSelectedQuestions();
                renderReviewSummary();
                syncAvailableToggleState();
            });
        }

        if (availableLoadMoreBtn) {
            availableLoadMoreBtn.addEventListener("click", function () {
                fetchAvailableQuestions({ append: true });
            });
        }

        if (addCategoryBtn && categorySelector) {
            addCategoryBtn.addEventListener("click", function () {
                const categoryId = categorySelector.value;
                if (!categoryId) {
                    window.alert("Pilih kategori terlebih dahulu.");
                    return;
                }
                fetchAllByCategoryAndSelect(categoryId);
            });
        }

        if (filterSearchInput) {
            filterSearchInput.addEventListener("input", applyQuestionFilters);
        }
        if (filterSubjectSelect) {
            filterSubjectSelect.addEventListener("change", function () {
                fetchAvailableQuestions({ append: false });
            });
        }
        if (filterTypeSelect) {
            filterTypeSelect.addEventListener("change", function () {
                fetchAvailableQuestions({ append: false });
            });
        }
        if (filterCategorySelect) {
            filterCategorySelect.addEventListener("change", function () {
                fetchAvailableQuestions({ append: false });
            });
        }
        if (filterResetBtn) {
            filterResetBtn.addEventListener("click", function () {
                if (filterSearchInput) {
                    filterSearchInput.value = "";
                }
                if (filterSubjectSelect) {
                    filterSubjectSelect.value = "";
                }
                if (filterTypeSelect) {
                    filterTypeSelect.value = "";
                }
                if (filterCategorySelect) {
                    filterCategorySelect.value = "";
                }
                fetchAvailableQuestions({ append: false });
            });
        }

        if (availableModalEl) {
            availableModalEl.addEventListener("shown.bs.modal", function () {
                if (!availableState.totalItems && !availableState.isLoading) {
                    fetchAvailableQuestions({ append: false });
                }
                if (filterSearchInput) {
                    filterSearchInput.focus();
                }
            });
        }

        if (selectedToggleSelectBtn) {
            selectedToggleSelectBtn.addEventListener("click", function () {
                const bulkChecks = Array.from(selectedListEl.querySelectorAll(".selected-question-bulk-check"));
                if (!bulkChecks.length) {
                    return;
                }
                const shouldSelectAll = bulkChecks.some(function (checkbox) { return !checkbox.checked; });
                bulkChecks.forEach(function (checkbox) {
                    checkbox.checked = shouldSelectAll;
                });
                syncSelectedBulkCheckAllState();
            });
        }

        if (applyBulkSelectedBtn) {
            applyBulkSelectedBtn.addEventListener("click", function () {
                const targetIds = getSelectedBulkQuestionIds();
                if (!targetIds.length) {
                    window.alert("Pilih minimal satu soal pada daftar soal terpilih.");
                    return;
                }

                targetIds.forEach(function (questionId) {
                    const item = selectedQuestions[questionId];
                    if (!item) {
                        return;
                    }
                    if (bulkPointsInput && bulkPointsInput.value.trim() !== "") {
                        item.points_override = bulkPointsInput.value.trim();
                    }
                    item.allow_previous_override = boolFromOverride(bulkAllowPrevSelect && bulkAllowPrevSelect.value);
                    item.allow_next_override = boolFromOverride(bulkAllowNextSelect && bulkAllowNextSelect.value);
                    item.force_sequential_override = boolFromOverride(bulkForceSeqSelect && bulkForceSeqSelect.value);
                    item.override_navigation = hasNavigationOverride(item);
                });

                renderSelectedQuestions();
                renderReviewSummary();
            });
        }

        if (deleteBulkSelectedBtn) {
            deleteBulkSelectedBtn.addEventListener("click", function () {
                const targetIds = getSelectedBulkQuestionIds();
                if (!targetIds.length) {
                    window.alert("Pilih minimal satu soal untuk dihapus.");
                    return;
                }
                targetIds.forEach(function (questionId) {
                    delete selectedQuestions[questionId];
                });
                syncAvailableCheckboxState();
                renderSelectedQuestions();
                renderReviewSummary();
            });
        }

        document.querySelectorAll(".assignment-checkbox").forEach(function (checkbox) {
            checkbox.addEventListener("change", function () {
                syncAssignmentPayload();
                renderReviewSummary();
            });
        });

        if (studentAssignmentToggleBtn) {
            studentAssignmentToggleBtn.addEventListener("click", function () {
                const checkboxes = getStudentAssignmentCheckboxes();
                if (!checkboxes.length) {
                    return;
                }
                const shouldSelectAll = checkboxes.some(function (checkbox) { return !checkbox.checked; });
                checkboxes.forEach(function (checkbox) {
                    checkbox.checked = shouldSelectAll;
                });
                syncAssignmentPayload();
                renderReviewSummary();
            });
        }

        if (prevBtn) {
            prevBtn.addEventListener("click", function () {
                setStep(currentStep - 1);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener("click", function () {
                if (canMoveToStep(currentStep + 1)) {
                    setStep(currentStep + 1);
                }
            });
        }

        stepIndicators.forEach(function (indicator, index) {
            indicator.addEventListener("click", function () {
                const step = parseInt(indicator.getAttribute("data-step-indicator"), 10);
                if (!isNaN(step) && canMoveToStep(step)) {
                    setStep(step);
                }
            });

            indicator.addEventListener("keydown", function (event) {
                let targetIndex = index;
                if (event.key === "ArrowRight") {
                    targetIndex = (index + 1) % stepIndicators.length;
                } else if (event.key === "ArrowLeft") {
                    targetIndex = (index - 1 + stepIndicators.length) % stepIndicators.length;
                } else if (event.key === "Home") {
                    targetIndex = 0;
                } else if (event.key === "End") {
                    targetIndex = stepIndicators.length - 1;
                } else {
                    return;
                }

                event.preventDefault();
                stepIndicators[targetIndex].focus();
            });
        });

        submitButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                statusActionInput.value = button.getAttribute("data-status-action") || "draft";
                serializeSelectedQuestions();
                syncAssignmentPayload();
            });
        });

        const globalForceSequential = document.getElementById("id_global_force_sequential");
        const globalAllowPrevious = document.getElementById("id_global_allow_previous");
        if (globalForceSequential && globalAllowPrevious) {
            globalForceSequential.addEventListener("change", function () {
                if (globalForceSequential.checked) {
                    globalAllowPrevious.checked = false;
                }
            });
        }

        if (allowRetakeField) {
            allowRetakeField.addEventListener("change", function () {
                toggleRetakeSettings();
                renderReviewSummary();
            });
        }
        if (certificateEnabledField) {
            certificateEnabledField.addEventListener("change", function () {
                toggleCertificateSettings();
                renderReviewSummary();
            });
        }
        if (certificateTemplateField) {
            certificateTemplateField.addEventListener("change", renderReviewSummary);
        }
        if (maxRetakeAttemptsField) {
            maxRetakeAttemptsField.addEventListener("input", renderReviewSummary);
        }
        if (retakeCooldownField) {
            retakeCooldownField.addEventListener("input", renderReviewSummary);
        }
        if (retakeShowReviewField) {
            retakeShowReviewField.addEventListener("change", renderReviewSummary);
        }
        document.querySelectorAll('input[name="retake_score_policy"]').forEach(function (input) {
            input.addEventListener("change", renderReviewSummary);
        });

        loadInitialSelected();
        renderSelectedQuestions();
        fetchAvailableQuestions({ append: false });

        if (Array.isArray(initialAssignments)) {
            initialAssignments.forEach(function (item) {
                const selector = `.assignment-checkbox[data-type="${item.type}"][value="${item.id}"]`;
                const checkbox = document.querySelector(selector);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
        }
        syncAssignmentPayload();
        renderReviewSummary();
        toggleRetakeSettings();
        toggleCertificateSettings();
        syncStudentAssignmentToggleState();

        if (window.Sortable && selectedListEl) {
            window.Sortable.create(selectedListEl, {
                animation: 150,
                handle: ".drag-handle",
                onEnd() {
                    serializeSelectedQuestions();
                    renderSelectedQuestions();
                    renderReviewSummary();
                }
            });
        }

        form.addEventListener("submit", function () {
            serializeSelectedQuestions();
            syncAssignmentPayload();
        });

        setStep(findInitialStepFromErrors());
    });
})();
