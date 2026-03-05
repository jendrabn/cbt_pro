(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var selectAll = document.getElementById("selectAllResults");
        var itemCheckboxes = Array.from(document.querySelectorAll(".result-select-item"));
        var exportForm = document.getElementById("exportSelectedForm");
        var selectedIdsInput = document.getElementById("selectedResultIds");
        var detailButtons = Array.from(document.querySelectorAll(".student-detail-btn"));

        if (selectAll) {
            selectAll.addEventListener("change", function () {
                itemCheckboxes.forEach(function (item) {
                    item.checked = selectAll.checked;
                });
            });
        }

        itemCheckboxes.forEach(function (item) {
            item.addEventListener("change", function () {
                if (!selectAll) {
                    return;
                }
                var allChecked =
                    itemCheckboxes.length > 0 &&
                    itemCheckboxes.every(function (checkbox) { return checkbox.checked; });
                selectAll.checked = allChecked;
            });
        });

        if (exportForm && selectedIdsInput) {
            exportForm.addEventListener("submit", function (event) {
                var ids = itemCheckboxes
                    .filter(function (item) { return item.checked; })
                    .map(function (item) { return item.value; });
                if (!ids.length) {
                    event.preventDefault();
                    window.alert("Pilih minimal satu siswa untuk ekspor terpilih.");
                    return;
                }
                selectedIdsInput.value = ids.join(",");
            });
        }

        var detailStudentName = document.getElementById("detailStudentName");
        var detailStudentClass = document.getElementById("detailStudentClass");
        var detailStudentScore = document.getElementById("detailStudentScore");
        var detailStudentPercentage = document.getElementById("detailStudentPercentage");
        var detailStudentStatus = document.getElementById("detailStudentStatus");
        var detailStudentTime = document.getElementById("detailStudentTime");
        var detailStudentViolations = document.getElementById("detailStudentViolations");
        var detailReviewLink = document.getElementById("detailReviewLink");

        detailButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                if (detailStudentName) {
                    detailStudentName.textContent = button.getAttribute("data-student-name") || "-";
                }
                if (detailStudentClass) {
                    detailStudentClass.textContent = button.getAttribute("data-class") || "-";
                }
                if (detailStudentScore) {
                    detailStudentScore.textContent = button.getAttribute("data-score") || "-";
                }
                if (detailStudentPercentage) {
                    detailStudentPercentage.textContent = (button.getAttribute("data-percentage") || "-") + "%";
                }
                if (detailStudentStatus) {
                    detailStudentStatus.textContent = button.getAttribute("data-status") || "-";
                }
                if (detailStudentTime) {
                    detailStudentTime.textContent = button.getAttribute("data-time") || "-";
                }
                if (detailStudentViolations) {
                    detailStudentViolations.textContent = button.getAttribute("data-violations") || "0";
                }
                if (detailReviewLink) {
                    detailReviewLink.setAttribute("href", button.getAttribute("data-review-url") || "#");
                }
            });
        });
    });
})();
