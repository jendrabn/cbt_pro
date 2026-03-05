(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var previewModal = document.getElementById("previewModal");
        var previewFrame = document.getElementById("previewFrame");
        var deleteModal = document.getElementById("deleteModal");
        var deleteForm = document.getElementById("deleteQuestionForm");
        var deleteQuestionText = document.getElementById("deleteQuestionText");
        var selectAllCheckbox = document.getElementById("selectAllQuestions");
        var itemCheckboxes = Array.from(document.querySelectorAll(".question-select-item"));
        var exportSelectedButtons = Array.from(document.querySelectorAll(".export-selected-btn"));

        if (previewModal && previewFrame) {
            previewModal.addEventListener("show.bs.modal", function (event) {
                var trigger = event.relatedTarget;
                var source = trigger && trigger.closest ? trigger.closest("[data-preview-url]") : null;
                var url = source ? source.getAttribute("data-preview-url") : "";
                if (!url) {
                    event.preventDefault();
                    return;
                }
                previewFrame.src = url;
            });
            previewModal.addEventListener("hidden.bs.modal", function () {
                previewFrame.src = "about:blank";
            });
        }

        if (deleteModal && deleteForm && deleteQuestionText) {
            deleteModal.addEventListener("show.bs.modal", function (event) {
                var trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }
                deleteForm.action = trigger.getAttribute("data-action-url") || "";
                deleteQuestionText.textContent = trigger.getAttribute("data-question-text") || "";
            });
        }

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener("change", function () {
                itemCheckboxes.forEach(function (checkbox) {
                    checkbox.checked = selectAllCheckbox.checked;
                });
            });
        }

        itemCheckboxes.forEach(function (checkbox) {
            checkbox.addEventListener("change", function () {
                if (!selectAllCheckbox) {
                    return;
                }
                var allChecked = itemCheckboxes.length > 0 && itemCheckboxes.every(function (item) {
                    return item.checked;
                });
                selectAllCheckbox.checked = allChecked;
            });
        });

        function getSelectedIds() {
            return itemCheckboxes
                .filter(function (checkbox) { return checkbox.checked; })
                .map(function (checkbox) { return checkbox.value; });
        }

        function exportSelected(format) {
            var ids = getSelectedIds();
            if (!ids.length) {
                window.alert("Pilih minimal satu soal untuk ekspor terpilih.");
                return;
            }

            var baseUrl = window.questionExportBaseUrl || "";
            if (!baseUrl) {
                return;
            }
            var params = new URLSearchParams(window.location.search);
            params.delete("page");
            params.delete("format");
            params.delete("ids");
            params.set("format", format);
            ids.forEach(function (id) {
                params.append("ids", id);
            });
            window.location.href = baseUrl + "?" + params.toString();
        }

        exportSelectedButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                var format = button.getAttribute("data-format") || "json";
                exportSelected(format);
            });
        });
    });
})();
