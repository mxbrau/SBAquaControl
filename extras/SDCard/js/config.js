// Configuration
const CONFIG = {
    // Channel names (customize these!)
    channelNames: [
        'Blau',      // Channel 0
        'Weiß',      // Channel 1
        'Rot',       // Channel 2
        'Grün',      // Channel 3
        'UV',        // Channel 4
        'Mondlicht'  // Channel 5
    ],

    // Channel colors for visualization
    channelColors: [
        '#2196F3',  // Blue
        '#E0E0E0',  // White (gray for visibility)
        '#F44336',  // Red
        '#4CAF50',  // Green
        '#9C27B0',  // Purple
        '#FFD700'   // Gold
    ],

    // Update intervals
    statusUpdateInterval: 1000,      // Update status every second
    chartUpdateInterval: 60000,      // Refresh chart every 6 seconds
    sliderDebounceTime: 150,         // Wait 150ms after slider stops moving

    // API endpoints (relative URLs work with mock server and ESP8266)
    api: {
        status: '/api/status',
        scheduleGet: '/api/schedule/get',
        scheduleAll: '/api/schedule/all',
        scheduleSave: '/api/schedule/save',
        scheduleClear: '/api/schedule/clear',
        targetAdd: '/api/schedule/target/add',
        targetDelete: '/api/schedule/target/delete',
        testStart: '/api/test/start',
        testUpdate: '/api/test/update',
        testExit: '/api/test/exit',
        macroList: '/api/macro/list',
        macroGet: '/api/macro/get',
        macroSave: '/api/macro/save',
        macroActivate: '/api/macro/activate',
        macroStop: '/api/macro/stop',
        macroDelete: '/api/macro/delete'
    }
};
