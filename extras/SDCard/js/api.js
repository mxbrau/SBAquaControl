// API Communication Layer
const API = {
    // Generic API call wrapper
    async call(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },

    // Status
    async getStatus() {
        return this.call(CONFIG.api.status);
    },

    // Schedule
    async getSchedule(channel) {
        return this.call(`${CONFIG.api.scheduleGet}?channel=${channel}`);
    },

    async getAllSchedules() {
        return this.call(CONFIG.api.scheduleAll);
    },

    async saveSchedule(channel, targets) {
        return this.call(CONFIG.api.scheduleSave, {
            method: 'POST',
            body: JSON.stringify({ channel, targets })
        });
    },

    async clearAllSchedules() {
        return this.call(CONFIG.api.scheduleClear, {
            method: 'POST'
        });
    },

    async addTarget(channel, time, value) {
        return this.call(CONFIG.api.targetAdd, {
            method: 'POST',
            body: JSON.stringify({ channel, time, value })
        });
    },

    async deleteTarget(channel, time) {
        return this.call(CONFIG.api.targetDelete, {
            method: 'POST',
            body: JSON.stringify({ channel, time })
        });
    },

    // Test Mode
    async startTestMode() {
        return this.call(CONFIG.api.testStart, { method: 'POST' });
    },

    async updateTestValue(channel, value) {
        return this.call(CONFIG.api.testUpdate, {
            method: 'POST',
            body: JSON.stringify({ channel, value })
        });
    },

    async exitTestMode() {
        return this.call(CONFIG.api.testExit, { method: 'POST' });
    },

    // Macros
    async getMacros() {
        return this.call(CONFIG.api.macroList);
    },

    async getMacro(id) {
        return this.call(`${CONFIG.api.macroGet}?id=${encodeURIComponent(id)}`);
    },

    async saveMacro(id, name, duration, channels) {
        return this.call(CONFIG.api.macroSave, {
            method: 'POST',
            body: JSON.stringify({ id, name, duration, channels })
        });
    },

    async activateMacro(id) {
        return this.call(CONFIG.api.macroActivate, {
            method: 'POST',
            body: JSON.stringify({ id })
        });
    },

    async stopMacro() {
        return this.call(CONFIG.api.macroStop, { method: 'POST' });
    },

    async deleteMacro(id) {
        return this.call(CONFIG.api.macroDelete, {
            method: 'POST',
            body: JSON.stringify({ id })
        });
    }
};
