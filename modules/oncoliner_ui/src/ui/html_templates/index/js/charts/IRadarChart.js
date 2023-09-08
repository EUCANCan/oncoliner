/**
 * @typedef {import('chartjs-plugin-datalabels').Context} ChartDataLabelsContext
 * @typedef {import('chart.js').Chart} Chart
 * @typedef {import('chart.js').ChartConfiguration} ChartConfiguration
 * @typedef {import('chart.js').ChartDataset} ChartDataset
 */

/**
 * @param {string[]} labels
 * @param {ChartDataset[]} datasets
 * @param {string} title
 * @param {HTMLCanvasElement} ctx
 * @returns {Chart}
 */
function buildRadarChart(labels, datasets, title, ctx) {
    /** @type {ChartConfiguration} */
    const config = {
        type: "radar",
        data: {
            labels: labels,
            datasets: datasets,
        },
        // @ts-ignore
        plugins: [ChartDataLabels],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        display: false,
                    },
                    min: 0,
                    max: 1.1, // For extra space at the top
                    ticks: {
                        stepSize: 0.25,
                        backdropColor: "rgba(0, 0, 0, 0)",
                        // Skip last tick
                        callback: (value, index, values) =>
                            index < values.length - 1
                                // @ts-ignore
                                ? `${value.toFixed(2)}                  `
                                : null,
                    },
                },
            },
            plugins: {
                title: {
                    display: true,
                    text: title,
                },
                tooltip: {
                    mode: "index",
                },
                legend: {
                    display: true,
                    position: "top",
                },
            },
        },
    };

    // @ts-ignore
    const chart = /** @type {Chart} */ (new Chart(ctx, config));
    return chart;
}