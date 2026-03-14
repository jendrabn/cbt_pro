(function () {
    function parseData(id) {
        const el = document.getElementById(id);
        if (!el) {
            return null;
        }
        try {
            return JSON.parse(el.textContent);
        } catch (error) {
            return null;
        }
    }

    function hasChartLibrary() {
        return typeof window.Chart !== "undefined";
    }

    document.addEventListener("DOMContentLoaded", function () {
        if (!hasChartLibrary()) {
            return;
        }

        const trendData = parseData("student-results-trend-data");
        const subjectData = parseData("student-results-subject-data");
        const answerBreakdownData = parseData("student-result-answer-breakdown-data");

        const trendCanvas = document.getElementById("studentResultsTrendChart");
        if (trendCanvas && trendData) {
            new window.Chart(trendCanvas, {
                type: "line",
                data: {
                    labels: trendData.labels || [],
                    datasets: [
                        {
                            label: "Nilai (%)",
                            data: trendData.values || [],
                            borderColor: "#0d6efd",
                            backgroundColor: "rgba(13, 110, 253, 0.14)",
                            tension: 0.3,
                            fill: true,
                            pointRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: "top" }
                    },
                    scales: {
                        y: {
                            min: 0,
                            max: 100
                        }
                    }
                }
            });
        }

        const subjectCanvas = document.getElementById("studentResultsSubjectChart");
        if (subjectCanvas && subjectData) {
            new window.Chart(subjectCanvas, {
                type: "bar",
                data: {
                    labels: subjectData.labels || [],
                    datasets: [
                        {
                            label: "Rata-rata Nilai (%)",
                            data: subjectData.values || [],
                            backgroundColor: "#198754",
                            borderRadius: 8
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            min: 0,
                            max: 100
                        }
                    }
                }
            });
        }

        const breakdownCanvas = document.getElementById("studentResultAnswerBreakdownChart");
        if (breakdownCanvas && answerBreakdownData) {
            new window.Chart(breakdownCanvas, {
                type: "doughnut",
                data: {
                    labels: answerBreakdownData.labels || [],
                    datasets: [
                        {
                            data: answerBreakdownData.values || [],
                            backgroundColor: ["#198754", "#dc3545", "#6c757d"],
                            borderWidth: 1,
                            borderColor: "#ffffff"
                        }
                    ]
                },
                options: {
                    responsive: true,
                    cutout: "62%",
                    plugins: {
                        legend: {
                            position: "bottom"
                        }
                    }
                }
            });
        }
    });
})();
