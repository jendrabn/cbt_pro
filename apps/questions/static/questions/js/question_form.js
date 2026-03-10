(function () {
    function getCookie(name) {
        if (!document.cookie) {
            return "";
        }
        var cookies = document.cookie.split(";");
        for (var index = 0; index < cookies.length; index += 1) {
            var cookie = cookies[index].trim();
            if (cookie.indexOf(name + "=") === 0) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return "";
    }

    function getCsrfToken() {
        var csrfInput = document.querySelector("input[name='csrfmiddlewaretoken']");
        if (csrfInput && csrfInput.value) {
            return csrfInput.value;
        }
        return getCookie("csrftoken");
    }

    function parseEditorConfig() {
        var configNode = document.getElementById("question-editor-config");
        if (!configNode) {
            return {};
        }
        try {
            return JSON.parse(configNode.textContent || "{}");
        } catch (error) {
            return {};
        }
    }

    function escapeHtmlValue(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function hasMeaningfulRichContent(value) {
        if (!value) {
            return false;
        }
        if (/<\s*(img|video|audio|iframe|table|embed|object)\b/i.test(value)) {
            return true;
        }
        var container = document.createElement("div");
        container.innerHTML = value;
        var plainText = (container.textContent || container.innerText || "").replace(/\u00a0/g, " ").trim();
        return !!plainText;
    }

    function uploadRichTextFile(file, progressCallback, editorConfig) {
        return new Promise(function (resolve, reject) {
            if (!editorConfig.uploadUrl) {
                reject("URL upload media editor belum tersedia.");
                return;
            }

            var xhr = new XMLHttpRequest();
            xhr.open("POST", editorConfig.uploadUrl, true);
            xhr.responseType = "json";
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

            var csrfToken = getCsrfToken();
            if (csrfToken) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            }

            if (xhr.upload && typeof progressCallback === "function") {
                xhr.upload.onprogress = function (event) {
                    if (!event.lengthComputable) {
                        return;
                    }
                    progressCallback((event.loaded / event.total) * 100);
                };
            }

            xhr.onload = function () {
                var payload = xhr.response;
                if (!payload && xhr.responseText) {
                    try {
                        payload = JSON.parse(xhr.responseText);
                    } catch (error) {
                        payload = null;
                    }
                }

                if (xhr.status >= 200 && xhr.status < 300 && payload && (payload.location || payload.url)) {
                    resolve(payload);
                    return;
                }
                reject(payload && payload.error ? payload.error : "Upload media gagal diproses.");
            };

            xhr.onerror = function () {
                reject("Upload media gagal. Periksa koneksi lalu coba lagi.");
            };

            var formData = new FormData();
            formData.append("file", file);
            xhr.send(formData);
        });
    }

    function fetchRichTextMediaItems(editorConfig, fileType) {
        return new Promise(function (resolve, reject) {
            if (!editorConfig.browserUrl) {
                resolve([]);
                return;
            }

            var kindValue = fileType === "image" ? "image" : "media";
            var browserUrl = editorConfig.browserUrl;
            browserUrl += browserUrl.indexOf("?") >= 0 ? "&" : "?";
            browserUrl += "kind=" + encodeURIComponent(kindValue);

            var xhr = new XMLHttpRequest();
            xhr.open("GET", browserUrl, true);
            xhr.responseType = "json";
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

            xhr.onload = function () {
                var payload = xhr.response;
                if (!payload && xhr.responseText) {
                    try {
                        payload = JSON.parse(xhr.responseText);
                    } catch (error) {
                        payload = null;
                    }
                }

                if (xhr.status >= 200 && xhr.status < 300 && payload && Array.isArray(payload.items)) {
                    resolve(payload.items);
                    return;
                }
                reject(payload && payload.error ? payload.error : "Daftar media editor tidak dapat dimuat.");
            };

            xhr.onerror = function () {
                reject("Daftar media editor tidak dapat dimuat.");
            };

            xhr.send();
        });
    }

    function buildMediaAcceptValue(fileType) {
        return fileType === "image" ? "image/*" : "audio/*,video/*";
    }

    function chooseLocalRichTextFile(meta, editorConfig) {
        return new Promise(function (resolve, reject) {
            var input = document.createElement("input");
            input.type = "file";
            input.accept = buildMediaAcceptValue(meta.filetype);
            input.onchange = function () {
                var file = input.files && input.files.length ? input.files[0] : null;
                if (!file) {
                    resolve(null);
                    return;
                }
                uploadRichTextFile(file, null, editorConfig)
                    .then(resolve)
                    .catch(reject);
            };
            input.click();
        });
    }

    function buildMediaPreviewHtml(item) {
        var safeUrl = item && item.url ? item.url : "";
        var safeName = escapeHtmlValue(item && item.name ? item.name : "Media");
        if (item && item.kind === "image") {
            return '<img src="' + safeUrl + '" alt="' + safeName + '" class="img-fluid rounded border" style="max-height: 160px;">';
        }
        if (item && item.kind === "video") {
            return '<video src="' + safeUrl + '" controls preload="metadata" class="w-100 rounded border" style="max-height: 160px;"></video>';
        }
        if (item && item.kind === "audio") {
            return '<audio src="' + safeUrl + '" controls preload="metadata" class="w-100"></audio>';
        }
        return '<div class="small text-muted">Preview tidak tersedia.</div>';
    }

    function openRichTextMediaPicker(editorConfig, meta) {
        return fetchRichTextMediaItems(editorConfig, meta.filetype).then(function (items) {
            return new Promise(function (resolve, reject) {
                var overlay = document.createElement("div");
                overlay.className = "position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center p-3";
                overlay.style.background = "rgba(15, 23, 42, 0.7)";
                overlay.style.zIndex = "2000";

                var modal = document.createElement("div");
                modal.className = "bg-white rounded-4 shadow-lg w-100";
                modal.style.maxWidth = "920px";
                modal.style.maxHeight = "85vh";
                modal.style.overflow = "hidden";
                var escapeHandler = null;

                var closePicker = function (value) {
                    if (escapeHandler) {
                        document.removeEventListener("keydown", escapeHandler);
                        escapeHandler = null;
                    }
                    if (overlay.parentNode) {
                        overlay.parentNode.removeChild(overlay);
                    }
                    resolve(value || null);
                };

                modal.innerHTML = `
                    <div class="border-bottom px-3 py-3 d-flex flex-wrap align-items-center justify-content-between gap-2">
                        <div>
                            <h3 class="h6 mb-1">Browser Media Editor</h3>
                            <p class="small text-muted mb-0">Pilih file yang sudah diunggah atau tambahkan media baru.</p>
                        </div>
                        <div class="d-flex gap-2">
                            <button type="button" class="btn btn-sm btn-outline-primary" data-picker-upload>
                                <i class="ri-upload-2-line me-1"></i>Unggah Baru
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-secondary" data-picker-close aria-label="Tutup">
                                <i class="ri-close-line"></i>
                            </button>
                        </div>
                    </div>
                    <div class="p-3" style="overflow: auto; max-height: calc(85vh - 88px);">
                        <div class="row g-3" data-picker-grid></div>
                    </div>
                `;

                overlay.appendChild(modal);
                document.body.appendChild(overlay);

                overlay.addEventListener("click", function (event) {
                    if (event.target === overlay) {
                        closePicker(null);
                    }
                });

                escapeHandler = function (event) {
                    if (event.key === "Escape") {
                        closePicker(null);
                    }
                };
                document.addEventListener("keydown", escapeHandler);

                var closeBtn = modal.querySelector("[data-picker-close]");
                var uploadBtn = modal.querySelector("[data-picker-upload]");
                var grid = modal.querySelector("[data-picker-grid]");

                if (closeBtn) {
                    closeBtn.addEventListener("click", function () {
                        closePicker(null);
                    });
                }

                if (uploadBtn) {
                    uploadBtn.addEventListener("click", function () {
                        chooseLocalRichTextFile(meta, editorConfig)
                            .then(function (payload) {
                                if (!payload) {
                                    return;
                                }
                                closePicker(payload);
                            })
                            .catch(function (message) {
                                window.alert(message || "Upload media gagal.");
                            });
                    });
                }

                if (!grid) {
                    reject("Browser media editor tidak dapat dibuka.");
                    return;
                }

                if (!items.length) {
                    grid.innerHTML = `
                        <div class="col-12">
                            <div class="alert alert-light border mb-0">
                                Belum ada media tersimpan untuk tipe ini. Gunakan tombol <strong>Unggah Baru</strong>.
                            </div>
                        </div>
                    `;
                    return;
                }

                items.forEach(function (item) {
                    var cardWrap = document.createElement("div");
                    cardWrap.className = "col-md-6 col-xl-4";

                    var sizeLabel = item.size_kb ? item.size_kb + " KB" : "-";
                    cardWrap.innerHTML = `
                        <button type="button" class="btn btn-outline-secondary w-100 text-start h-100 p-0 overflow-hidden" data-picker-select>
                            <div class="p-2 bg-light-subtle border-bottom">
                                ${buildMediaPreviewHtml(item)}
                            </div>
                            <div class="p-3">
                                <div class="d-flex align-items-center justify-content-between gap-2 mb-2">
                                    <strong class="small text-truncate">${escapeHtmlValue(item.name)}</strong>
                                    <span class="badge text-bg-light text-uppercase">${escapeHtmlValue(item.kind)}</span>
                                </div>
                                <div class="small text-muted">Ukuran: ${escapeHtmlValue(sizeLabel)}</div>
                            </div>
                        </button>
                    `;

                    var selectBtn = cardWrap.querySelector("[data-picker-select]");
                    if (selectBtn) {
                        selectBtn.addEventListener("click", function () {
                            closePicker(item);
                        });
                    }

                    grid.appendChild(cardWrap);
                });
            });
        });
    }

    function applyPickedMediaToEditor(asset, callback, meta) {
        if (!asset) {
            return;
        }
        var uploadedUrl = asset.location || asset.url || "";
        if (!uploadedUrl) {
            return;
        }

        if (meta.filetype === "image") {
            callback(uploadedUrl, {
                alt: asset.name || "",
                title: asset.name || ""
            });
            return;
        }

        callback(uploadedUrl, {
            source2: "",
            poster: ""
        });
    }

    function getOptionInput(row) {
        return row.querySelector(".option-input");
    }

    function getOptionRadio(row) {
        return row.querySelector(".option-correct-radio");
    }

    function getOptionCheckbox(row) {
        return row.querySelector(".option-correct-checkbox");
    }

    function getOrderingInput(row) {
        return row.querySelector(".ordering-item-input");
    }

    function getMatchingPromptInput(row) {
        return row.querySelector(".matching-prompt-input");
    }

    function getMatchingAnswerInput(row) {
        return row.querySelector(".matching-answer-input");
    }

    function getEditorContent(input) {
        if (!input) {
            return "";
        }
        if (typeof window.tinymce !== "undefined" && input.id) {
            var editor = window.tinymce.get(input.id);
            if (editor) {
                return editor.getContent();
            }
        }
        return input.value || "";
    }

    function rowHasValue(row) {
        return hasMeaningfulRichContent(getEditorContent(getOptionInput(row)));
    }

    function orderingRowHasValue(row) {
        return hasMeaningfulRichContent(getEditorContent(getOrderingInput(row)));
    }

    function matchingRowHasValue(row) {
        return hasMeaningfulRichContent(getEditorContent(getMatchingPromptInput(row)))
            || hasMeaningfulRichContent(getEditorContent(getMatchingAnswerInput(row)));
    }

    function isOrderingOpened(row) {
        return row.getAttribute("data-ordering-opened") === "1";
    }

    function setOrderingOpened(row, opened) {
        row.setAttribute("data-ordering-opened", opened ? "1" : "0");
    }

    function isMatchingOpened(row) {
        return row.getAttribute("data-matching-opened") === "1";
    }

    function setMatchingOpened(row, opened) {
        row.setAttribute("data-matching-opened", opened ? "1" : "0");
    }

    function getBlankAcceptedInput(row) {
        return row.querySelector(".blank-accepted-input");
    }

    function getBlankCaseInput(row) {
        return row.querySelector(".form-check-input");
    }

    function getBlankPointsInput(row) {
        return row.querySelector(".blank-points-input");
    }

    function extractBlankNumbers(value) {
        var numbers = [];
        var seen = {};
        var regex = /\{\{\s*(\d+)\s*\}\}/g;
        var match = regex.exec(value || "");
        while (match) {
            var number = parseInt(match[1], 10);
            if (Number.isFinite(number) && !seen[number]) {
                seen[number] = true;
                numbers.push(number);
            }
            match = regex.exec(value || "");
        }
        return numbers;
    }

    function isOptionOpened(row) {
        return row.getAttribute("data-option-opened") === "1";
    }

    function setOptionOpened(row, opened) {
        row.setAttribute("data-option-opened", opened ? "1" : "0");
    }

    function setRowVisible(row, visible) {
        row.classList.toggle("d-none", !visible);
        var input = getOptionInput(row);
        var radio = getOptionRadio(row);
        var checkbox = getOptionCheckbox(row);
        if (input) {
            input.disabled = !visible;
        }
        if (radio) {
            radio.disabled = !visible;
            if (!visible) {
                radio.checked = false;
            }
        }
        if (checkbox) {
            checkbox.disabled = !visible;
            if (!visible) {
                checkbox.checked = false;
            }
        }
    }

    function buildTinyMceConfig(options) {
        var editorConfig = options.editorConfig || {};
        return {
            selector: "#" + options.textarea.id,
            menubar: "edit insert format table view",
            branding: false,
            height: options.height,
            min_height: options.minHeight || options.height,
            plugins: "advlist autolink lists link image media table charmap anchor code fullscreen preview autoresize",
            toolbar: [
                "undo redo | blocks | bold italic underline | alignleft aligncenter alignright alignjustify",
                "bullist numlist outdent indent | table | image media link | removeformat | code preview"
            ].join(" | "),
            toolbar_mode: "sliding",
            contextmenu: "link image table",
            automatic_uploads: true,
            paste_data_images: true,
            convert_urls: false,
            image_advtab: true,
            image_caption: true,
            image_dimensions: true,
            media_dimensions: true,
            media_alt_source: false,
            media_poster: false,
            object_resizing: true,
            file_picker_types: "image media",
            table_default_attributes: {
                border: "1"
            },
            table_default_styles: {
                borderCollapse: "collapse",
                width: "100%"
            },
            content_style: [
                "body { font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; }",
                "img, video, audio, iframe { max-width: 100%; }",
                "table { width: 100%; border-collapse: collapse; }",
                "table td, table th { border: 1px solid #cbd5e1; padding: 6px 8px; vertical-align: top; }"
            ].join(" "),
            autoresize_bottom_margin: 18,
            images_upload_handler: function (blobInfo, progress) {
                return uploadRichTextFile(blobInfo.blob(), progress, editorConfig).then(function (payload) {
                    return payload.location || payload.url;
                });
            },
            file_picker_callback: function (callback, value, meta) {
                if (editorConfig.browserUrl) {
                    openRichTextMediaPicker(editorConfig, meta)
                        .then(function (asset) {
                            applyPickedMediaToEditor(asset, callback, meta);
                        })
                        .catch(function () {
                            chooseLocalRichTextFile(meta, editorConfig)
                                .then(function (payload) {
                                    applyPickedMediaToEditor(payload, callback, meta);
                                })
                                .catch(function (message) {
                                    window.alert(message || "Upload media gagal.");
                                });
                        });
                    return;
                }

                chooseLocalRichTextFile(meta, editorConfig)
                    .then(function (payload) {
                        applyPickedMediaToEditor(payload, callback, meta);
                    })
                    .catch(function (message) {
                        window.alert(message || "Upload media gagal.");
                    });
            },
            audio_template_callback: function (data) {
                return '<audio controls="controls" src="' + data.source + '"></audio>';
            },
            video_template_callback: function (data) {
                var width = data.width || 640;
                var height = data.height || 360;
                var mimeAttr = data.sourcemime ? ' type="' + data.sourcemime + '"' : "";
                return (
                    '<video controls="controls" width="' + width + '" height="' + height + '">' +
                    '<source src="' + data.source + '"' + mimeAttr + ">" +
                    "</video>"
                );
            },
            setup: function (editor) {
                var syncContent = function () {
                    editor.save();
                    if (typeof options.onContentChange === "function") {
                        options.onContentChange(editor);
                    }
                };

                editor.on("init change keyup undo redo blur setcontent input", syncContent);
            }
        };
    }

    function initRichTextEditor(textarea, options) {
        if (!textarea || typeof window.tinymce === "undefined") {
            return;
        }
        if (window.tinymce.get(textarea.id)) {
            return;
        }
        window.tinymce.init(buildTinyMceConfig({
            textarea: textarea,
            height: options.height,
            minHeight: options.minHeight,
            editorConfig: options.editorConfig,
            onContentChange: options.onContentChange
        }));
    }

    document.addEventListener("DOMContentLoaded", function () {
        var editorConfig = parseEditorConfig();
        var typeSelect = document.getElementById("id_question_type");
        var questionTextInput = document.getElementById("id_question_text");
        var multipleChoiceCard = document.getElementById("multipleChoiceCard");
        var orderingCard = document.getElementById("orderingCard");
        var matchingCard = document.getElementById("matchingCard");
        var fillBlankCard = document.getElementById("fillBlankCard");
        var answerCard = document.getElementById("answerCard");
        var checkboxScoringWrap = document.getElementById("checkboxScoringWrap");
        var addOptionBtn = document.getElementById("addOptionBtn");
        var optionRows = Array.prototype.slice.call(document.querySelectorAll(".option-item-row"));
        var addOrderingItemBtn = document.getElementById("addOrderingItemBtn");
        var orderingRows = Array.prototype.slice.call(document.querySelectorAll(".ordering-item-row"));
        var addMatchingPairBtn = document.getElementById("addMatchingPairBtn");
        var matchingRows = Array.prototype.slice.call(document.querySelectorAll(".matching-pair-row"));
        var blankRows = Array.prototype.slice.call(document.querySelectorAll(".fill-blank-row"));
        var imageInput = document.getElementById("id_question_image");
        var uploadedImageName = document.getElementById("uploadedImageName");
        var questionForm = document.getElementById("questionForm");
        var forceSequentialInput = document.getElementById("id_force_sequential");
        var allowPreviousInput = document.getElementById("id_allow_previous");

        function focusOptionInput(row) {
            var input = getOptionInput(row);
            if (!input) {
                return;
            }
            if (typeof window.tinymce !== "undefined") {
                var editor = window.tinymce.get(input.id);
                if (editor) {
                    editor.focus();
                    return;
                }
            }
            input.focus();
        }

        function initVisibleOptionEditors() {
            optionRows.forEach(function (row) {
                if (row.classList.contains("d-none")) {
                    return;
                }
                initRichTextEditor(getOptionInput(row), {
                    height: 180,
                    editorConfig: editorConfig,
                    onContentChange: syncOptionVisibility
                });
            });
        }

        function focusOrderingInput(row) {
            var input = getOrderingInput(row);
            if (!input) {
                return;
            }
            if (typeof window.tinymce !== "undefined") {
                var editor = window.tinymce.get(input.id);
                if (editor) {
                    editor.focus();
                    return;
                }
            }
            input.focus();
        }

        function initVisibleOrderingEditors() {
            orderingRows.forEach(function (row) {
                if (row.classList.contains("d-none")) {
                    return;
                }
                initRichTextEditor(getOrderingInput(row), {
                    height: 180,
                    editorConfig: editorConfig,
                    onContentChange: syncOrderingVisibility
                });
            });
        }

        function focusMatchingInput(row) {
            var input = getMatchingPromptInput(row);
            if (!input) {
                return;
            }
            if (typeof window.tinymce !== "undefined") {
                var editor = window.tinymce.get(input.id);
                if (editor) {
                    editor.focus();
                    return;
                }
            }
            input.focus();
        }

        function initVisibleMatchingEditors() {
            matchingRows.forEach(function (row) {
                if (row.classList.contains("d-none")) {
                    return;
                }
                initRichTextEditor(getMatchingPromptInput(row), {
                    height: 180,
                    editorConfig: editorConfig,
                    onContentChange: syncMatchingVisibility
                });
                initRichTextEditor(getMatchingAnswerInput(row), {
                    height: 180,
                    editorConfig: editorConfig,
                    onContentChange: syncMatchingVisibility
                });
            });
        }

        function syncOptionVisibility() {
            optionRows.forEach(function (row) {
                var defaultVisible = row.getAttribute("data-default-visible") === "1";
                var radio = getOptionRadio(row);
                var checkbox = getOptionCheckbox(row);
                var shouldShow = defaultVisible || isOptionOpened(row) || rowHasValue(row) || (radio && radio.checked) || (checkbox && checkbox.checked);
                setRowVisible(row, shouldShow);
            });

            if (multipleChoiceCard && !multipleChoiceCard.classList.contains("d-none")) {
                initVisibleOptionEditors();
            }

            var hiddenOptional = optionRows.filter(function (row) {
                return row.getAttribute("data-default-visible") !== "1" && row.classList.contains("d-none");
            });
            if (addOptionBtn) {
                addOptionBtn.disabled = hiddenOptional.length === 0;
            }
        }

        function syncOrderingVisibility() {
            orderingRows.forEach(function (row) {
                var defaultVisible = row.getAttribute("data-default-visible") === "1";
                var shouldShow = defaultVisible || isOrderingOpened(row) || orderingRowHasValue(row);
                row.classList.toggle("d-none", !shouldShow);
                var input = getOrderingInput(row);
                if (input) {
                    input.disabled = !shouldShow;
                }
            });

            if (orderingCard && !orderingCard.classList.contains("d-none")) {
                initVisibleOrderingEditors();
            }

            var hiddenOptional = orderingRows.filter(function (row) {
                return row.getAttribute("data-default-visible") !== "1" && row.classList.contains("d-none");
            });
            if (addOrderingItemBtn) {
                addOrderingItemBtn.disabled = hiddenOptional.length === 0;
            }
        }

        function syncMatchingVisibility() {
            matchingRows.forEach(function (row) {
                var defaultVisible = row.getAttribute("data-default-visible") === "1";
                var shouldShow = defaultVisible || isMatchingOpened(row) || matchingRowHasValue(row);
                row.classList.toggle("d-none", !shouldShow);
                var promptInput = getMatchingPromptInput(row);
                var answerInput = getMatchingAnswerInput(row);
                if (promptInput) {
                    promptInput.disabled = !shouldShow;
                }
                if (answerInput) {
                    answerInput.disabled = !shouldShow;
                }
            });

            if (matchingCard && !matchingCard.classList.contains("d-none")) {
                initVisibleMatchingEditors();
            }

            var hiddenOptional = matchingRows.filter(function (row) {
                return row.getAttribute("data-default-visible") !== "1" && row.classList.contains("d-none");
            });
            if (addMatchingPairBtn) {
                addMatchingPairBtn.disabled = hiddenOptional.length === 0;
            }
        }

        function syncBlankDefinitionVisibility() {
            var questionContent = getEditorContent(questionTextInput);
            var blankNumbers = extractBlankNumbers(questionContent);

            blankRows.forEach(function (row) {
                var defaultVisible = row.getAttribute("data-default-visible") === "1";
                var blankNumber = parseInt(row.getAttribute("data-blank-number") || "0", 10);
                var acceptedInput = getBlankAcceptedInput(row);
                var caseInput = getBlankCaseInput(row);
                var pointsInput = getBlankPointsInput(row);
                var hasValue = Boolean(acceptedInput && acceptedInput.value && acceptedInput.value.trim())
                    || Boolean(pointsInput && pointsInput.value)
                    || Boolean(caseInput && caseInput.checked);
                var shouldShow = defaultVisible || hasValue || blankNumbers.indexOf(blankNumber) >= 0;
                row.classList.toggle("d-none", !shouldShow);
            });
        }

        function toggleTypeSections() {
            if (!typeSelect) {
                return;
            }
            var isMultipleChoice = typeSelect.value === "multiple_choice";
            var isCheckbox = typeSelect.value === "checkbox";
            var isOrdering = typeSelect.value === "ordering";
            var isMatching = typeSelect.value === "matching";
            var isFillInBlank = typeSelect.value === "fill_in_blank";
            var isChoiceType = isMultipleChoice || isCheckbox;
            var isTextAnswerType = typeSelect.value === "essay" || typeSelect.value === "short_answer";

            if (multipleChoiceCard) {
                multipleChoiceCard.classList.toggle("d-none", !isChoiceType);
            }
            if (orderingCard) {
                orderingCard.classList.toggle("d-none", !isOrdering);
            }
            if (matchingCard) {
                matchingCard.classList.toggle("d-none", !isMatching);
            }
            if (fillBlankCard) {
                fillBlankCard.classList.toggle("d-none", !isFillInBlank);
            }
            if (answerCard) {
                answerCard.classList.toggle("d-none", !isTextAnswerType);
            }
            if (checkboxScoringWrap) {
                checkboxScoringWrap.classList.toggle("d-none", !isCheckbox);
            }

            optionRows.forEach(function (row) {
                var singleWrap = row.querySelector(".correct-option-single-wrap");
                var multiWrap = row.querySelector(".correct-option-multi-wrap");
                if (singleWrap) {
                    singleWrap.classList.toggle("d-none", !isMultipleChoice);
                }
                if (multiWrap) {
                    multiWrap.classList.toggle("d-none", !isCheckbox);
                }
            });

            if (isChoiceType) {
                syncOptionVisibility();
                initVisibleOptionEditors();
            }
            if (isOrdering) {
                syncOrderingVisibility();
                initVisibleOrderingEditors();
            }
            if (isMatching) {
                syncMatchingVisibility();
                initVisibleMatchingEditors();
            }
            if (isFillInBlank) {
                syncBlankDefinitionVisibility();
            }
        }

        if (typeSelect) {
            typeSelect.addEventListener("change", toggleTypeSections);
        }

        optionRows.forEach(function (row) {
            var input = getOptionInput(row);
            if (input) {
                input.addEventListener("input", syncOptionVisibility);
            }
        });

        orderingRows.forEach(function (row) {
            var input = getOrderingInput(row);
            if (input) {
                input.addEventListener("input", syncOrderingVisibility);
            }
        });

        matchingRows.forEach(function (row) {
            var promptInput = getMatchingPromptInput(row);
            var answerInput = getMatchingAnswerInput(row);
            if (promptInput) {
                promptInput.addEventListener("input", syncMatchingVisibility);
            }
            if (answerInput) {
                answerInput.addEventListener("input", syncMatchingVisibility);
            }
        });

        blankRows.forEach(function (row) {
            var acceptedInput = getBlankAcceptedInput(row);
            var caseInput = getBlankCaseInput(row);
            var pointsInput = getBlankPointsInput(row);
            if (acceptedInput) {
                acceptedInput.addEventListener("input", syncBlankDefinitionVisibility);
            }
            if (caseInput) {
                caseInput.addEventListener("change", syncBlankDefinitionVisibility);
            }
            if (pointsInput) {
                pointsInput.addEventListener("input", syncBlankDefinitionVisibility);
            }
        });

        document.querySelectorAll(".remove-option-btn").forEach(function (button) {
            button.addEventListener("click", function () {
                var row = button.closest(".option-item-row");
                if (!row) {
                    return;
                }
                var input = getOptionInput(row);
                var radio = getOptionRadio(row);
                var checkbox = getOptionCheckbox(row);
                if (input) {
                    if (typeof window.tinymce !== "undefined") {
                        var editor = window.tinymce.get(input.id);
                        if (editor) {
                            editor.setContent("");
                            editor.save();
                        }
                    }
                    input.value = "";
                }
                if (radio) {
                    radio.checked = false;
                }
                if (checkbox) {
                    checkbox.checked = false;
                }
                setOptionOpened(row, false);
                setRowVisible(row, false);
                syncOptionVisibility();
            });
        });

        if (addOptionBtn) {
            addOptionBtn.addEventListener("click", function () {
                var hiddenOptional = optionRows.find(function (row) {
                    return row.getAttribute("data-default-visible") !== "1" && row.classList.contains("d-none");
                });
                if (!hiddenOptional) {
                    return;
                }
                setOptionOpened(hiddenOptional, true);
                setRowVisible(hiddenOptional, true);
                initRichTextEditor(getOptionInput(hiddenOptional), {
                    height: 180,
                    editorConfig: editorConfig,
                    onContentChange: syncOptionVisibility
                });
                window.setTimeout(function () {
                    focusOptionInput(hiddenOptional);
                }, 120);
                syncOptionVisibility();
            });
        }

        document.querySelectorAll(".remove-ordering-item-btn").forEach(function (button) {
            button.addEventListener("click", function () {
                var row = button.closest(".ordering-item-row");
                if (!row) {
                    return;
                }
                var input = getOrderingInput(row);
                if (input) {
                    if (typeof window.tinymce !== "undefined") {
                        var editor = window.tinymce.get(input.id);
                        if (editor) {
                            editor.setContent("");
                            editor.save();
                        }
                    }
                    input.value = "";
                }
                setOrderingOpened(row, false);
                row.classList.add("d-none");
                syncOrderingVisibility();
            });
        });

        if (addOrderingItemBtn) {
            addOrderingItemBtn.addEventListener("click", function () {
                var hiddenOptional = orderingRows.find(function (row) {
                    return row.getAttribute("data-default-visible") !== "1" && row.classList.contains("d-none");
                });
                if (!hiddenOptional) {
                    return;
                }
                setOrderingOpened(hiddenOptional, true);
                hiddenOptional.classList.remove("d-none");
                var input = getOrderingInput(hiddenOptional);
                if (input) {
                    input.disabled = false;
                }
                initRichTextEditor(getOrderingInput(hiddenOptional), {
                    height: 180,
                    editorConfig: editorConfig,
                    onContentChange: syncOrderingVisibility
                });
                window.setTimeout(function () {
                    focusOrderingInput(hiddenOptional);
                }, 120);
                syncOrderingVisibility();
            });
        }

        document.querySelectorAll(".remove-matching-pair-btn").forEach(function (button) {
            button.addEventListener("click", function () {
                var row = button.closest(".matching-pair-row");
                if (!row) {
                    return;
                }
                [getMatchingPromptInput(row), getMatchingAnswerInput(row)].forEach(function (input) {
                    if (!input) {
                        return;
                    }
                    if (typeof window.tinymce !== "undefined") {
                        var editor = window.tinymce.get(input.id);
                        if (editor) {
                            editor.setContent("");
                            editor.save();
                        }
                    }
                    input.value = "";
                });
                setMatchingOpened(row, false);
                row.classList.add("d-none");
                syncMatchingVisibility();
            });
        });

        if (addMatchingPairBtn) {
            addMatchingPairBtn.addEventListener("click", function () {
                var hiddenOptional = matchingRows.find(function (row) {
                    return row.getAttribute("data-default-visible") !== "1" && row.classList.contains("d-none");
                });
                if (!hiddenOptional) {
                    return;
                }
                setMatchingOpened(hiddenOptional, true);
                hiddenOptional.classList.remove("d-none");
                [getMatchingPromptInput(hiddenOptional), getMatchingAnswerInput(hiddenOptional)].forEach(function (input) {
                    if (input) {
                        input.disabled = false;
                    }
                });
                initRichTextEditor(getMatchingPromptInput(hiddenOptional), {
                    height: 180,
                    editorConfig: editorConfig,
                    onContentChange: syncMatchingVisibility
                });
                initRichTextEditor(getMatchingAnswerInput(hiddenOptional), {
                    height: 180,
                    editorConfig: editorConfig,
                    onContentChange: syncMatchingVisibility
                });
                window.setTimeout(function () {
                    focusMatchingInput(hiddenOptional);
                }, 120);
                syncMatchingVisibility();
            });
        }

        if (imageInput && uploadedImageName) {
            imageInput.addEventListener("change", function () {
                var file = imageInput.files && imageInput.files.length ? imageInput.files[0] : null;
                uploadedImageName.textContent = file ? ("File dipilih: " + file.name) : "";
            });
        }

        if (forceSequentialInput && allowPreviousInput) {
            forceSequentialInput.addEventListener("change", function () {
                if (forceSequentialInput.checked) {
                    allowPreviousInput.checked = false;
                }
            });
        }

        if (questionForm) {
            questionForm.addEventListener("submit", function () {
                if (typeof window.tinymce !== "undefined") {
                    window.tinymce.triggerSave();
                }
            });
        }

        initRichTextEditor(document.getElementById("id_question_text"), {
            height: 320,
            minHeight: 320,
            editorConfig: editorConfig,
            onContentChange: syncBlankDefinitionVisibility
        });
        initRichTextEditor(document.getElementById("id_explanation"), {
            height: 320,
            minHeight: 320,
            editorConfig: editorConfig
        });

        toggleTypeSections();
        syncOptionVisibility();
        syncOrderingVisibility();
        syncMatchingVisibility();
        syncBlankDefinitionVisibility();
    });
})();
