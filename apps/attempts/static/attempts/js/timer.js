(function attachExamRoomTimer(windowObj) {
    function formatDuration(totalSeconds) {
        const safe = Math.max(parseInt(totalSeconds || 0, 10), 0);
        const hours = Math.floor(safe / 3600);
        const minutes = Math.floor((safe % 3600) / 60);
        const seconds = safe % 60;
        if (hours > 0) {
            return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
        }
        return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    }

    function createTimer({ initialSeconds, onTick, onFinish }) {
        let remaining = Math.max(parseInt(initialSeconds || 0, 10), 0);
        let intervalId = null;

        const emit = () => {
            if (typeof onTick === "function") {
                onTick(remaining, formatDuration(remaining));
            }
        };

        const start = () => {
            if (intervalId) {
                return;
            }
            emit();
            intervalId = windowObj.setInterval(() => {
                remaining = Math.max(remaining - 1, 0);
                emit();
                if (remaining <= 0) {
                    stop();
                    if (typeof onFinish === "function") {
                        onFinish();
                    }
                }
            }, 1000);
        };

        const stop = () => {
            if (!intervalId) {
                return;
            }
            windowObj.clearInterval(intervalId);
            intervalId = null;
        };

        const setRemaining = (seconds) => {
            remaining = Math.max(parseInt(seconds || 0, 10), 0);
            emit();
        };

        return {
            start,
            stop,
            setRemaining,
            getRemaining: () => remaining,
            formatDuration,
        };
    }

    windowObj.ExamRoomTimer = {
        formatDuration,
        createTimer,
    };
})(window);
