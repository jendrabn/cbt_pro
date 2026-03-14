(function () {
    function formatCountdown(targetIso) {
        if (!targetIso) {
            return "";
        }
        const now = new Date();
        const target = new Date(targetIso);
        const diff = target.getTime() - now.getTime();
        if (diff <= 0) {
            return "Sudah memasuki waktu ujian.";
        }
        const totalSeconds = Math.floor(diff / 1000);
        const days = Math.floor(totalSeconds / 86400);
        const hours = Math.floor((totalSeconds % 86400) / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        if (days > 0) {
            return `${days} hari ${hours} jam lagi`;
        }
        return `${hours}j ${minutes}m ${seconds}d lagi`;
    }

    function formatDuration(seconds) {
        const total = Number(seconds || 0);
        if (!total) {
            return "0 menit";
        }
        const hours = Math.floor(total / 3600);
        const minutes = Math.floor((total % 3600) / 60);
        const parts = [];
        if (hours) {
            parts.push(`${hours} jam`);
        }
        if (minutes) {
            parts.push(`${minutes} menit`);
        }
        if (!parts.length) {
            parts.push("kurang dari 1 menit");
        }
        return parts.join(" ");
    }

    document.addEventListener("DOMContentLoaded", function () {
        const countdownNodes = Array.prototype.slice.call(document.querySelectorAll("[data-countdown]"));
        if (countdownNodes.length) {
            const tick = function () {
                countdownNodes.forEach(function (node) {
                    const target = node.getAttribute("data-target");
                    node.textContent = formatCountdown(target);
                });
            };
            tick();
            window.setInterval(tick, 1000);
        }

        const detailModal = document.getElementById("examDetailModal");
        if (detailModal) {
            const detailTitle = document.getElementById("detailTitle");
            const detailSubject = document.getElementById("detailSubject");
            const detailDescription = document.getElementById("detailDescription");
            const detailSchedule = document.getElementById("detailSchedule");
            const detailDuration = document.getElementById("detailDuration");
            const detailQuestionCount = document.getElementById("detailQuestionCount");
            const detailInstructions = document.getElementById("detailInstructions");
            const detailNavigation = document.getElementById("detailNavigation");
            const detailAntiCheat = document.getElementById("detailAntiCheat");
            const detailStartBtn = document.getElementById("detailStartBtn");
            const detailRetakeWrap = document.getElementById("detailRetakeWrap");
            const detailRetakeMax = document.getElementById("detailRetakeMax");
            const detailRetakeUsed = document.getElementById("detailRetakeUsed");
            const detailRetakeRemaining = document.getElementById("detailRetakeRemaining");
            const detailRetakePolicy = document.getElementById("detailRetakePolicy");
            const detailRetakeCooldown = document.getElementById("detailRetakeCooldown");

            detailModal.addEventListener("show.bs.modal", function (event) {
                const trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }

                detailTitle.textContent = trigger.getAttribute("data-title") || "-";
                detailSubject.textContent = trigger.getAttribute("data-subject") || "-";
                detailDescription.textContent = trigger.getAttribute("data-description") || "-";
                detailSchedule.textContent = trigger.getAttribute("data-schedule") || "-";
                detailDuration.textContent = trigger.getAttribute("data-duration") || "-";
                detailQuestionCount.textContent = trigger.getAttribute("data-question-count") || "-";
                detailInstructions.textContent = trigger.getAttribute("data-instructions") || "-";
                detailNavigation.textContent = trigger.getAttribute("data-navigation-rules") || "-";
                detailAntiCheat.textContent = trigger.getAttribute("data-anti-cheat") || "-";

                const retakeEnabled = (trigger.getAttribute("data-retake-enabled") || "false") === "true";
                if (detailRetakeWrap) {
                    detailRetakeWrap.classList.toggle("d-none", !retakeEnabled);
                }
                if (retakeEnabled) {
                    if (detailRetakeMax) {
                        detailRetakeMax.textContent = trigger.getAttribute("data-retake-max-attempts") || "-";
                    }
                    if (detailRetakeUsed) {
                        detailRetakeUsed.textContent = trigger.getAttribute("data-retake-attempts-used") || "-";
                    }
                    if (detailRetakeRemaining) {
                        detailRetakeRemaining.textContent = trigger.getAttribute("data-retake-remaining-attempts") || "-";
                    }
                    if (detailRetakePolicy) {
                        detailRetakePolicy.textContent = trigger.getAttribute("data-retake-policy") || "-";
                    }
                    if (detailRetakeCooldown) {
                        const cooldown = trigger.getAttribute("data-retake-cooldown") || "0";
                        detailRetakeCooldown.textContent = `${cooldown} menit`;
                    }
                }

                const startUrl = trigger.getAttribute("data-start-url") || "";
                if (startUrl) {
                    detailStartBtn.classList.remove("d-none");
                    detailStartBtn.setAttribute("href", startUrl);
                } else {
                    detailStartBtn.classList.add("d-none");
                    detailStartBtn.setAttribute("href", "#");
                }
            });
        }

        const resultModal = document.getElementById("examResultModal");
        if (resultModal) {
            const resultTitle = document.getElementById("resultTitle");
            const resultScore = document.getElementById("resultScore");
            const resultPercentage = document.getElementById("resultPercentage");
            const resultStatus = document.getElementById("resultStatus");
            const resultCorrect = document.getElementById("resultCorrect");
            const resultWrong = document.getElementById("resultWrong");
            const resultUnanswered = document.getElementById("resultUnanswered");
            const resultTime = document.getElementById("resultTime");
            const resultDetailLink = document.getElementById("resultDetailLink");

            resultModal.addEventListener("show.bs.modal", function (event) {
                const trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }

                resultTitle.textContent = trigger.getAttribute("data-title") || "-";
                resultScore.textContent = trigger.getAttribute("data-score") || "0";
                resultPercentage.textContent = `${trigger.getAttribute("data-percentage") || "0"}%`;
                resultStatus.textContent = trigger.getAttribute("data-status") || "-";
                resultCorrect.textContent = trigger.getAttribute("data-correct") || "0";
                resultWrong.textContent = trigger.getAttribute("data-wrong") || "0";
                resultUnanswered.textContent = trigger.getAttribute("data-unanswered") || "0";
                resultTime.textContent = formatDuration(trigger.getAttribute("data-time-spent") || "0");
                if (resultDetailLink) {
                    resultDetailLink.setAttribute("href", trigger.getAttribute("data-result-url") || "/student/results/");
                }
            });
        }
    });
})();
