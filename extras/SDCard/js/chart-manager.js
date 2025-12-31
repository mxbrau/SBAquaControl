// Chart.js Manager
// NOTE: This manager uses LINEAR interpolation only (no spline smoothing)
// to match the firmware's simple linear PWM interpolation algorithm.
// The firmware does: pwmValue = lastTarget.value + (nextTarget.value - lastTarget.value) * progress
// This UI replicates that exact behavior.
class ChartManager {
    constructor(canvasId, isTimeRange = false) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.isTimeRange = isTimeRange;
        this.chart = null;
        this.controlSchedules = Array(6).fill(null).map(() => []); // control points (user-defined only)
        this.sampledSchedules = Array(6).fill(null).map(() => []);  // LINEAR samples between control points (NO smoothing)
        this.samplesPerSegmentDefault = 2; // LINEAR only: just start and end point per segment
        this.maxTargetsPerChannel = 32;    // align with new firmware cap (was 128, reduced for ESP8266 RAM)
    }

    // Initialize the chart
    init() {
        const datasets = CONFIG.channelNames.map((name, i) => ({
            label: name,
            data: [],
            borderColor: CONFIG.channelColors[i],
            backgroundColor: CONFIG.channelColors[i] + '20',
            borderWidth: 3,
            tension: 0, // pure linear segments to mirror hardware PWM interpolation
            pointRadius: (ctx) => ctx.raw && ctx.raw.isControl ? 5 : 0,
            pointHoverRadius: (ctx) => ctx.raw && ctx.raw.isControl ? 7 : 0,
            fill: false
        }));

        this.chart = new Chart(this.ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'nearest',
                    intersect: true
                },
                plugins: {
                    legend: {
                        display: false  // We'll use custom legend
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `${context.dataset.label}: ${context.parsed.y}%`;
                            },
                            title: (items) => {
                                if (this.isTimeRange) {
                                    const seconds = items[0].parsed.x;
                                    const mins = Math.floor(seconds / 60);
                                    const secs = seconds % 60;
                                    return `${mins}:${secs.toString().padStart(2, '0')}`;
                                } else {
                                    return this.formatTime(items[0].parsed.x);
                                }
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        min: 0,
                        max: this.isTimeRange ? 7200 : 86400,  // 2 hours or 24 hours
                        ticks: {
                            callback: (value) => this.formatTime(value)
                        },
                        title: {
                            display: true,
                            text: 'Zeit'
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            callback: (value) => value + '%'
                        },
                        title: {
                            display: true,
                            text: 'Helligkeit'
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (!this.isTimeRange) {
                        this.handleChartClick(event, elements);
                    }
                }
            }
        });

        this.updateLegend();
    }

    // Format seconds to time string
    formatTime(seconds) {
        if (this.isTimeRange) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        }
    }

    // Parse time string to seconds
    parseTime(timeStr) {
        const parts = timeStr.split(':');
        return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60;
    }

    // Update schedule data for a specific channel
    updateChannel(channel, targets) {
        // Normalize incoming targets
        let points = (targets || []).map(t => ({
            x: typeof t.time === 'string' ? this.parseTime(t.time) : t.time,
            y: t.value,
            isControl: t.isControl === true
        }));
        points.sort((a, b) => a.x - b.x);

        // Determine whether incoming points already include sampled curve
        const controlPointsPresent = points.some(p => p.isControl === true);
        let controlPoints;
        let samples;

        if (controlPointsPresent) {
            // Use control points as the authoritative shape and resample
            controlPoints = points.filter(p => p.isControl);

            if (!this.isTimeRange && controlPoints.length > 0) {
                const first = controlPoints[0];
                const last = controlPoints[controlPoints.length - 1];

                if (first.x > 0) {
                    controlPoints.unshift({ x: 0, y: last.y, isControl: false });
                }
                if (last.x < 86400) {
                    controlPoints.push({ x: 86400, y: last.y, isControl: false });
                }
            }

            samples = this.generateMonotoneSamples(controlPoints);
        } else {
            // No control points flagged: treat as pre-sampled
            controlPoints = [];
            samples = points;
        }

        this.controlSchedules[channel] = controlPoints;
        this.sampledSchedules[channel] = samples;
        this.chart.data.datasets[channel].data = samples;
        this.chart.update('none');
    }

    // Update all channels
    updateAll(schedules) {
        schedules.forEach(schedule => {
            if (schedule && schedule.targets) {
                this.updateChannel(schedule.channel, schedule.targets);
            }
        });
    }

    // Get current values at specific time
    getValuesAtTime(time) {
        const values = [];
        for (let channel = 0; channel < 6; channel++) {
            values.push(this.interpolateValue(channel, time));
        }
        return values;
    }

    // Interpolate value at specific time
    interpolateValue(channel, time) {
        const schedule = this.sampledSchedules[channel];
        if (schedule.length === 0) return 0;
        if (schedule.length === 1) return schedule[0].y;

        // Find surrounding points
        let before = schedule[0];
        let after = schedule[schedule.length - 1];

        for (let i = 0; i < schedule.length - 1; i++) {
            if (schedule[i].x <= time && schedule[i + 1].x >= time) {
                before = schedule[i];
                after = schedule[i + 1];
                break;
            }
        }

        // Linear interpolation
        const dt = after.x - before.x;
        if (dt === 0) return before.y;

        const dv = after.y - before.y;
        const progress = (time - before.x) / dt;
        return Math.round(before.y + (dv * progress));
    }

    // Handle chart click (add/remove points)
    handleChartClick(event, elements) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;

        // Get time from click position using chart scales
        const chartArea = this.chart.chartArea;
        const xScale = this.chart.scales.x;
        const clickTime = Math.round(xScale.getValueForPixel(x));

        if (clickTime < 0 || clickTime > 86400) return;

        // If clicked on existing point, offer to delete
        if (elements.length > 0) {
            const element = elements[0];
            const channel = element.datasetIndex;
            const schedule = this.sampledSchedules[channel];
            const rawPoint = schedule && schedule[element.index];

            // Only allow deletion on actual control points
            if (rawPoint && rawPoint.isControl) {
                const pointTime = rawPoint.x;
                if (confirm(`Zeitpunkt ${this.formatTime(pointTime)} für ${CONFIG.channelNames[channel]} löschen?`)) {
                    this.removePoint(channel, pointTime);
                }
            }
        }
    }

    // Remove a point from schedule
    async removePoint(channel, pointTime) {
        try {
            // Update local control points first to avoid spikes
            const existing = this.controlSchedules[channel] || [];
            const userControls = existing.filter(p => p.isControl);
            const nextControls = userControls.filter(p => Math.round(p.x) !== Math.round(pointTime));

            // Rebuild working control list with wrap-around
            let working = nextControls.slice().sort((a, b) => a.x - b.x);
            if (!this.isTimeRange && working.length > 0) {
                const first = working[0];
                const last = working[working.length - 1];
                if (first.x > 0) working.unshift({ x: 0, y: last.y, isControl: false });
                if (last.x < 86400) working.push({ x: 86400, y: last.y, isControl: false });
            }

            const samples = this.generateMonotoneSamples(working);
            this.controlSchedules[channel] = working;
            this.sampledSchedules[channel] = samples;
            this.chart.data.datasets[channel].data = samples;
            this.chart.update('none');

            // Propagate deletion to server (control point only)
            await API.deleteTarget(channel, pointTime);

            // Optional: persist the recomputed sampled schedule
            const targets = samples.map(p => ({
                time: Math.max(0, Math.min(86400, Math.round(p.x))),
                value: Math.max(0, Math.min(100, Math.round(p.y))),
                isControl: !!p.isControl
            }));
            await API.saveSchedule(channel, targets);
        } catch (error) {
            alert('Fehler beim Löschen des Zeitpunkts: ' + error.message);
        }
    }

    // Update custom legend
    updateLegend() {
        const legendDiv = document.getElementById('chartLegend');
        if (!legendDiv) return;

        legendDiv.innerHTML = CONFIG.channelNames.map((name, i) => `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${CONFIG.channelColors[i]}"></div>
                <span>${name}</span>
            </div>
        `).join('');
    }

    // Destroy chart (for cleanup)
    destroy() {
        if (this.chart) {
            this.chart.destroy();
        }
    }

    // Generate LINEAR samples along the control points, with NO spline smoothing
    // This matches the firmware's simple linear interpolation: y = y0 + (y1 - y0) * progress
    // samplesPerSegment ignored for linear mode (always 2: start + end per segment)
    generateMonotoneSamples(points, samplesPerSegment) {
        if (!points || points.length === 0) return [];
        if (points.length === 1) return [{ ...points[0], isControl: true }];

        // For linear interpolation, we only need control points
        // Chart.js will draw straight lines between them
        // Mark all as control points so they show up as markers in the chart
        const samples = points.map(p => ({
            x: p.x,
            y: p.y,
            isControl: p.isControl !== false  // preserve isControl flag
        }));

        return samples;
    }
}
