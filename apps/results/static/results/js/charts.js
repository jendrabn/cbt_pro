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

        const distributionData = parseData("result-score-distribution-data");
        const passFailData = parseData("result-pass-fail-data");
        const examComparisonData = parseData("result-exam-comparison-data");
        const classComparisonData = parseData("result-class-comparison-data");

        const distributionCanvas = document.getElementById("scoreDistributionChart");
        if (distributionCanvas && distributionData) {
            new window.Chart(distributionCanvas, {
                type: "bar",
                data: {
                    labels: distributionData.labels || [],
                    datasets: [
                        {
                            label: "Jumlah Siswa",
                            data: distributionData.values || [],
                            backgroundColor: ["#dc3545", "#fd7e14", "#ffc107", "#0d6efd", "#198754"],
                            borderRadius: 6,
                            borderSkipped: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
                }
            });
        }

        const passFailCanvas = document.getElementById("passFailChart");
        if (passFailCanvas && passFailData) {
            new window.Chart(passFailCanvas, {
                type: "doughnut",
                data: {
                    labels: passFailData.labels || [],
                    datasets: [
                        {
                            data: passFailData.values || [],
                            backgroundColor: ["#198754", "#dc3545"]
                        }
                    ]
                },
                options: {
                    responsive: true,
                    cutout: "62%",
                    plugins: { legend: { position: "bottom" } }
                }
            });
        }

        const examComparisonCanvas = document.getElementById("examComparisonChart");
        if (examComparisonCanvas && examComparisonData) {
            new window.Chart(examComparisonCanvas, {
                type: "bar",
                data: {
                    labels: examComparisonData.labels || [],
                    datasets: [
                        {
                            label: "Rata-rata Nilai (%)",
                            data: examComparisonData.avg_scores || [],
                            backgroundColor: "#0d6efd"
                        },
                        {
                            label: "Tingkat Lulus (%)",
                            data: examComparisonData.pass_rates || [],
                            backgroundColor: "#20c997"
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, max: 100 } }
                }
            });
        }

        const classComparisonCanvas = document.getElementById("classComparisonChart");
        if (classComparisonCanvas && classComparisonData) {
            new window.Chart(classComparisonCanvas, {
                type: "bar",
                data: {
                    labels: classComparisonData.labels || [],
                    datasets: [
                        {
                            label: "Rata-rata Nilai (%)",
                            data: classComparisonData.avg_scores || [],
                            backgroundColor: "#6f42c1"
                        },
                        {
                            label: "Tingkat Lulus (%)",
                            data: classComparisonData.pass_rates || [],
                            backgroundColor: "#198754"
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, max: 100 } }
                }
            });
        }

        const analyticsTrendData = parseData("analytics-trend-data");
        const analyticsPassData = parseData("analytics-pass-rate-data");
        const analyticsClassData = parseData("analytics-class-average-data");

        const analyticsTrendCanvas = document.getElementById("analyticsTrendChart");
        if (analyticsTrendCanvas && analyticsTrendData) {
            new window.Chart(analyticsTrendCanvas, {
                type: "line",
                data: {
                    labels: analyticsTrendData.labels || [],
                    datasets: [
                        {
                            label: "Rata-rata Nilai",
                            data: analyticsTrendData.values || [],
                            borderColor: "#0d6efd",
                            backgroundColor: "rgba(13, 110, 253, 0.12)",
                            fill: true,
                            tension: 0.25
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, max: 100 } }
                }
            });
        }

        const analyticsPassCanvas = document.getElementById("analyticsPassChart");
        if (analyticsPassCanvas && analyticsPassData) {
            new window.Chart(analyticsPassCanvas, {
                type: "line",
                data: {
                    labels: analyticsPassData.labels || [],
                    datasets: [
                        {
                            label: "Tingkat Lulus",
                            data: analyticsPassData.values || [],
                            borderColor: "#198754",
                            backgroundColor: "rgba(25, 135, 84, 0.12)",
                            fill: true,
                            tension: 0.25
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, max: 100 } }
                }
            });
        }

        const analyticsClassCanvas = document.getElementById("analyticsClassChart");
        if (analyticsClassCanvas && analyticsClassData) {
            new window.Chart(analyticsClassCanvas, {
                type: "bar",
                data: {
                    labels: analyticsClassData.labels || [],
                    datasets: [
                        {
                            label: "Rata-rata Nilai",
                            data: analyticsClassData.values || [],
                            backgroundColor: "#fd7e14"
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, max: 100 } }
                }
            });
        }
    });
})();
