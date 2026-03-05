(function () {
    function formatCountdown(targetIso) {
        if (!targetIso) {
            return "";
        }
        var now = new Date();
        var target = new Date(targetIso);
        var diff = target.getTime() - now.getTime();
        if (diff <= 0) {
            return "Sudah memasuki waktu ujian.";
        }
        var totalSeconds = Math.floor(diff / 1000);
        var days = Math.floor(totalSeconds / 86400);
        var hours = Math.floor((totalSeconds % 86400) / 3600);
        var minutes = Math.floor((totalSeconds % 3600) / 60);
        var seconds = totalSeconds % 60;
        if (days > 0) {
            return days + " hari " + hours + " jam lagi";
        }
        return hours + "j " + minutes + "m " + seconds + "d lagi";
    }

    function formatDuration(seconds) {
        var total = Number(seconds || 0);
        if (!total) {
            return "0 menit";
        }
        var hours = Math.floor(total / 3600);
        var minutes = Math.floor((total % 3600) / 60);
        var parts = [];
        if (hours) {
            parts.push(hours + " jam");
        }
        if (minutes) {
            parts.push(minutes + " menit");
        }
        if (!parts.length) {
            parts.push("kurang dari 1 menit");
        }
        return parts.join(" ");
    }

    document.addEventListener("DOMContentLoaded", function () {
        var countdownNodes = Array.prototype.slice.call(document.querySelectorAll("[data-countdown]"));
        if (countdownNodes.length) {
            var tick = function () {
                countdownNodes.forEach(function (node) {
                    var target = node.getAttribute("data-target");
                    node.textContent = formatCountdown(target);
                });
            };
            tick();
            window.setInterval(tick, 1000);
        }

        var detailModal = document.getElementById("examDetailModal");
        if (detailModal) {
            var detailTitle = document.getElementById("detailTitle");
            var detailSubject = document.getElementById("detailSubject");
            var detailDescription = document.getElementById("detailDescription");
            var detailSchedule = document.getElementById("detailSchedule");
            var detailDuration = document.getElementById("detailDuration");
            var detailQuestionCount = document.getElementById("detailQuestionCount");
            var detailInstructions = document.getElementById("detailInstructions");
            var detailNavigation = document.getElementById("detailNavigation");
            var detailAntiCheat = document.getElementById("detailAntiCheat");
            var detailStartBtn = document.getElementById("detailStartBtn");
            var detailRetakeWrap = document.getElementById("detailRetakeWrap");
            var detailRetakeMax = document.getElementById("detailRetakeMax");
            var detailRetakeUsed = document.getElementById("detailRetakeUsed");
            var detailRetakeRemaining = document.getElementById("detailRetakeRemaining");
            var detailRetakePolicy = document.getElementById("detailRetakePolicy");
            var detailRetakeCooldown = document.getElementById("detailRetakeCooldown");

            detailModal.addEventListener("show.bs.modal", function (event) {
                var trigger = event.relatedTarget;
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

                var retakeEnabled = (trigger.getAttribute("data-retake-enabled") || "false") === "true";
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
                        var cooldown = trigger.getAttribute("data-retake-cooldown") || "0";
                        detailRetakeCooldown.textContent = cooldown + " menit";
                    }
                }

                var startUrl = trigger.getAttribute("data-start-url") || "";
                if (startUrl) {
                    detailStartBtn.classList.remove("d-none");
                    detailStartBtn.setAttribute("href", startUrl);
                } else {
                    detailStartBtn.classList.add("d-none");
                    detailStartBtn.setAttribute("href", "#");
                }
            });
        }

        var resultModal = document.getElementById("examResultModal");
        if (resultModal) {
            var resultTitle = document.getElementById("resultTitle");
            var resultScore = document.getElementById("resultScore");
            var resultPercentage = document.getElementById("resultPercentage");
            var resultStatus = document.getElementById("resultStatus");
            var resultCorrect = document.getElementById("resultCorrect");
            var resultWrong = document.getElementById("resultWrong");
            var resultUnanswered = document.getElementById("resultUnanswered");
            var resultTime = document.getElementById("resultTime");
            var resultDetailLink = document.getElementById("resultDetailLink");

            resultModal.addEventListener("show.bs.modal", function (event) {
                var trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }

                resultTitle.textContent = trigger.getAttribute("data-title") || "-";
                resultScore.textContent = trigger.getAttribute("data-score") || "0";
                resultPercentage.textContent = (trigger.getAttribute("data-percentage") || "0") + "%";
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
