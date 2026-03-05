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

    document.addEventListener("DOMContentLoaded", function () {
        var form = document.getElementById("examWizardForm");
        if (!form) {
            return;
        }

        var availableQuestions = parseJSONScript("available-questions-data", []);
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
        var availableVisibleCountEl = document.getElementById("availableQuestionVisibleCount");
        var assignmentSummaryEl = document.getElementById("assignmentSummaryList");
        var reviewSummaryEl = document.getElementById("reviewSummary");

        var addCategoryBtn = document.getElementById("addCategoryQuestionsBtn");
        var categorySelector = document.getElementById("bulkCategorySelector");
        var filterSearchInput = document.getElementById("questionFilterSearch");
        var filterSubjectSelect = document.getElementById("questionFilterSubject");
        var filterTypeSelect = document.getElementById("questionFilterType");
        var filterCategorySelect = document.getElementById("questionFilterCategory");
        var filterApplyBtn = document.getElementById("questionFilterApplyBtn");
        var filterResetBtn = document.getElementById("questionFilterResetBtn");
        var questionFilterModalEl = document.getElementById("questionFilterModal");

        var selectedBulkCheckAll = document.getElementById("selectedBulkCheckAll");
        var bulkPointsInput = document.getElementById("bulkPointsOverride");
        var bulkAllowPrevSelect = document.getElementById("bulkAllowPrevious");
        var bulkAllowNextSelect = document.getElementById("bulkAllowNext");
        var bulkForceSeqSelect = document.getElementById("bulkForceSequential");
        var applyBulkSelectedBtn = document.getElementById("applyBulkSelectedBtn");
        var deleteBulkSelectedBtn = document.getElementById("deleteBulkSelectedBtn");
        var selectedBulkModalEl = document.getElementById("selectedBulkModal");

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

        var availableById = {};
        availableQuestions.forEach(function (item) {
            availableById[item.id] = item;
        });

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
                base.override_navigation = !!item.override_navigation;
                base.allow_previous_override = boolFromOverride(item.allow_previous_override);
                base.allow_next_override = boolFromOverride(item.allow_next_override);
                base.force_sequential_override = boolFromOverride(item.force_sequential_override);

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

        function populateQuestionSubjectFilter() {
            if (!filterSubjectSelect) {
                return;
            }
            var seen = {};
            availableQuestions.forEach(function (item) {
                var normalized = normalizeFilterText(item.subject_name);
                if (!normalized || seen[normalized]) {
                    return;
                }
                seen[normalized] = item.subject_name || "";
            });
            var current = filterSubjectSelect.value;
            Object.keys(seen).sort().forEach(function (key) {
                var option = document.createElement("option");
                option.value = key;
                option.textContent = seen[key];
                filterSubjectSelect.appendChild(option);
            });
            filterSubjectSelect.value = current;
        }

        function applyQuestionFilters() {
            var keyword = normalizeFilterText(filterSearchInput && filterSearchInput.value);
            var subject = normalizeFilterText(filterSubjectSelect && filterSubjectSelect.value);
            var questionType = normalizeFilterText(filterTypeSelect && filterTypeSelect.value);
            var categoryId = normalizeFilterText(filterCategorySelect && filterCategorySelect.value);
            var visibleCount = 0;

            document.querySelectorAll(".question-picker-item").forEach(function (item) {
                var itemText = normalizeFilterText(item.getAttribute("data-question-text"));
                var itemSubject = normalizeFilterText(item.getAttribute("data-subject-name"));
                var itemType = normalizeFilterText(item.getAttribute("data-question-type"));
                var itemCategory = normalizeFilterText(item.getAttribute("data-category-id"));

                var isVisible = true;
                if (keyword && itemText.indexOf(keyword) === -1) {
                    isVisible = false;
                }
                if (subject && itemSubject !== subject) {
                    isVisible = false;
                }
                if (questionType && itemType !== questionType) {
                    isVisible = false;
                }
                if (categoryId && itemCategory !== categoryId) {
                    isVisible = false;
                }

                item.classList.toggle("d-none", !isVisible);
                if (isVisible) {
                    visibleCount += 1;
                }
            });

            if (availableVisibleCountEl) {
                availableVisibleCountEl.textContent = String(visibleCount);
            }
        }

        function syncAvailableCheckboxState() {
            document.querySelectorAll(".question-picker-checkbox").forEach(function (checkbox) {
                checkbox.checked = !!selectedQuestions[checkbox.value];
            });
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
                return {
                    question_id: item.question_id,
                    display_order: item.display_order,
                    points_override: item.points_override === "" ? "" : Number(item.points_override),
                    override_navigation: !!item.override_navigation,
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
                selectedPayloadInput.value = "[]";
                if (selectedBulkCheckAll) {
                    selectedBulkCheckAll.checked = false;
                }
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
                return (
                    '<div class="selected-question-item list-group-item mb-2 rounded" data-question-id="' + item.question_id + '">' +
                        '<div class="d-flex justify-content-between align-items-start gap-2">' +
                            '<div class="d-flex align-items-start gap-2">' +
                                '<input type="checkbox" class="form-check-input selected-question-bulk-check mt-1" title="Pilih untuk bulk action">' +
                                '<i class="ri-draggable drag-handle mt-1 text-secondary" title="Geser untuk ubah urutan"></i>' +
                                '<div>' +
                                    '<p class="mb-1 fw-semibold">' + item.question_text + '</p>' +
                                    '<p class="small text-muted mb-0">' + item.subject_name + ' &bull; ' + item.category_name + ' &bull; ' + (item.question_type === "multiple_choice" ? "Pilihan Ganda" : (item.question_type === "essay" ? "Esai" : "Jawaban Singkat")) + '</p>' +
                                '</div>' +
                            '</div>' +
                            '<button type="button" class="btn btn-sm btn-outline-danger remove-selected-question-btn" title="Hapus soal dari pilihan"><i class="ri-close-line"></i></button>' +
                        '</div>' +
                        '<div class="row g-2 mt-2">' +
                            '<div class="col-md-3">' +
                                '<label class="form-label small mb-1">Poin Timpa</label>' +
                                '<input type="number" min="0.01" step="0.01" class="form-control form-control-sm selected-question-points" value="' + item.points_override + '" placeholder="' + item.default_points + '">' +
                            '</div>' +
                            '<div class="col-md-3 d-flex align-items-end">' +
                                '<label class="form-check small mb-0">' +
                                    '<input type="checkbox" class="form-check-input selected-question-override-nav" ' + (item.override_navigation ? "checked" : "") + '>' +
                                    '<span>Timpa Navigasi</span>' +
                                '</label>' +
                            '</div>' +
                            '<div class="col-md-2">' +
                                '<label class="form-label small mb-1">Sebelumnya</label>' +
                                '<select class="form-select form-select-sm selected-question-allow-prev">' +
                                    '<option value="inherit" ' + (selectValue(item.allow_previous_override) === "inherit" ? "selected" : "") + '>Ikuti</option>' +
                                    '<option value="true" ' + (selectValue(item.allow_previous_override) === "true" ? "selected" : "") + '>Ya</option>' +
                                    '<option value="false" ' + (selectValue(item.allow_previous_override) === "false" ? "selected" : "") + '>Tidak</option>' +
                                '</select>' +
                            '</div>' +
                            '<div class="col-md-2">' +
                                '<label class="form-label small mb-1">Berikutnya</label>' +
                                '<select class="form-select form-select-sm selected-question-allow-next">' +
                                    '<option value="inherit" ' + (selectValue(item.allow_next_override) === "inherit" ? "selected" : "") + '>Ikuti</option>' +
                                    '<option value="true" ' + (selectValue(item.allow_next_override) === "true" ? "selected" : "") + '>Ya</option>' +
                                    '<option value="false" ' + (selectValue(item.allow_next_override) === "false" ? "selected" : "") + '>Tidak</option>' +
                                '</select>' +
                            '</div>' +
                            '<div class="col-md-2">' +
                                '<label class="form-label small mb-1">Berurutan</label>' +
                                '<select class="form-select form-select-sm selected-question-force-seq">' +
                                    '<option value="inherit" ' + (selectValue(item.force_sequential_override) === "inherit" ? "selected" : "") + '>Ikuti</option>' +
                                    '<option value="true" ' + (selectValue(item.force_sequential_override) === "true" ? "selected" : "") + '>Ya</option>' +
                                    '<option value="false" ' + (selectValue(item.force_sequential_override) === "false" ? "selected" : "") + '>Tidak</option>' +
                                '</select>' +
                            '</div>' +
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
            serializeSelectedQuestions();
            bindSelectedQuestionEvents();
        }

        function syncSelectedBulkCheckAllState() {
            if (!selectedBulkCheckAll) {
                return;
            }
            var bulkChecks = Array.from(selectedListEl.querySelectorAll(".selected-question-bulk-check"));
            selectedBulkCheckAll.checked = !!bulkChecks.length && bulkChecks.every(function (checkbox) { return checkbox.checked; });
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

                card.querySelector(".selected-question-override-nav").addEventListener("change", function (event) {
                    model.override_navigation = event.target.checked;
                    serializeSelectedQuestions();
                });

                card.querySelector(".selected-question-allow-prev").addEventListener("change", function (event) {
                    model.allow_previous_override = boolFromOverride(event.target.value);
                    serializeSelectedQuestions();
                });

                card.querySelector(".selected-question-allow-next").addEventListener("change", function (event) {
                    model.allow_next_override = boolFromOverride(event.target.value);
                    serializeSelectedQuestions();
                });

                card.querySelector(".selected-question-force-seq").addEventListener("change", function (event) {
                    model.force_sequential_override = boolFromOverride(event.target.value);
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

        function setStep(stepNumber) {
            currentStep = Math.max(1, Math.min(7, stepNumber));
            stepCards.forEach(function (card) {
                var step = parseInt(card.getAttribute("data-step"), 10);
                card.classList.toggle("d-none", step !== currentStep);
            });
            stepIndicators.forEach(function (indicator) {
                var step = parseInt(indicator.getAttribute("data-step-indicator"), 10);
                indicator.classList.toggle("active", step === currentStep);
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

        function bindAvailableQuestionCheckboxes() {
            document.querySelectorAll(".question-picker-checkbox").forEach(function (checkbox) {
                checkbox.addEventListener("change", function () {
                    var questionId = checkbox.value;
                    if (checkbox.checked) {
                        if (!selectedQuestions[questionId] && availableById[questionId]) {
                            var item = normalizeQuestionFromAvailable(availableById[questionId]);
                            item.display_order = Object.keys(selectedQuestions).length + 1;
                            selectedQuestions[questionId] = item;
                        }
                    } else {
                        delete selectedQuestions[questionId];
                    }
                    renderSelectedQuestions();
                    renderReviewSummary();
                });
            });
        }

        if (addCategoryBtn && categorySelector) {
            addCategoryBtn.addEventListener("click", function () {
                var categoryId = categorySelector.value;
                if (!categoryId) {
                    window.alert("Pilih kategori terlebih dahulu.");
                    return;
                }
                document.querySelectorAll(".question-picker-item").forEach(function (row) {
                    if (row.getAttribute("data-category-id") !== categoryId) {
                        return;
                    }
                    var checkbox = row.querySelector(".question-picker-checkbox");
                    if (checkbox && !checkbox.checked) {
                        checkbox.checked = true;
                        checkbox.dispatchEvent(new Event("change"));
                    }
                });
            });
        }

        if (filterApplyBtn) {
            filterApplyBtn.addEventListener("click", function () {
                applyQuestionFilters();
                hideModal(questionFilterModalEl);
            });
        }
        if (filterSearchInput) {
            filterSearchInput.addEventListener("keydown", function (event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    applyQuestionFilters();
                }
            });
        }
        if (filterResetBtn) {
            filterResetBtn.addEventListener("click", function () {
                if (filterSubjectSelect) {
                    filterSubjectSelect.value = "";
                }
                if (filterTypeSelect) {
                    filterTypeSelect.value = "";
                }
                if (filterCategorySelect) {
                    filterCategorySelect.value = "";
                }
                applyQuestionFilters();
            });
        }

        if (selectedBulkCheckAll) {
            selectedBulkCheckAll.addEventListener("change", function () {
                selectedListEl.querySelectorAll(".selected-question-bulk-check").forEach(function (checkbox) {
                    checkbox.checked = selectedBulkCheckAll.checked;
                });
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
                    item.override_navigation = true;
                });

                renderSelectedQuestions();
                renderReviewSummary();
                hideModal(selectedBulkModalEl);
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
                hideModal(selectedBulkModalEl);
            });
        }

        document.querySelectorAll(".assignment-checkbox").forEach(function (checkbox) {
            checkbox.addEventListener("change", function () {
                syncAssignmentPayload();
                renderReviewSummary();
            });
        });

        if (prevBtn) {
            prevBtn.addEventListener("click", function () {
                setStep(currentStep - 1);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener("click", function () {
                if (currentStep === 3 && Object.keys(selectedQuestions).length === 0) {
                    window.alert("Pilih minimal satu soal sebelum lanjut.");
                    return;
                }
                if (currentStep === 4 && allowRetakeField && allowRetakeField.checked) {
                    var attemptsValue = parseInt((maxRetakeAttemptsField && maxRetakeAttemptsField.value) || "0", 10);
                    if (isNaN(attemptsValue) || attemptsValue < 2 || attemptsValue > 10) {
                        window.alert("Maksimal percobaan retake harus berada di rentang 2 sampai 10.");
                        return;
                    }
                }
                if (currentStep === 6 && getCheckedAssignments().length === 0) {
                    window.alert("Pilih minimal satu penugasan kelas atau siswa sebelum lanjut.");
                    return;
                }
                setStep(currentStep + 1);
            });
        }

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
        populateQuestionSubjectFilter();
        bindAvailableQuestionCheckboxes();
        applyQuestionFilters();
        syncAvailableCheckboxState();
        renderSelectedQuestions();

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

