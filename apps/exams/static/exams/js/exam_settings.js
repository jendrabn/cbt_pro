(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var previewModal = document.getElementById("examPreviewModal");
        var previewFrame = document.getElementById("examPreviewFrame");
        var duplicateModal = document.getElementById("duplicateModal");
        var duplicateForm = document.getElementById("duplicateExamForm");
        var duplicateTitle = document.getElementById("duplicateExamTitle");
        var deleteModal = document.getElementById("deleteModal");
        var deleteForm = document.getElementById("deleteExamForm");
        var deleteTitle = document.getElementById("deleteExamTitle");

        if (previewModal && previewFrame) {
            previewModal.addEventListener("show.bs.modal", function (event) {
                var trigger = event.relatedTarget;
                var source = trigger && trigger.closest ? trigger.closest("[data-preview-url]") : null;
                var previewUrl = source ? source.getAttribute("data-preview-url") : "";
                if (!previewUrl) {
                    event.preventDefault();
                    return;
                }
                previewFrame.src = previewUrl;
            });
            previewModal.addEventListener("hidden.bs.modal", function () {
                previewFrame.src = "about:blank";
            });
        }

        if (duplicateModal && duplicateForm && duplicateTitle) {
            duplicateModal.addEventListener("show.bs.modal", function (event) {
                var trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }
                duplicateForm.action = trigger.getAttribute("data-action-url") || "";
                duplicateTitle.textContent = trigger.getAttribute("data-title") || "";
            });
        }

        if (deleteModal && deleteForm && deleteTitle) {
            deleteModal.addEventListener("show.bs.modal", function (event) {
                var trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }
                deleteForm.action = trigger.getAttribute("data-action-url") || "";
                deleteTitle.textContent = trigger.getAttribute("data-title") || "";
            });
        }
    });
})();
