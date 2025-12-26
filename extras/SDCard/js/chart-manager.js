// Chart.js Manager
class ChartManager {
    constructor(canvasId, isTimeRange = false) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.isTimeRange = isTimeRange;
        this.chart = null;
        this.controlSchedules = Array(6).fill(null).map(() => []); // control points (user-defined + wrap)
        this.sampledSchedules = Array(6).fill(null).map(() => []);  // densified samples following the PWM
        this.samplesPerSegmentDefault = 64; // higher density for smoother curve
        this.maxTargetsPerChannel = 128;    // align with firmware cap
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

    // Generate monotone cubic samples along the control points, returning dense points with flags
    generateMonotoneSamples(points, samplesPerSegment) {
        if (!points || points.length === 0) return [];
        if (points.length === 1) return [{ ...points[0], isControl: true }];

        // Decide actual samples per segment to stay within maxTargetsPerChannel budget
        const segments = Math.max(1, points.length - 1);
        const targetPerSegCap = Math.max(1, Math.floor((this.maxTargetsPerChannel - 1) / segments));
        const perSeg = Math.min(samplesPerSegment || this.samplesPerSegmentDefault, targetPerSegCap);

        // Precompute slopes and tangents (monotone cubic Hermite)
        const n = points.length;
        const d = new Array(n - 1);
        const m = new Array(n);

        for (let i = 0; i < n - 1; i++) {
            const dx = points[i + 1].x - points[i].x;
            const dy = points[i + 1].y - points[i].y;
            d[i] = dy / dx;
        }

        m[0] = d[0];
        m[n - 1] = d[n - 2];
        for (let i = 1; i < n - 1; i++) {
            if (d[i - 1] * d[i] <= 0) {
                m[i] = 0;
            } else {
                m[i] = (d[i - 1] + d[i]) / 2;
            }
        }

        // Adjust tangents to preserve monotonicity
        for (let i = 0; i < n - 1; i++) {
            if (d[i] === 0) {
                m[i] = 0;
                m[i + 1] = 0;
            } else {
                const a = m[i] / d[i];
                const b = m[i + 1] / d[i];
                const h = Math.hypot(a, b);
                if (h > 3) {
                    const t = 3 / h;
                    m[i] = t * a * d[i];
                    m[i + 1] = t * b * d[i];
                }
            }
        }

        const samples = [];
        for (let i = 0; i < n - 1; i++) {
            const p0 = points[i];
            const p1 = points[i + 1];
            const dx = p1.x - p0.x;
            const dy = p1.y - p0.y;

            // push the start point of the segment
            samples.push({ ...p0 });

            for (let s = 1; s <= perSeg; s++) {
                const t = s / perSeg;
                const h00 = (2 * t ** 3) - (3 * t ** 2) + 1;
                const h10 = t ** 3 - (2 * t ** 2) + t;
                const h01 = (-2 * t ** 3) + (3 * t ** 2);
                const h11 = t ** 3 - t ** 2;

                const y = h00 * p0.y + h10 * dx * m[i] + h01 * p1.y + h11 * dx * m[i + 1];
                const x = p0.x + t * dx;

                // skip the exact end point; it will be added as start of next segment
                if (s < perSeg) {
                    samples.push({ x, y, isControl: false });
                }
            }
        }

        // push final control point
        samples.push({ ...points[n - 1] });

        return samples;
    }
}
