// Application State
const state = {
    testMode: false,
    macroActive: false,
    activeMacro: null,
    channelValues: Array(6).fill(0),
    linkChannels: false,
    schedules: Array(6).fill(null).map(() => []),
    macros: []
};

// Chart instances
let mainChart = null;
let macroChart = null;

// Slider update timers (for debouncing)
const sliderTimers = {};

// Initialize application
async function init() {
    console.log('🚀 Initializing Aquarium Control...');

    // Initialize main chart
    mainChart = new ChartManager('scheduleChart');
    mainChart.init();

    // Create channel controls
    createChannelControls();

    // Load initial data
    await loadSchedules();
    startScheduleUpdates();
    await loadMacros();

    // Start status updates
    startStatusUpdates();

    // Setup event listeners
    document.getElementById('linkChannels').addEventListener('change', (e) => {
        state.linkChannels = e.target.checked;
    });

    console.log('✅ Initialization complete');
}

// Periodic schedule refresh to avoid empty chart on slow/failed first load
let scheduleUpdateTimer = null;
let quickScheduleTimeout = null;
function startScheduleUpdates() {
    if (scheduleUpdateTimer) {
        clearInterval(scheduleUpdateTimer);
    }
    if (quickScheduleTimeout) {
        clearTimeout(quickScheduleTimeout);
    }
    // Refresh on the configured interval; first load already awaited in init
    scheduleUpdateTimer = setInterval(() => {
        loadSchedules().catch((err) => console.error('❌ Scheduled reload failed:', err));
    }, CONFIG.chartUpdateInterval);

    // Quick first refresh after 5 seconds to avoid long initial wait
    quickScheduleTimeout = setTimeout(() => {
        loadSchedules().catch((err) => console.error('❌ Quick reload failed:', err));
    }, 5000);
}

// Create slider controls for all channels
function createChannelControls(containerId = 'channelControls', includeAllChannels = true) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const channels = includeAllChannels ? 6 : 6;  // Always 6 channels

    container.innerHTML = '';

    for (let i = 0; i < channels; i++) {
        const control = document.createElement('div');
        control.className = 'channel-control';
        control.innerHTML = `
            <div class="channel-header">
                <span class="channel-name">${CONFIG.channelNames[i]}</span>
                <span class="channel-value" id="value-${containerId}-${i}">0%</span>
            </div>
            <div class="slider-container">
                <input type="range" 
                       class="slider" 
                       id="slider-${containerId}-${i}"
                       min="0" 
                       max="100" 
                       value="0"
                       style="--channel-color: ${CONFIG.channelColors[i]}">
            </div>
        `;

        container.appendChild(control);

        // Add event listener
        const slider = control.querySelector('.slider');
        const valueDisplay = control.querySelector('.channel-value');

        slider.addEventListener('input', (e) => {
            handleSliderInput(i, parseInt(e.target.value), containerId);
            updateSliderBackground(slider, e.target.value);
            valueDisplay.textContent = e.target.value + '%';
        });

        // Initialize slider background
        updateSliderBackground(slider, 0);
    }
}

// Update slider background gradient
function updateSliderBackground(slider, value) {
    slider.style.setProperty('--value', value + '%');
}

// Handle slider input with debouncing
function handleSliderInput(channel, value, containerId = 'channelControls') {
    // Update state
    state.channelValues[channel] = value;

    // If channels are linked, update all other channels
    if (state.linkChannels && containerId === 'channelControls') {
        for (let i = 0; i < 6; i++) {
            if (i !== channel) {
                updateSliderValue(i, value, containerId);
            }
        }
    }

    // Clear existing timer
    const timerKey = `${containerId}-${channel}`;
    if (sliderTimers[timerKey]) {
        clearTimeout(sliderTimers[timerKey]);
    }

    // Debounce: send update after slider stops moving
    if (state.testMode && containerId === 'channelControls') {
        sliderTimers[timerKey] = setTimeout(() => {
            sendTestUpdate(channel, value);

            // If linked, send updates for all channels
            if (state.linkChannels) {
                for (let i = 0; i < 6; i++) {
                    if (i !== channel) {
                        sendTestUpdate(i, value);
                    }
                }
            }
        }, CONFIG.sliderDebounceTime);
    }
}

// Update slider value programmatically
function updateSliderValue(channel, value, containerId = 'channelControls') {
    const slider = document.getElementById(`slider-${containerId}-${channel}`);
    const valueDisplay = document.getElementById(`value-${containerId}-${channel}`);

    if (slider) {
        slider.value = value;
        updateSliderBackground(slider, value);
    }
    if (valueDisplay) {
        valueDisplay.textContent = value + '%';
    }

    state.channelValues[channel] = value;
}

// Send test mode update to ESP
async function sendTestUpdate(channel, value) {
    try {
        await API.updateTestValue(channel, value);
        console.log(`✅ Test update sent: Channel ${channel} = ${value}%`);
    } catch (error) {
        console.error('❌ Test update failed:', error);
    }
}

// Load all schedules
async function loadSchedules() {
    try {
        console.log('📥 Loading schedules...');
        const data = await API.getAllSchedules();

        if (data.schedules) {
            state.schedules = data.schedules;
            mainChart.updateAll(data.schedules);
            console.log('✅ Schedules loaded');
        }
    } catch (error) {
        console.error('❌ Failed to load schedules:', error);
    }
}

// Load macros
async function loadMacros() {
    try {
        console.log('📥 Loading macros...');
        const data = await API.getMacros();

        if (data.macros) {
            // Load full details for each macro to get duration
            state.macros = await Promise.all(data.macros.map(async (macro) => {
                try {
                    const details = await API.getMacro(macro.id);
                    // Calculate duration from first channel's last target time
                    let duration = 3600; // Default 1 hour
                    if (details.channels && details.channels[0] && details.channels[0].targets.length > 0) {
                        const targets = details.channels[0].targets;
                        duration = targets[targets.length - 1].time;
                    }
                    return { ...macro, duration };
                } catch (err) {
                    console.warn(`⚠️ Could not load duration for ${macro.id}:`, err);
                    return { ...macro, duration: 3600 }; // Fallback to 1 hour
                }
            }));
            renderMacroList();
            console.log(`✅ ${state.macros.length} macros loaded`);
        }
    } catch (error) {
        console.error('❌ Failed to load macros:', error);
        document.getElementById('macroList').innerHTML =
            '<p class="loading">Fehler beim Laden der Makros</p>';
    }
}

// Render macro list
function renderMacroList() {
    const container = document.getElementById('macroList');

    if (state.macros.length === 0) {
        container.innerHTML = '<p class="loading">Keine Makros vorhanden</p>';
        return;
    }

    container.innerHTML = state.macros.map(macro => {
        const hours = Math.floor(macro.duration / 3600);
        const minutes = Math.floor((macro.duration % 3600) / 60);
        const durationText = hours > 0 ? `${hours}h ${minutes}min` : `${minutes}min`;

        return `
            <div class="macro-card" onclick="activateMacro('${macro.id}')">
                <h3>🎬 ${macro.name}</h3>
                <p class="macro-duration">⏱️ ${durationText}</p>
                <div class="macro-actions" onclick="event.stopPropagation()">
                    <button class="btn btn-small btn-primary" onclick="editMacro('${macro.id}')">
                        ✏️ Bearbeiten
                    </button>
                    <button class="btn btn-small btn-stop" onclick="deleteMacro('${macro.id}')">
                        🗑️ Löschen
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Activate macro
async function activateMacro(macroId) {
    if (state.macroActive) {
        if (!confirm('Ein Makro ist bereits aktiv. Trotzdem wechseln?')) {
            return;
        }
    }

    try {
        // Find macro duration from loaded macros
        const macro = state.macros.find(m => m.id === macroId);
        if (!macro || !macro.duration) {
            throw new Error('Makro-Dauer nicht gefunden');
        }

        await API.activateMacro(macroId, macro.duration);
        console.log(`✅ Macro activated: ${macroId} for ${macro.duration}s`);
    } catch (error) {
        console.error('❌ Macro activation failed:', error);
        alert('Fehler beim Aktivieren des Makros: ' + error.message);
    }
}

// Stop macro
async function stopMacro() {
    try {
        await API.stopMacro();
        console.log('✅ Macro stopped');
    } catch (error) {
        console.error('❌ Macro stop failed:', error);
    }
}

// Delete macro
async function deleteMacro(macroId) {
    const macro = state.macros.find(m => m.id === macroId);
    const displayName = macro ? macro.name : macroId;

    if (!confirm(`Makro "${displayName}" wirklich löschen?`)) {
        return;
    }

    try {
        await API.deleteMacro(macroId);
        console.log(`✅ Macro deleted: ${macroId}`);
        await loadMacros();
    } catch (error) {
        console.error('❌ Macro deletion failed:', error);
        alert('Fehler beim Löschen des Makros: ' + error.message);
    }
}

// Toggle test mode
async function toggleTestMode() {
    if (state.testMode) {
        await exitTestMode();
    } else {
        await startTestMode();
    }
}

// Start test mode
async function startTestMode() {
    try {
        await API.startTestMode();
        state.testMode = true;

        // Update UI
        document.getElementById('testBanner').classList.remove('hidden');
        document.getElementById('testModeBtn').textContent = '⚡ Test-Modus beenden';
        document.getElementById('testModeBtn').classList.add('btn-stop');
        document.getElementById('testModeBtn').classList.remove('btn-primary');

        console.log('✅ Test mode started');
    } catch (error) {
        console.error('❌ Test mode start failed:', error);
        alert('Fehler beim Starten des Test-Modus: ' + error.message);
    }
}

// Exit test mode
async function exitTestMode() {
    try {
        await API.exitTestMode();
        state.testMode = false;

        // Update UI
        document.getElementById('testBanner').classList.add('hidden');
        document.getElementById('testModeBtn').textContent = '⚡ Test-Modus starten';
        document.getElementById('testModeBtn').classList.remove('btn-stop');
        document.getElementById('testModeBtn').classList.add('btn-primary');

        console.log('✅ Test mode exited');
    } catch (error) {
        console.error('❌ Test mode exit failed:', error);
    }
}

// Add target at specific time
async function addTargetAtTime() {
    console.log('🔵 addTargetAtTime() called');
    const timeInput = document.getElementById('newTargetTime');
    const time = timeInput.value;
    console.log('🔵 Selected time:', time);

    if (!time) {
        alert('Bitte eine Zeit auswählen');
        return;
    }

    try {
        console.log('🔵 Adding targets for all channels...');
        // Add current slider values to this time for all channels
        for (let channel = 0; channel < 6; channel++) {
            console.log(`🔵 Channel ${channel}: value=${state.channelValues[channel]}`);
            await API.addTarget(channel, time, state.channelValues[channel]);
        }

        // Reload schedules
        await loadSchedules();

        console.log(`✅ Targets added at ${time}`);
        alert(`✅ Zeitpunkte gespeichert für ${time}`);
    } catch (error) {
        console.error('❌ Failed to add targets:', error);
        alert('Fehler beim Hinzufügen der Zeitpunkte: ' + error.message);
    }
}

// Save schedule
async function saveSchedule() {
    try {
        // Save all channels using densified sampled schedules from chart
        for (let channel = 0; channel < 6; channel++) {
            const targets = buildSampledTargetsForChannel(channel);
            await API.saveSchedule(channel, targets);
        }

        alert('Zeitplan gespeichert!');
        console.log('✅ Schedule saved');
    } catch (error) {
        console.error('❌ Schedule save failed:', error);
        alert('Fehler beim Speichern: ' + error.message);
    }
}

// Delete all schedules
async function deleteAllSchedules() {
    if (!confirm('Wirklich alle Zeitpläne löschen? Diese Aktion kann nicht rückgängig gemacht werden.')) {
        console.log('Delete operation cancelled by user');
        return;
    }

    try {
        await API.clearAllSchedules();

        // Clear the chart state
        for (let channel = 0; channel < 6; channel++) {
            state.schedules[channel] = [];
        }

        // Refresh the chart to show empty state
        await loadSchedules();

        alert('✅ Alle Zeitpläne wurden gelöscht!');
        console.log('✅ All schedules deleted');
    } catch (error) {
        console.error('❌ Schedule delete failed:', error);
        alert('Fehler beim Löschen: ' + error.message);
    }
}

// Build sanitized, capped target list from sampled chart data
function buildSampledTargetsForChannel(channel) {
    const MAX_TARGETS = 128; // align with ESP8266 firmware cap
    if (!mainChart || !mainChart.sampledSchedules) return [];
    const samples = mainChart.sampledSchedules[channel] || [];

    // Map to simple {time,value} and sanitize
    let targets = samples.map(p => ({
        time: Math.max(0, Math.min(86400, Math.round(p.x))),
        value: Math.max(0, Math.min(100, Math.round(p.y))),
        isControl: !!p.isControl
    }));

    // Sort by time ascending
    targets.sort((a, b) => a.time - b.time);

    // Remove duplicate times, keeping the last occurrence
    const unique = [];
    let lastTime = null;
    for (const t of targets) {
        if (t.time !== lastTime) {
            unique.push(t);
            lastTime = t.time;
        } else {
            // overwrite previous entry with latest value at same time
            unique[unique.length - 1] = t;
        }
    }

    // Cap to MAX_TARGETS
    if (unique.length > MAX_TARGETS) {
        unique = unique.slice(0, MAX_TARGETS);
    }

    return unique;
}

// Status updates
let statusUpdateTimer = null;

function startStatusUpdates() {
    updateStatus();  // Initial update
    statusUpdateTimer = setInterval(updateStatus, CONFIG.statusUpdateInterval);
}

async function updateStatus() {
    try {
        const data = await API.getStatus();

        // Update time
        if (data.time) {
            document.getElementById('time').textContent = data.time;
        }

        // Update temperature
        if (data.temperature !== undefined) {
            document.getElementById('temp').textContent = data.temperature.toFixed(1);
        }

        // Update test mode status
        if (data.test_mode !== state.testMode) {
            state.testMode = data.test_mode;
            if (data.test_mode) {
                document.getElementById('testBanner').classList.remove('hidden');
            } else {
                document.getElementById('testBanner').classList.add('hidden');
            }
        }

        // Update macro status
        if (data.macro_active !== state.macroActive) {
            state.macroActive = data.macro_active;

            if (data.macro_active) {
                state.activeMacro = data.macro_id || 'Unknown';
                document.getElementById('macroName').textContent = data.macro_id || 'Macro';
                document.getElementById('macroBanner').classList.remove('hidden');
            } else {
                document.getElementById('macroBanner').classList.add('hidden');
            }
        }

        // Update macro timer (use macro_expires_in from server)
        if (state.macroActive && data.macro_expires_in !== undefined) {
            const remaining = data.macro_expires_in;

            if (remaining > 0) {
                const mins = Math.floor(remaining / 60);
                const secs = remaining % 60;
                document.getElementById('macroRemaining').textContent =
                    `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            } else {
                document.getElementById('macroRemaining').textContent = '00:00';
            }
        }

    } catch (error) {
        console.error('❌ Status update failed:', error);
        document.getElementById('wifiStatus').textContent = '📶 Verbindungsfehler';
    }
}

// Macro Wizard
let wizardMode = 'create';  // 'create' or 'edit'
let wizardMacroName = null;
let wizardDurationSeconds = 0;
let wizardMacroId = null;

function showMacroWizard() {
    wizardMode = 'create';
    wizardMacroId = null;
    document.getElementById('macroWizard').classList.remove('hidden');
    document.getElementById('wizardStep1').classList.remove('hidden');
    document.getElementById('wizardStep2').classList.add('hidden');

    // Reset form
    document.getElementById('wizardMacroNameInput').value = '';
    document.getElementById('macroDurationHours').value = '2';
    document.getElementById('macroDurationMinutes').value = '0';
    const addTime = document.getElementById('macroAddTime');
    if (addTime) {
        addTime.value = '05:00';
    }
}

function closeMacroWizard() {
    document.getElementById('macroWizard').classList.add('hidden');

    // Cleanup macro chart
    if (macroChart) {
        macroChart.destroy();
        macroChart = null;
    }
}

function wizardNext() {
    const name = document.getElementById('wizardMacroNameInput').value.trim();
    const hours = parseInt(document.getElementById('macroDurationHours').value) || 0;
    const minutes = parseInt(document.getElementById('macroDurationMinutes').value) || 0;

    if (!name) {
        alert('Bitte einen Namen eingeben');
        return;
    }

    const duration = (hours * 3600) + (minutes * 60);
    wizardDurationSeconds = duration;
    if (duration < 60) {
        alert('Dauer muss mindestens 1 Minute betragen');
        return;
    }

    wizardMacroName = name;

    // Show step 2
    document.getElementById('wizardStep1').classList.add('hidden');
    document.getElementById('wizardStep2').classList.remove('hidden');

    // Initialize macro chart with custom duration
    if (!macroChart) {
        createChannelControls('macroChannelControls', true);
        macroChart = new ChartManager('macroChart', true, duration);  // Pass duration as max seconds
        macroChart.init();

        // Initialize with simple start/end pattern
        for (let i = 0; i < 6; i++) {
            macroChart.updateChannel(i, [
                { time: 0, value: 0, isControl: true },
                { time: duration, value: 0, isControl: true }
            ]);
        }
    }
}

function wizardBack() {
    document.getElementById('wizardStep1').classList.remove('hidden');
    document.getElementById('wizardStep2').classList.add('hidden');
}

async function saveMacro() {
    const name = document.getElementById('wizardMacroNameInput').value.trim();
    const hours = parseInt(document.getElementById('macroDurationHours').value) || 0;
    const minutes = parseInt(document.getElementById('macroDurationMinutes').value) || 0;
    const duration = (hours * 3600) + (minutes * 60);

    const macroId = (wizardMode === 'edit' && wizardMacroId)
        ? wizardMacroId
        : (name ? name.toLowerCase().replace(/\s+/g, '_') : '');

    if (!macroId) {
        alert('Bitte einen Makro-Namen eingeben.');
        return;
    }

    // Get channel schedules from macro chart
    const channels = (macroChart.sampledSchedules || []).map((schedule, i) => ({
        channel: i,
        targets: schedule.map(point => ({
            time: point.x,
            value: point.y,
            isControl: !!point.isControl
        }))
    }));

    try {
        await API.saveMacro(macroId, name, duration, channels);
        console.log(`✅ Macro saved: ${name}`);

        closeMacroWizard();
        await loadMacros();

        alert(`Makro "${name}" erfolgreich gespeichert!`);
    } catch (error) {
        console.error('❌ Macro save failed:', error);
        alert('Fehler beim Speichern des Makros: ' + error.message);
    }
}

function parseMacroTimeInput(value) {
    if (!value || typeof value !== 'string') return null;
    const parts = value.split(':');
    if (parts.length !== 2) return null;

    const mins = parseInt(parts[0], 10);
    const secs = parseInt(parts[1], 10);

    if (Number.isNaN(mins) || Number.isNaN(secs)) return null;
    if (mins < 0 || secs < 0 || secs >= 60) return null;

    return (mins * 60) + secs;
}

// Add a macro timestamp using the current slider values
function addMacroTimestamp() {
    if (!macroChart) {
        alert('Bitte zuerst den Makro-Assistenten starten.');
        return;
    }

    const timeInput = document.getElementById('macroAddTime');
    const timeStr = timeInput ? timeInput.value.trim() : '';
    const seconds = parseMacroTimeInput(timeStr);

    if (seconds === null) {
        alert('Bitte eine Zeit im Format MM:SS eingeben.');
        return;
    }

    const hours = parseInt(document.getElementById('macroDurationHours').value) || 0;
    const minutes = parseInt(document.getElementById('macroDurationMinutes').value) || 0;
    const duration = (hours * 3600) + (minutes * 60);

    if (seconds > duration) {
        alert('Zeitpunkt liegt außerhalb der Makro-Dauer.');
        return;
    }

    for (let channel = 0; channel < 6; channel++) {
        let controls = (macroChart.controlSchedules[channel] || []).filter(p => p.isControl);
        if (controls.length === 0) {
            controls = (macroChart.sampledSchedules[channel] || []).map(p => ({ x: p.x, y: p.y, isControl: true }));
        }

        // Replace existing entry at this time if present
        const next = controls.filter(p => Math.round(p.x) !== Math.round(seconds));
        next.push({ x: seconds, y: state.channelValues[channel], isControl: true });
        next.sort((a, b) => a.x - b.x);

        macroChart.updateChannel(channel, next.map(p => ({ time: p.x, value: p.y, isControl: true })));
    }

    console.log(`✅ Makro-Zeitpunkt hinzugefügt bei ${timeStr}`);
}

// Edit existing macro
async function editMacro(macroId) {
    try {
        const data = await API.getMacro(macroId);

        // Populate form
        document.getElementById('wizardMacroNameInput').value = data.name || macroId;
        const hours = Math.floor(data.duration / 3600);
        const minutes = Math.floor((data.duration % 3600) / 60);
        document.getElementById('macroDurationHours').value = hours;
        document.getElementById('macroDurationMinutes').value = minutes;

        wizardMode = 'edit';
        wizardMacroName = data.name || macroId;
        wizardMacroId = macroId;
        wizardDurationSeconds = data.duration;  // Store duration for chart

        // Go directly to step 2
        document.getElementById('macroWizard').classList.remove('hidden');
        document.getElementById('wizardStep1').classList.add('hidden');
        document.getElementById('wizardStep2').classList.remove('hidden');

        // Initialize chart with existing data and custom duration
        createChannelControls('macroChannelControls', true);
        macroChart = new ChartManager('macroChart', true, data.duration);  // Pass duration
        macroChart.init();

        // Load existing schedule
        data.channels.forEach(ch => {
            macroChart.updateChannel(ch.channel, ch.targets);
        });

    } catch (error) {
        console.error('❌ Failed to load macro:', error);
        alert('Fehler beim Laden des Makros: ' + error.message);
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', init);

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (statusUpdateTimer) {
        clearInterval(statusUpdateTimer);
    }
});
