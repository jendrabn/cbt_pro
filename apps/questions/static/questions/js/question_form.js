(function () {
    function getOptionInput(row) {
        return row.querySelector(".option-input");
    }

    function getOptionRadio(row) {
        return row.querySelector(".option-correct-radio");
    }

    function rowHasValue(row) {
        var input = getOptionInput(row);
        return !!(input && input.value && input.value.trim());
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

    function initTinyMce() {
        if (typeof window.tinymce === "undefined") {
            return;
        }
        window.tinymce.init({
            selector: "#id_question_text, #id_explanation, #id_answer_text",
            menubar: false,
            height: 260,
            plugins: "advlist autolink lists link image charmap anchor",
            toolbar: "undo redo | bold italic underline | bullist numlist | link image | removeformat",
            branding: false,
            setup: function (editor) {
                var syncContent = function () {
                    editor.save();
                };
                editor.on("init change keyup undo redo blur", syncContent);
            }
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        var typeSelect = document.getElementById("id_question_type");
        var multipleChoiceCard = document.getElementById("multipleChoiceCard");
        var answerCard = document.getElementById("answerCard");
        var addOptionBtn = document.getElementById("addOptionBtn");
        var optionRows = Array.from(document.querySelectorAll(".option-item-row"));
        var imageInput = document.getElementById("id_question_image");
        var uploadedImageName = document.getElementById("uploadedImageName");
        var questionForm = document.getElementById("questionForm");
        var forceSequentialInput = document.getElementById("id_force_sequential");
        var allowPreviousInput = document.getElementById("id_allow_previous");

        function syncOptionVisibility() {
            optionRows.forEach(function (row) {
                var defaultVisible = row.getAttribute("data-default-visible") === "1";
                var shouldShow = defaultVisible || isOptionOpened(row) || rowHasValue(row) || (getOptionRadio(row) && getOptionRadio(row).checked);
                setRowVisible(row, shouldShow);
            });

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
            var typeValue = typeSelect.value;
            var isMultipleChoice = typeValue === "multiple_choice";

            if (multipleChoiceCard) {
                multipleChoiceCard.classList.toggle("d-none", !isMultipleChoice);
            }
            if (answerCard) {
                answerCard.classList.toggle("d-none", isMultipleChoice);
            }

            if (isMultipleChoice) {
                syncOptionVisibility();
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
                var input = getOptionInput(hiddenOptional);
                if (input) {
                    input.focus();
                }
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

        initTinyMce();
        syncOptionVisibility();
        toggleTypeSections();
    });
})();
