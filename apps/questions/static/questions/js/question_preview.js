(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var previewModal = document.getElementById("previewModal");
        var previewFrame = document.getElementById("previewFrame");
        var deleteModal = document.getElementById("deleteModal");
        var deleteForm = document.getElementById("deleteQuestionForm");
        var deleteQuestionText = document.getElementById("deleteQuestionText");

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

    });
})();
