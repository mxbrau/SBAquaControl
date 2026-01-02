// Example JavaScript code for integrating time-setting API into web UI
// This can be added to extras/SDCard/js/api.js or a new time-settings.js file

/**
 * Sets the device time via POST /api/time/set
 * @param {number} hour - Hour (0-23)
 * @param {number} minute - Minute (0-59)
 * @param {number} second - Second (0-59)
 * @returns {Promise<Object>} Response with status and time
 */
async function setDeviceTime(hour, minute, second) {
    try {
        const response = await fetch('/api/time/set', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                hour: hour,
                minute: minute,
                second: second
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to set time');
        }

        return await response.json();
    } catch (error) {
        console.error('Error setting device time:', error);
        throw error;
    }
}

/**
 * Set device time from browser's current time
 */
async function syncTimeToBrowser() {
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const second = now.getSeconds();
    
    try {
        const result = await setDeviceTime(hour, minute, second);
        console.log('Time synchronized:', result.time);
        alert(`Zeit erfolgreich auf ${result.time} gesetzt`);
        return result;
    } catch (error) {
        alert(`Fehler beim Setzen der Zeit: ${error.message}`);
        throw error;
    }
}

/**
 * Set device time from user input (form fields)
 * Assumes HTML elements with IDs: time-hour, time-minute, time-second
 */
async function setTimeFromForm() {
    const hour = parseInt(document.getElementById('time-hour').value, 10);
    const minute = parseInt(document.getElementById('time-minute').value, 10);
    const second = parseInt(document.getElementById('time-second').value, 10);

    // Validate input
    if (isNaN(hour) || hour < 0 || hour > 23) {
        alert('Ungültige Stunde (0-23)');
        return;
    }
    if (isNaN(minute) || minute < 0 || minute > 59) {
        alert('Ungültige Minute (0-59)');
        return;
    }
    if (isNaN(second) || second < 0 || second > 59) {
        alert('Ungültige Sekunde (0-59)');
        return;
    }

    try {
        const result = await setDeviceTime(hour, minute, second);
        console.log('Time set successfully:', result.time);
        alert(`Zeit erfolgreich auf ${result.time} gesetzt`);
        return result;
    } catch (error) {
        alert(`Fehler beim Setzen der Zeit: ${error.message}`);
        throw error;
    }
}

// Example HTML for time setting form:
/*
<div class="time-settings">
    <h3>⏰ Zeit einstellen</h3>
    <div class="form-group">
        <label>Stunde (0-23):</label>
        <input type="number" id="time-hour" min="0" max="23" value="12">
    </div>
    <div class="form-group">
        <label>Minute (0-59):</label>
        <input type="number" id="time-minute" min="0" max="59" value="0">
    </div>
    <div class="form-group">
        <label>Sekunde (0-59):</label>
        <input type="number" id="time-second" min="0" max="59" value="0">
    </div>
    <button onclick="setTimeFromForm()">Zeit setzen</button>
    <button onclick="syncTimeToBrowser()">Mit Browser synchronisieren</button>
</div>
*/
