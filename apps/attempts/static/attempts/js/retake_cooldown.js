(function () {
    function formatRemaining(seconds) {
        const total = Math.max(parseInt(seconds || 0, 10), 0);
        const minutes = Math.floor(total / 60);
        const secs = total % 60;
        return `${minutes}m ${secs}d`;
    }

    document.addEventListener("DOMContentLoaded", function () {
        const nodes = Array.prototype.slice.call(document.querySelectorAll("[data-retake-countdown]"));
        if (!nodes.length) {
            return;
        }

        function tick() {
            const now = Date.now();
            nodes.forEach(function (node) {
                const targetIso = node.getAttribute("data-next-available");
                if (!targetIso) {
                    return;
                }
                const target = new Date(targetIso).getTime();
                const diffSeconds = Math.max(Math.floor((target - now) / 1000), 0);
                if (diffSeconds > 0) {
                    node.textContent = `Retake tersedia dalam ${formatRemaining(diffSeconds)}.`;
                } else {
                    node.textContent = "Retake sudah tersedia. Silakan refresh halaman.";
                }
            });
        }

        tick();
        window.setInterval(tick, 1000);
    });
})();
