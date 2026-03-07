(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var toggleSelectAll = document.getElementById("toggle-select-all");
        var rowChecks = Array.from(document.querySelectorAll(".row-check"));
        var toggleSelectAllLabel = document.querySelector(".toggle-select-all-label");
        var sortOptionSelect = document.getElementById("result-sort-option");
        var detailButtons = Array.from(document.querySelectorAll(".student-detail-btn"));

        var updateToggleButton = function () {
            if (!toggleSelectAll) {
                return;
            }
            var totalRows = rowChecks.length;
            var checkedRows = rowChecks.filter(function (item) { return item.checked; }).length;
            var allSelected = totalRows > 0 && checkedRows === totalRows;

            toggleSelectAll.dataset.allSelected = allSelected ? "true" : "false";
            toggleSelectAll.title = allSelected ? "Batalkan semua pilihan siswa" : "Pilih semua siswa";
            if (toggleSelectAllLabel) {
                toggleSelectAllLabel.textContent = allSelected ? "Batalkan Semua" : "Pilih Semua";
            }
        };

        if (toggleSelectAll) {
            toggleSelectAll.addEventListener("click", function () {
                var shouldSelectAll = this.dataset.allSelected !== "true";
                rowChecks.forEach(function (item) {
                    item.checked = shouldSelectAll;
                });
                updateToggleButton();
            });
        }

        rowChecks.forEach(function (item) {
            item.addEventListener("change", function () {
                updateToggleButton();
            });
        });

        if (sortOptionSelect) {
            sortOptionSelect.addEventListener("change", function () {
                var params = new URLSearchParams(window.location.search);
                params.delete("page");
                params.delete("sort");
                params.delete("dir");
                params.set("sort_option", this.value || "rank_asc");
                window.location.href = window.location.pathname + "?" + params.toString();
            });
        }

        updateToggleButton();

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
