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
        const previewButtons = document.querySelectorAll(".preview-btn");
        const duplicateButtons = document.querySelectorAll(".duplicate-btn");
        const deleteButtons = document.querySelectorAll(".delete-btn");
        const previewModalInstance = previewModal ? bootstrap.Modal.getOrCreateInstance(previewModal) : null;
        const duplicateModalInstance = duplicateModal ? bootstrap.Modal.getOrCreateInstance(duplicateModal) : null;
        const deleteModalInstance = deleteModal ? bootstrap.Modal.getOrCreateInstance(deleteModal) : null;

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

        if (previewModalInstance) {
            previewButtons.forEach(function (button) {
                button.addEventListener("click", function () {
                    previewModalInstance.show(button);
                });
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

        if (duplicateModalInstance) {
            duplicateButtons.forEach(function (button) {
                button.addEventListener("click", function () {
                    duplicateModalInstance.show(button);
                });
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

        if (deleteModalInstance) {
            deleteButtons.forEach(function (button) {
                button.addEventListener("click", function () {
                    deleteModalInstance.show(button);
                });
            });
        }
    });
})();
