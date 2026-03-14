(function () {
    document.addEventListener("DOMContentLoaded", function () {
        const previewModal = document.getElementById("examPreviewModal");
        const previewFrame = document.getElementById("examPreviewFrame");
        const duplicateModal = document.getElementById("duplicateModal");
        const duplicateForm = document.getElementById("duplicateExamForm");
        const duplicateTitle = document.getElementById("duplicateExamTitle");
        const deleteModal = document.getElementById("deleteModal");
        const deleteForm = document.getElementById("deleteExamForm");
        const deleteTitle = document.getElementById("deleteExamTitle");

        if (previewModal && previewFrame) {
            previewModal.addEventListener("show.bs.modal", function (event) {
                const trigger = event.relatedTarget;
                const source = trigger && trigger.closest ? trigger.closest("[data-preview-url]") : null;
                const previewUrl = source ? source.getAttribute("data-preview-url") : "";
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
                const trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }
                duplicateForm.action = trigger.getAttribute("data-action-url") || "";
                duplicateTitle.textContent = trigger.getAttribute("data-title") || "";
            });
        }

        if (deleteModal && deleteForm && deleteTitle) {
            deleteModal.addEventListener("show.bs.modal", function (event) {
                const trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }
                deleteForm.action = trigger.getAttribute("data-action-url") || "";
                deleteTitle.textContent = trigger.getAttribute("data-title") || "";
            });
        }
    });
})();
