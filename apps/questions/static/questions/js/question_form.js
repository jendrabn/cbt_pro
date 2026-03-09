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

    function getOptionInput(row) {
        return row.querySelector(".option-input");
    }

    function getOptionRadio(row) {
        return row.querySelector(".option-correct-radio");
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
        if (input) {
            input.disabled = !visible;
        }
        if (radio) {
            radio.disabled = !visible;
            if (!visible) {
                radio.checked = false;
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
                var input = document.createElement("input");
                input.type = "file";
                input.accept = meta.filetype === "image" ? "image/*" : "audio/*,video/*";
                input.onchange = function () {
                    var file = input.files && input.files.length ? input.files[0] : null;
                    if (!file) {
                        return;
                    }
                    uploadRichTextFile(file, null, editorConfig)
                        .then(function (payload) {
                            var uploadedUrl = payload.location || payload.url;
                            if (meta.filetype === "image") {
                                callback(uploadedUrl, {
                                    alt: file.name,
                                    title: file.name
                                });
                                return;
                            }
                            callback(uploadedUrl, {
                                source2: "",
                                poster: ""
                            });
                        })
                        .catch(function (message) {
                            window.alert(message || "Upload media gagal.");
                        });
                };
                input.click();
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
        var multipleChoiceCard = document.getElementById("multipleChoiceCard");
        var answerCard = document.getElementById("answerCard");
        var addOptionBtn = document.getElementById("addOptionBtn");
        var optionRows = Array.prototype.slice.call(document.querySelectorAll(".option-item-row"));
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

        function syncOptionVisibility() {
            optionRows.forEach(function (row) {
                var defaultVisible = row.getAttribute("data-default-visible") === "1";
                var radio = getOptionRadio(row);
                var shouldShow = defaultVisible || isOptionOpened(row) || rowHasValue(row) || (radio && radio.checked);
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

        function toggleTypeSections() {
            if (!typeSelect) {
                return;
            }
            var isMultipleChoice = typeSelect.value === "multiple_choice";

            if (multipleChoiceCard) {
                multipleChoiceCard.classList.toggle("d-none", !isMultipleChoice);
            }
            if (answerCard) {
                answerCard.classList.toggle("d-none", isMultipleChoice);
            }

            if (isMultipleChoice) {
                syncOptionVisibility();
                initVisibleOptionEditors();
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

        document.querySelectorAll(".remove-option-btn").forEach(function (button) {
            button.addEventListener("click", function () {
                var row = button.closest(".option-item-row");
                if (!row) {
                    return;
                }
                var input = getOptionInput(row);
                var radio = getOptionRadio(row);
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
            editorConfig: editorConfig
        });
        initRichTextEditor(document.getElementById("id_explanation"), {
            height: 320,
            minHeight: 320,
            editorConfig: editorConfig
        });

        toggleTypeSections();
        syncOptionVisibility();
    });
})();
