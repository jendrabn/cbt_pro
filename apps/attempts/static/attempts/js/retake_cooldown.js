(function () {
    function formatRemaining(seconds) {
        var total = Math.max(parseInt(seconds || 0, 10), 0);
        var minutes = Math.floor(total / 60);
        var secs = total % 60;
        return minutes + "m " + secs + "d";
    }

    document.addEventListener("DOMContentLoaded", function () {
        var nodes = Array.prototype.slice.call(document.querySelectorAll("[data-retake-countdown]"));
        if (!nodes.length) {
            return;
        }

        function tick() {
            var now = Date.now();
            nodes.forEach(function (node) {
                var targetIso = node.getAttribute("data-next-available");
                if (!targetIso) {
                    return;
                }
                var target = new Date(targetIso).getTime();
                var diffSeconds = Math.max(Math.floor((target - now) / 1000), 0);
                if (diffSeconds > 0) {
                    node.textContent = "Retake tersedia dalam " + formatRemaining(diffSeconds) + ".";
                } else {
                    node.textContent = "Retake sudah tersedia. Silakan refresh halaman.";
                }
            });
        }

        tick();
        window.setInterval(tick, 1000);
    });
})();
