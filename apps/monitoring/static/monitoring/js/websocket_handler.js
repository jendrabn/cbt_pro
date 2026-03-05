(function (window) {
    function MonitoringWebSocket(options) {
        this.url = options && options.url ? options.url : "";
        this.onMessage = options && typeof options.onMessage === "function" ? options.onMessage : function () {};
        this.onStatus = options && typeof options.onStatus === "function" ? options.onStatus : function () {};
        this.socket = null;
        this.retryTimer = null;
        this.retryDelayMs = 5000;
    }

    MonitoringWebSocket.prototype.connect = function () {
        if (!this.url || !window.WebSocket) {
            this.onStatus("unsupported");
            return;
        }
        this.disconnect();
        try {
            this.socket = new window.WebSocket(this.url);
        } catch (err) {
            this.onStatus("error");
            this.scheduleReconnect();
            return;
        }

        var self = this;
        this.socket.onopen = function () {
            self.onStatus("connected");
        };
        this.socket.onmessage = function (event) {
            self.onMessage(event.data);
        };
        this.socket.onclose = function () {
            self.onStatus("disconnected");
            self.scheduleReconnect();
        };
        this.socket.onerror = function () {
            self.onStatus("error");
        };
    };

    MonitoringWebSocket.prototype.scheduleReconnect = function () {
        var self = this;
        if (this.retryTimer) {
            window.clearTimeout(this.retryTimer);
        }
        this.retryTimer = window.setTimeout(function () {
            self.connect();
        }, this.retryDelayMs);
    };

    MonitoringWebSocket.prototype.disconnect = function () {
        if (this.retryTimer) {
            window.clearTimeout(this.retryTimer);
            this.retryTimer = null;
        }
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    };

    window.MonitoringWebSocket = MonitoringWebSocket;
})(window);
