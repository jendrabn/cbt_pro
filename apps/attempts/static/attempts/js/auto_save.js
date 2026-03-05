(function attachExamRoomAutosave(windowObj) {
    function debounce(fn, wait = 700) {
        let timeoutId = null;
        return (...args) => {
            if (timeoutId) {
                windowObj.clearTimeout(timeoutId);
            }
            timeoutId = windowObj.setTimeout(() => {
                fn(...args);
            }, wait);
        };
    }

    function buildSaveIndicator() {
        return {
            syncing(el) {
                if (!el) {
                    return;
                }
                el.classList.remove("save-indicator-success", "save-indicator-error");
                el.textContent = "Menyimpan jawaban...";
            },
            success(el, label) {
                if (!el) {
                    return;
                }
                el.classList.remove("save-indicator-error");
                el.classList.add("save-indicator-success");
                el.textContent = label || "Tersimpan otomatis";
            },
            error(el, label) {
                if (!el) {
                    return;
                }
                el.classList.remove("save-indicator-success");
                el.classList.add("save-indicator-error");
                el.textContent = label || "Gagal menyimpan";
            },
        };
    }

    windowObj.ExamRoomAutoSave = {
        debounce,
        buildSaveIndicator,
    };
})(window);
