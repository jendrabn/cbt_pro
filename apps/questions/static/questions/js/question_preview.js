(function () {
    document.addEventListener("DOMContentLoaded", function () {
        const previewModal = document.getElementById("previewModal");
        const previewFrame = document.getElementById("previewFrame");
        const deleteModal = document.getElementById("deleteModal");
        const deleteForm = document.getElementById("deleteQuestionForm");
        const deleteQuestionText = document.getElementById("deleteQuestionText");

        if (previewModal && previewFrame) {
            previewModal.addEventListener("show.bs.modal", function (event) {
                const trigger = event.relatedTarget;
                const source = trigger && trigger.closest ? trigger.closest("[data-preview-url]") : null;
                const url = source ? source.getAttribute("data-preview-url") : "";
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
                const trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }
                deleteForm.action = trigger.getAttribute("data-action-url") || "";
                deleteQuestionText.textContent = trigger.getAttribute("data-question-text") || "";
            });
        }

    });
})();
