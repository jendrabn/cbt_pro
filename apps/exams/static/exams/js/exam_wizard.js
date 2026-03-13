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

    function normalizeArrayPayload(value) {
        if (Array.isArray(value)) {
            return value;
        }
        if (!value) {
            return [];
        }
        if (typeof value === "string") {
            try {
                var parsed = JSON.parse(value);
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
        var form = document.getElementById("examWizardForm");
        if (!form) {
            return;
        }

        var questionPickerConfig = parseJSONScript("question-picker-config", {});
        var assignmentData = parseJSONScript("available-assignment-data", { classes: [], students: [] });
        var initialSelected = normalizeArrayPayload(parseJSONScript("initial-selected-questions", []));
        var initialAssignments = normalizeArrayPayload(parseJSONScript("initial-assignment-payload", []));

        var selectedPayloadInput = document.getElementById("id_selected_questions_payload");
        var assignmentPayloadInput = document.getElementById("id_assignment_payload");
        var statusActionInput = document.getElementById("id_status_action");

        var selectedListEl = document.getElementById("selectedQuestionList");
        var selectedCountEl = document.getElementById("selectedQuestionCount");
        var selectedPointsEl = document.getElementById("selectedQuestionTotalPoints");
        var selectedCountTopEl = document.getElementById("selectedQuestionCountTop");
        var selectedPointsTopEl = document.getElementById("selectedQuestionTotalPointsTop");
        var selectedCountModalEl = document.getElementById("selectedQuestionCountModal");
        var selectedPointsModalEl = document.getElementById("selectedQuestionTotalPointsModal");
        var availableListEl = document.getElementById("availableQuestionList");
        var availableLoadMoreBtn = document.getElementById("availableQuestionLoadMoreBtn");
        var availableModalEl = document.getElementById("availableQuestionModal");
        var assignmentSummaryEl = document.getElementById("assignmentSummaryList");
        var reviewSummaryEl = document.getElementById("reviewSummary");
        var studentAssignmentListEl = document.getElementById("studentAssignmentList");
        var studentAssignmentToggleBtn = document.getElementById("studentAssignmentToggleSelectBtn");
        var studentAssignmentToggleLabel = studentAssignmentToggleBtn ? studentAssignmentToggleBtn.querySelector(".student-toggle-select-label") : null;

        var addCategoryBtn = document.getElementById("addCategoryQuestionsBtn");
        var categorySelector = document.getElementById("bulkCategorySelector");
        var filterSearchInput = document.getElementById("questionFilterSearch");
        var filterSubjectSelect = document.getElementById("questionFilterSubject");
        var filterTypeSelect = document.getElementById("questionFilterType");
        var filterCategorySelect = document.getElementById("questionFilterCategory");
        var filterResetBtn = document.getElementById("questionFilterResetBtn");

        var availableToggleSelectBtn = document.getElementById("availableToggleSelectBtn");
        var selectedToggleSelectBtn = document.getElementById("selectedToggleSelectBtn");
        var bulkPointsInput = document.getElementById("bulkPointsOverride");
        var bulkAllowPrevSelect = document.getElementById("bulkAllowPrevious");
        var bulkAllowNextSelect = document.getElementById("bulkAllowNext");
        var bulkForceSeqSelect = document.getElementById("bulkForceSequential");
        var applyBulkSelectedBtn = document.getElementById("applyBulkSelectedBtn");
        var deleteBulkSelectedBtn = document.getElementById("deleteBulkSelectedBtn");
        var availableToggleSelectLabel = availableToggleSelectBtn ? availableToggleSelectBtn.querySelector(".available-toggle-select-label") : null;
        var selectedToggleSelectLabel = selectedToggleSelectBtn ? selectedToggleSelectBtn.querySelector(".selected-toggle-select-label") : null;

        var stepIndicators = Array.from(document.querySelectorAll("[data-step-indicator]"));
        var stepCards = Array.from(document.querySelectorAll("[data-step]"));
        var prevBtn = document.getElementById("wizardPrevBtn");
        var nextBtn = document.getElementById("wizardNextBtn");
        var submitButtons = Array.from(document.querySelectorAll(".wizard-submit-btn"));
        var currentStep = 1;
        var allowRetakeField = document.getElementById("id_allow_retake");
        var retakeSettingsFields = document.getElementById("retakeSettingsFields");
        var maxRetakeAttemptsField = document.getElementById("id_max_retake_attempts");
        var retakeCooldownField = document.getElementById("id_retake_cooldown_minutes");
        var retakeShowReviewField = document.getElementById("id_retake_show_review");
        var certificateEnabledField = document.getElementById("id_certificate_enabled");
        var certificateSettingsFields = document.getElementById("certificateSettingsFields");
        var certificateTemplateField = document.getElementById("id_certificate_template");

        if (!initialSelected.length && selectedPayloadInput && selectedPayloadInput.value) {
            initialSelected = normalizeArrayPayload(selectedPayloadInput.value);
        }

        var questionSearchUrl = questionPickerConfig.search_url || "";
        var questionPageSize = parseInt(questionPickerConfig.page_size || 50, 10);
        if (isNaN(questionPageSize) || questionPageSize < 10) {
            questionPageSize = 50;
        }
        var availableState = {
            page: 1,
            hasNext: false,
            totalItems: 0,
            isLoading: false
        };
        var filterDebounceTimer = null;

        var availableById = {};
        var selectedQuestions = {};

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
                var questionId = item.question_id || item.id;
                if (!questionId) {
                    return;
                }
                var fromAvailable = availableById[questionId];
                var base = fromAvailable ? normalizeQuestionFromAvailable(fromAvailable) : {
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
            var modalInstance = window.bootstrap.Modal.getInstance(modalEl);
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
            var labels = {
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
            var classes = {
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
            var parsed = parseFloat(value);
            if (isNaN(parsed)) {
                parsed = 0;
            }
            return parsed.toFixed(2);
        }

        function buildQuestionMetaBadges(subjectName, categoryName, pointsValue, questionType) {
            var badges = [];

            if (subjectName) {
                badges.push('<span class="badge-soft-info text-nowrap">' + escapeHTML(subjectName) + "</span>");
            }

            if (categoryName) {
                badges.push('<span class="badge-soft-secondary text-nowrap">' + escapeHTML(categoryName) + "</span>");
            }

            badges.push('<span class="badge-soft-warning text-nowrap">' + escapeHTML(formatPointsValue(pointsValue)) + " poin</span>");
            badges.push(
                '<span class="' + questionTypeBadgeClass(questionType) + ' text-nowrap">'
                + escapeHTML(questionTypeLabel(questionType))
                + "</span>"
            );

            return badges.join("");
        }

        function buildQuestionQueryParams(page, extraFilters) {
            var params = new URLSearchParams();
            params.set("page", String(page || 1));
            params.set("page_size", String(questionPageSize));

            var keyword = normalizeFilterText(filterSearchInput && filterSearchInput.value);
            var subject = String((filterSubjectSelect && filterSubjectSelect.value) || "").trim();
            var questionType = String((filterTypeSelect && filterTypeSelect.value) || "").trim();
            var category = String((filterCategorySelect && filterCategorySelect.value) || "").trim();

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
                    var val = extraFilters[key];
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

            var rowsHTML = items.map(function (item) {
                var safeText = escapeHTML(item.text || "");
                var checkboxId = buildSafeDomId("available-question-", item.id);
                var titleId = buildSafeDomId("available-question-title-", item.id);
                var metaBadges = buildQuestionMetaBadges(
                    item.subject_name || "",
                    item.category_name || "Tanpa kategori",
                    item.points || 0,
                    item.question_type || ""
                );
                return (
                    '<div class="list-group-item list-group-item-action question-picker-item" data-question-id="' + item.id + '" data-category-id="' + escapeHTML(item.category_id || "") + '">' +
                        '<div class="d-flex align-items-center gap-3">' +
                            '<div class="question-picker-check d-flex align-items-center flex-shrink-0">' +
                                '<input type="checkbox" class="form-check-input question-picker-checkbox m-0" id="' + checkboxId + '" value="' + item.id + '" title="Pilih soal" aria-label="Pilih soal: ' + safeText + '" aria-labelledby="' + titleId + '">' +
                            "</div>" +
                            '<div class="flex-grow-1 min-w-0">' +
                                '<p class="question-picker-title mb-2 fw-semibold" id="' + titleId + '">' + safeText + "</p>" +
                                '<div class="d-flex flex-wrap gap-2 mb-0">' + metaBadges + "</div>" +
                            '</div>' +
                        '</div>' +
                    "</div>"
                );
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
            var appendMode = !!options.append;
            if (availableState.isLoading) {
                return;
            }
            if (appendMode && !availableState.hasNext) {
                return;
            }

            var page = appendMode ? (availableState.page + 1) : 1;
            var params = buildQuestionQueryParams(page, options.extraFilters || null);
            availableState.isLoading = true;
            updateAvailablePaginationUI();

            if (!appendMode) {
                availableListEl.innerHTML = '<div class="list-group-item text-muted small">Memuat daftar soal...</div>';
            }

            fetch(questionSearchUrl + "?" + params.toString(), {
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
                    var items = Array.isArray(payload.items) ? payload.items : [];
                    items.forEach(function (item) {
                        availableById[item.id] = item;
                    });
                    renderAvailableQuestionItems(items, appendMode);
                    var pagination = payload.pagination || {};
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
            var checkboxes = Array.from(availableListEl.querySelectorAll(".question-picker-checkbox"));
            var allChecked = !!checkboxes.length && checkboxes.every(function (checkbox) { return checkbox.checked; });
            availableToggleSelectLabel.textContent = allChecked ? "Batal Pilih" : "Pilih Semua";
        }

        function syncAvailableCheckboxState() {
            if (!availableListEl) {
                return;
            }
            availableListEl.querySelectorAll(".question-picker-checkbox").forEach(function (checkbox) {
                checkbox.checked = !!selectedQuestions[checkbox.value];
                var item = checkbox.closest(".question-picker-item");
                if (item) {
                    item.classList.toggle("list-group-item-primary", checkbox.checked);
                }
            });
            syncAvailableToggleState();
        }

        function serializeSelectedQuestions() {
            var idsInOrder = Array.from(selectedListEl.querySelectorAll(".selected-question-item"))
                .map(function (el) { return el.getAttribute("data-question-id"); })
                .filter(Boolean);

            var payload = idsInOrder.map(function (questionId, index) {
                var item = selectedQuestions[questionId];
                if (!item) {
                    return null;
                }
                item.display_order = index + 1;
                var overrideNavigation = hasNavigationOverride(item);
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
            var items = Object.values(selectedQuestions).sort(function (a, b) {
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
                var safeQuestionText = escapeHTML(item.question_text || "");
                var safeDefaultPoints = escapeHTML(formatPointsValue(item.default_points || 0));
                var safePointsOverride = escapeHTML(item.points_override || "");
                var bulkCheckId = buildSafeDomId("selected-question-bulk-", item.question_id);
                var titleId = buildSafeDomId("selected-question-title-", item.question_id);
                var effectivePoints = item.points_override !== "" ? item.points_override : item.default_points;
                var metaBadges = buildQuestionMetaBadges(
                    item.subject_name || "",
                    item.category_name || "Tanpa kategori",
                    effectivePoints,
                    item.question_type || ""
                );
                return (
                    '<div class="selected-question-item list-group-item" data-question-id="' + item.question_id + '">' +
                        '<div class="d-flex align-items-center gap-3">' +
                            '<div class="question-picker-check d-flex align-items-center flex-shrink-0">' +
                                '<input type="checkbox" class="form-check-input selected-question-bulk-check m-0" id="' + bulkCheckId + '" title="Pilih untuk bulk action" aria-labelledby="' + titleId + '">' +
                            "</div>" +
                            '<div class="flex-grow-1 min-w-0">' +
                                '<p class="question-picker-title mb-2 fw-semibold" id="' + titleId + '">' + safeQuestionText + '</p>' +
                                '<div class="d-flex flex-wrap gap-2 mb-0">' + metaBadges + "</div>" +
                                '<div class="row g-2 mt-1 question-picker-controls">' +
                                    '<div class="col-12 col-md-4 col-xl-2">' +
                                        '<input type="number" min="0.01" step="0.01" class="form-control form-control-sm selected-question-points" value="' + safePointsOverride + '" placeholder="Poin (' + safeDefaultPoints + ')" aria-label="Timpa poin untuk soal ini">' +
                                    "</div>" +
                                    '<div class="col-12 col-md-4 col-xl-2">' +
                                        '<select class="form-select form-select-sm selected-question-allow-prev" aria-label="Override navigasi sebelumnya">' +
                                            '<option value="inherit" ' + (selectValue(item.allow_previous_override) === "inherit" ? "selected" : "") + '>Prev: Ikuti</option>' +
                                            '<option value="true" ' + (selectValue(item.allow_previous_override) === "true" ? "selected" : "") + '>Prev: Ya</option>' +
                                            '<option value="false" ' + (selectValue(item.allow_previous_override) === "false" ? "selected" : "") + '>Prev: Tidak</option>' +
                                        '</select>' +
                                    "</div>" +
                                    '<div class="col-12 col-md-4 col-xl-2">' +
                                        '<select class="form-select form-select-sm selected-question-allow-next" aria-label="Override navigasi berikutnya">' +
                                            '<option value="inherit" ' + (selectValue(item.allow_next_override) === "inherit" ? "selected" : "") + '>Next: Ikuti</option>' +
                                            '<option value="true" ' + (selectValue(item.allow_next_override) === "true" ? "selected" : "") + '>Next: Ya</option>' +
                                            '<option value="false" ' + (selectValue(item.allow_next_override) === "false" ? "selected" : "") + '>Next: Tidak</option>' +
                                        '</select>' +
                                    "</div>" +
                                    '<div class="col-12 col-md-4 col-xl-3">' +
                                        '<select class="form-select form-select-sm selected-question-force-seq" aria-label="Override aturan berurutan">' +
                                            '<option value="inherit" ' + (selectValue(item.force_sequential_override) === "inherit" ? "selected" : "") + '>Berurutan: Ikuti</option>' +
                                            '<option value="true" ' + (selectValue(item.force_sequential_override) === "true" ? "selected" : "") + '>Berurutan: Ya</option>' +
                                            '<option value="false" ' + (selectValue(item.force_sequential_override) === "false" ? "selected" : "") + '>Berurutan: Tidak</option>' +
                                        '</select>' +
                                    "</div>" +
                                "</div>" +
                            "</div>" +
                            '<div class="d-flex align-items-center gap-2 flex-shrink-0 ms-auto">' +
                                '<button type="button" class="icon-only-btn drag-handle" title="Geser untuk ubah urutan" aria-label="Geser untuk ubah urutan: ' + safeQuestionText + '">' +
                                    '<i class="ri-draggable fs-5"></i>' +
                                "</button>" +
                                '<button type="button" class="icon-only-btn is-danger remove-selected-question-btn" title="Hapus soal dari pilihan" aria-label="Hapus soal dari pilihan: ' + safeQuestionText + '">' +
                                    '<i class="ri-delete-bin-line"></i>' +
                                "</button>" +
                            "</div>" +
                        '</div>' +
                    '</div>'
                );
            }).join("");

            var totalPoints = 0;
            items.forEach(function (item) {
                var points = item.points_override !== "" ? parseFloat(item.points_override) : parseFloat(item.default_points || 0);
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
            var bulkChecks = Array.from(selectedListEl.querySelectorAll(".selected-question-bulk-check"));
            bulkChecks.forEach(function (checkbox) {
                var item = checkbox.closest(".selected-question-item");
                if (item) {
                    item.classList.toggle("list-group-item-primary", checkbox.checked);
                }
            });
            var allChecked = !!bulkChecks.length && bulkChecks.every(function (checkbox) { return checkbox.checked; });
            selectedToggleSelectLabel.textContent = allChecked ? "Batal Pilih" : "Pilih Semua";
        }

        function getSelectedBulkQuestionIds() {
            return Array.from(selectedListEl.querySelectorAll(".selected-question-item"))
                .filter(function (item) {
                    var bulkCheck = item.querySelector(".selected-question-bulk-check");
                    return bulkCheck && bulkCheck.checked;
                })
                .map(function (item) { return item.getAttribute("data-question-id"); })
                .filter(Boolean);
        }

        function bindSelectedQuestionEvents() {
            selectedListEl.querySelectorAll(".selected-question-item").forEach(function (card) {
                var questionId = card.getAttribute("data-question-id");
                var model = selectedQuestions[questionId];
                if (!model) {
                    return;
                }
                var allowPrevSelect = card.querySelector(".selected-question-allow-prev");
                var allowNextSelect = card.querySelector(".selected-question-allow-next");
                var forceSeqSelect = card.querySelector(".selected-question-force-seq");
                model.override_navigation = hasNavigationOverride(model);

                card.querySelector(".remove-selected-question-btn").addEventListener("click", function () {
                    delete selectedQuestions[questionId];
                    syncAvailableCheckboxState();
                    renderSelectedQuestions();
                    renderReviewSummary();
                });

                var bulkCheck = card.querySelector(".selected-question-bulk-check");
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
            var payload = getCheckedAssignments();
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
            var classMap = {};
            assignmentData.classes.forEach(function (c) { classMap[c.id] = c.name; });
            var studentMap = {};
            assignmentData.students.forEach(function (s) { studentMap[s.id] = s.name + " (" + s.username + ")"; });

            assignmentSummaryEl.innerHTML = payload.map(function (item) {
                var label = item.type === "class" ? (classMap[item.id] || item.id) : (studentMap[item.id] || item.id);
                return "<li>" + (item.type === "class" ? "Kelas: " : "Siswa: ") + label + "</li>";
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
            var checkboxes = getStudentAssignmentCheckboxes();
            var hasStudents = checkboxes.length > 0;
            var allChecked = hasStudents && checkboxes.every(function (checkbox) { return checkbox.checked; });
            studentAssignmentToggleBtn.disabled = !hasStudents;
            studentAssignmentToggleLabel.textContent = allChecked ? "Batal Pilih" : "Pilih Semua";
        }

        function setStep(stepNumber) {
            currentStep = Math.max(1, Math.min(7, stepNumber));
            stepCards.forEach(function (card) {
                var step = parseInt(card.getAttribute("data-step"), 10);
                var isActive = step === currentStep;
                card.classList.toggle("d-none", !isActive);
                card.toggleAttribute("hidden", !isActive);
                card.setAttribute("aria-hidden", isActive ? "false" : "true");
            });
            stepIndicators.forEach(function (indicator) {
                var step = parseInt(indicator.getAttribute("data-step-indicator"), 10);
                var isActive = step === currentStep;
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
            var desiredStep = Math.max(1, Math.min(7, targetStep));
            if (desiredStep <= currentStep) {
                return true;
            }

            for (var step = currentStep; step < desiredStep; step += 1) {
                if (step === 3 && Object.keys(selectedQuestions).length === 0) {
                    window.alert("Pilih minimal satu soal sebelum lanjut.");
                    return false;
                }
                if (step === 4 && allowRetakeField && allowRetakeField.checked) {
                    var attemptsValue = parseInt((maxRetakeAttemptsField && maxRetakeAttemptsField.value) || "0", 10);
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
            var stepWithError = stepCards.find(function (card) {
                return !!card.querySelector(".text-danger, .alert-danger");
            });
            if (!stepWithError) {
                return 1;
            }
            var parsed = parseInt(stepWithError.getAttribute("data-step"), 10);
            return isNaN(parsed) ? 1 : parsed;
        }

        function renderReviewSummary() {
            if (!reviewSummaryEl) {
                return;
            }
            var selectedCount = Object.keys(selectedQuestions).length;
            var assignments = getCheckedAssignments();
            var title = (document.getElementById("id_title") || {}).value || "-";
            var subjectText = (document.getElementById("id_subject") || {}).selectedOptions;
            subjectText = subjectText && subjectText.length ? subjectText[0].textContent : "-";
            var startTime = (document.getElementById("id_start_time") || {}).value || "-";
            var endTime = (document.getElementById("id_end_time") || {}).value || "-";
            var passingScore = (document.getElementById("id_passing_score") || {}).value || "-";
            var randomizeQ = (document.getElementById("id_randomize_questions") || {}).checked ? "Ya" : "Tidak";
            var randomizeOpt = (document.getElementById("id_randomize_options") || {}).checked ? "Ya" : "Tidak";
            var overrideGlobal = (document.getElementById("id_override_question_navigation") || {}).checked ? "Ya" : "Tidak";
            var certificateEnabled = !!(certificateEnabledField && certificateEnabledField.checked);
            var certificateTemplateText = "-";
            if (certificateTemplateField && certificateTemplateField.selectedOptions && certificateTemplateField.selectedOptions.length) {
                certificateTemplateText = certificateTemplateField.selectedOptions[0].textContent || "-";
            }
            var allowRetake = !!(allowRetakeField && allowRetakeField.checked);
            var retakePolicy = (document.querySelector('input[name="retake_score_policy"]:checked') || {}).value || "highest";
            var retakePolicyLabelMap = {
                highest: "Nilai Tertinggi",
                latest: "Nilai Terbaru",
                average: "Nilai Rata-rata"
            };
            var retakeSummary = "Nonaktif";
            if (allowRetake) {
                var maxAttemptsValue = (maxRetakeAttemptsField && maxRetakeAttemptsField.value) || "2";
                var cooldownValue = (retakeCooldownField && retakeCooldownField.value) || "0";
                var reviewBeforeRetake = (retakeShowReviewField && retakeShowReviewField.checked) ? "Ya" : "Tidak";
                retakeSummary =
                    "Aktif | Maks. " + maxAttemptsValue + " percobaan | Nilai: "
                    + (retakePolicyLabelMap[retakePolicy] || "Nilai Tertinggi")
                    + " | Jeda: " + cooldownValue + " menit | Review sebelum retake: " + reviewBeforeRetake;
            }

            reviewSummaryEl.innerHTML = [
                ["Judul Ujian", title],
                ["Mata Pelajaran", subjectText],
                ["Waktu Mulai", startTime],
                ["Waktu Selesai", endTime],
                ["Jumlah Soal Dipilih", String(selectedCount)],
                ["Jumlah Penugasan", String(assignments.length)],
                ["Nilai Kelulusan", passingScore + "%"],
                ["Acak Soal", randomizeQ],
                ["Acak Opsi", randomizeOpt],
                ["Timpa Navigasi Global", overrideGlobal],
                ["Sertifikat", certificateEnabled ? ("Aktif | " + certificateTemplateText) : "Nonaktif"],
                ["Retake", retakeSummary]
            ].map(function (row) {
                return '<div class="list-group-item d-flex justify-content-between gap-2"><span>' + row[0] + '</span><strong class="text-end">' + row[1] + '</strong></div>';
            }).join("");
        }

        function toggleRetakeSettings() {
            if (!retakeSettingsFields || !allowRetakeField) {
                return;
            }
            var enabled = !!allowRetakeField.checked;
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
            var enabled = !!certificateEnabledField.checked;
            certificateSettingsFields.classList.toggle("d-none", !enabled);
            certificateSettingsFields.toggleAttribute("hidden", !enabled);
            if (!enabled && certificateTemplateField) {
                certificateTemplateField.value = "";
            }
        }

        function addQuestionToSelection(questionId) {
            if (!selectedQuestions[questionId] && availableById[questionId]) {
                var item = normalizeQuestionFromAvailable(availableById[questionId]);
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
            var page = 1;
            var hasNext = true;
            var addedCount = 0;
            var hasFailed = false;

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
                var params = new URLSearchParams();
                params.set("page", String(page));
                params.set("page_size", String(Math.max(questionPageSize, 100)));
                params.set("category", categoryId);

                fetch(questionSearchUrl + "?" + params.toString(), {
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
                        var items = Array.isArray(payload.items) ? payload.items : [];
                        items.forEach(function (item) {
                            availableById[item.id] = item;
                            if (!selectedQuestions[item.id]) {
                                addQuestionToSelection(item.id);
                                addedCount += 1;
                            }
                        });
                        var pagination = payload.pagination || {};
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
                var checkbox = event.target;
                if (!checkbox || !checkbox.classList.contains("question-picker-checkbox")) {
                    return;
                }
                var questionId = checkbox.value;
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
                var checkboxes = Array.from(availableListEl.querySelectorAll(".question-picker-checkbox"));
                if (!checkboxes.length) {
                    return;
                }
                var shouldSelectAll = checkboxes.some(function (checkbox) { return !checkbox.checked; });
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
                var categoryId = categorySelector.value;
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
                var bulkChecks = Array.from(selectedListEl.querySelectorAll(".selected-question-bulk-check"));
                if (!bulkChecks.length) {
                    return;
                }
                var shouldSelectAll = bulkChecks.some(function (checkbox) { return !checkbox.checked; });
                bulkChecks.forEach(function (checkbox) {
                    checkbox.checked = shouldSelectAll;
                });
                syncSelectedBulkCheckAllState();
            });
        }

        if (applyBulkSelectedBtn) {
            applyBulkSelectedBtn.addEventListener("click", function () {
                var targetIds = getSelectedBulkQuestionIds();
                if (!targetIds.length) {
                    window.alert("Pilih minimal satu soal pada daftar soal terpilih.");
                    return;
                }

                targetIds.forEach(function (questionId) {
                    var item = selectedQuestions[questionId];
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
                var targetIds = getSelectedBulkQuestionIds();
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
                var checkboxes = getStudentAssignmentCheckboxes();
                if (!checkboxes.length) {
                    return;
                }
                var shouldSelectAll = checkboxes.some(function (checkbox) { return !checkbox.checked; });
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
                var step = parseInt(indicator.getAttribute("data-step-indicator"), 10);
                if (!isNaN(step) && canMoveToStep(step)) {
                    setStep(step);
                }
            });

            indicator.addEventListener("keydown", function (event) {
                var targetIndex = index;
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

        var globalForceSequential = document.getElementById("id_global_force_sequential");
        var globalAllowPrevious = document.getElementById("id_global_allow_previous");
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
                var selector = '.assignment-checkbox[data-type="' + item.type + '"][value="' + item.id + '"]';
                var checkbox = document.querySelector(selector);
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
                onEnd: function () {
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
