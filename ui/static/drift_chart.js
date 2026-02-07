/**
 * TIRS Dashboard - Drift Chart Component
 * Chart.js wrapper for drift visualization
 */

class DriftChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.chart = null;
        
        // Threshold lines
        this.thresholds = {
            warning: 0.3,
            danger: 0.6,
            critical: 0.8
        };
    }

    /**
     * Create or update the drift chart
     * @param {string} agentId - Agent identifier
     * @param {string[]} labels - Time labels
     * @param {number[]} scores - Drift scores
     */
    update(agentId, labels, scores) {
        if (this.chart) {
            this.chart.destroy();
        }

        // Calculate point colors based on score
        const pointColors = scores.map(score => {
            if (score >= this.thresholds.critical) return '#ff0000';
            if (score >= this.thresholds.danger) return '#ff6b6b';
            if (score >= this.thresholds.warning) return '#ffa500';
            return '#00ff88';
        });

        this.chart = new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `Drift Score - ${agentId}`,
                    data: scores,
                    borderColor: '#00f5ff',
                    backgroundColor: 'rgba(0, 245, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: pointColors,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#e0e0e0' }
                    },
                    annotation: {
                        annotations: {
                            warningLine: {
                                type: 'line',
                                yMin: this.thresholds.warning,
                                yMax: this.thresholds.warning,
                                borderColor: '#ffa500',
                                borderWidth: 1,
                                borderDash: [5, 5],
                                label: {
                                    content: 'Warning',
                                    display: true,
                                    position: 'end'
                                }
                            },
                            dangerLine: {
                                type: 'line',
                                yMin: this.thresholds.danger,
                                yMax: this.thresholds.danger,
                                borderColor: '#ff6b6b',
                                borderWidth: 1,
                                borderDash: [5, 5],
                                label: {
                                    content: 'Danger',
                                    display: true,
                                    position: 'end'
                                }
                            },
                            criticalLine: {
                                type: 'line',
                                yMin: this.thresholds.critical,
                                yMax: this.thresholds.critical,
                                borderColor: '#ff0000',
                                borderWidth: 1,
                                borderDash: [5, 5],
                                label: {
                                    content: 'Critical',
                                    display: true,
                                    position: 'end'
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 1,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { 
                            color: '#e0e0e0',
                            callback: function(value) {
                                return (value * 100).toFixed(0) + '%';
                            }
                        },
                        title: {
                            display: true,
                            text: 'Risk Score',
                            color: '#a0a0a0'
                        }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#e0e0e0' },
                        title: {
                            display: true,
                            text: 'Time',
                            color: '#a0a0a0'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    /**
     * Destroy the chart instance
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DriftChart;
}
