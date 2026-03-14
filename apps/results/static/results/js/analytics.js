(function () {
    document.addEventListener("DOMContentLoaded", function () {
        const toggleSelectAll = document.getElementById("toggle-select-all");
        const rowChecks = Array.from(document.querySelectorAll(".row-check"));
        const toggleSelectAllLabel = document.querySelector(".toggle-select-all-label");
        const sortOptionSelect = document.getElementById("result-sort-option");
        const detailButtons = Array.from(document.querySelectorAll(".student-detail-btn"));

        const updateToggleButton = function () {
            if (!toggleSelectAll) {
                return;
            }
            const totalRows = rowChecks.length;
            const checkedRows = rowChecks.filter(function (item) { return item.checked; }).length;
            const allSelected = totalRows > 0 && checkedRows === totalRows;

            toggleSelectAll.dataset.allSelected = allSelected ? "true" : "false";
            toggleSelectAll.title = allSelected ? "Batalkan semua pilihan siswa" : "Pilih semua siswa";
            if (toggleSelectAllLabel) {
                toggleSelectAllLabel.textContent = allSelected ? "Batalkan Semua" : "Pilih Semua";
            }
        };

        if (toggleSelectAll) {
            toggleSelectAll.addEventListener("click", function () {
                const shouldSelectAll = this.dataset.allSelected !== "true";
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
                const params = new URLSearchParams(window.location.search);
                params.delete("page");
                params.delete("sort");
                params.delete("dir");
                params.set("sort_option", this.value || "rank_asc");
                window.location.href = `${window.location.pathname}?${params.toString()}`;
            });
        }

        updateToggleButton();

        const detailStudentName = document.getElementById("detailStudentName");
        const detailStudentClass = document.getElementById("detailStudentClass");
        const detailStudentScore = document.getElementById("detailStudentScore");
        const detailStudentPercentage = document.getElementById("detailStudentPercentage");
        const detailStudentStatus = document.getElementById("detailStudentStatus");
        const detailStudentTime = document.getElementById("detailStudentTime");
        const detailStudentViolations = document.getElementById("detailStudentViolations");
        const detailReviewLink = document.getElementById("detailReviewLink");

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
                    detailStudentPercentage.textContent = `${button.getAttribute("data-percentage") || "-"}%`;
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
