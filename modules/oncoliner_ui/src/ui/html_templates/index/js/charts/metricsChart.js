/**
 * @typedef {Object} ChartData
 * @property {string} xLabel1
 * @property {string} xLabel2
 * @property {number} tp
 * @property {number} fp
 * @property {number} fn
 * @property {number} recall
 * @property {number} precision
 * @property {string} axisId
 */

/**
 * @param {string} htmlContainerId
 * @param {ChartData[]} chartData
 * @param {string} title
 */
function createMetricsPlot(htmlContainerId, chartData, title) {
    const htmlContainer = /** @type {HTMLElement} */ (document.querySelector(`#${htmlContainerId}`));
    // Count unique axis ids in chartData
    const axisIds = chartData.map((d) => d.axisId);
    const uniqueAxisIds = [...new Set(axisIds)];
    // Get number of columns
    const columnCount = chartData.length + uniqueAxisIds.length + 3;
    // 18 columns is 100% width of the chart
    // Adapt width of the htmlContainer to the number of columns
    const width = Math.round((columnCount / 18) * 100);
    htmlContainer.style.width = `${width}%`;
    htmlContainer.style.height = `100%`;
    const ctx = /** @type {HTMLCanvasElement} */ (htmlContainer.querySelector("canvas"));
    const chart = _buildMetricsChart(ctx, chartData, title);
    return {
        getBase64Images : () => [chart.getBase64Image()],
        getCanvas: () => {return ctx}
    }
}

/**
 * @param {HTMLCanvasElement} ctx
 * @param {ChartData[]} chartData
 */
function _buildMetricsChart(ctx, chartData, title) {
    const STEP_COUNT = 10;
    const TP_LABEL = "True positives";
    const FP_LABEL = "False positives";
    // const FN_LABEL = "False negatives";
    const RECALL_LABEL = "Recall";
    const PRECISION_LABEL = "Precision";
    const TRUTH_LABEL = "Total true variants";
    // The order must be Recall, Truth, FN, FP, TP, Precision
    let legendLabels = [
        RECALL_LABEL,
        TRUTH_LABEL,
        TP_LABEL,
        FP_LABEL,
        PRECISION_LABEL,
    ];

    // Style
    const TP_COLOR = "#228833";
    const FP_COLOR = "#EE6677";
    // const FN_COLOR = "#4477AA70";
    const TRUTH_BORDER_DASH = [5, 5];
    const TRUTH_BORDER_COLOR = "#0000009f";

    const scales = {
        x: {
            title: {
                display: true,
                text: "Variant sizes (bp)",
            },
            position: "bottom",
            stacked: true,
            offset: false,
            grid: {
                display: false,
            },
            ticks: {
                callback: function (value, index, values) {
                    const originalLabel = this.getLabelForValue(value);
                    if (originalLabel)
                        return originalLabel.split(";")[1].trim();
                    else return "";
                },
            },
        },
        x2: {
            title: {
                display: true,
                text: "Variant types",
            },
            position: "top",
            offset: false,
            grid: {
                display: false,
            },
            ticks: {
                callback: function (value, index, values) {
                    const originalLabel = this.getLabelForValue(value);
                    if (originalLabel)
                        return originalLabel.split(";")[0].trim();
                    else return "";
                },
            },
        },
        yAxisExtra: {
            axis: "y",
            position: "right",
            display: false,
        },
    };
    // Fill datasets, labels and scales
    const datasets = [];
    const labels = [];
    let showPrecision = false;
    let showFP = false;
    let firstAxis = undefined;
    for (let i = 0, x = 0, currAxisId = ""; i < chartData.length; i++, x++) {
        const data = chartData[i];
        const yAxisID = `yAxis${data.axisId}`;
        const yAxisIDTruth = `yAxis${data.axisId}Truth`;
        // Add new scale
        if (data.axisId !== currAxisId) {
            if (firstAxis === undefined) firstAxis = yAxisID;
            // Calculate max value for this axis
            const truthValues = chartData
                .filter((d) => d.axisId === data.axisId)
                .map((d) => d.tp + d.fn);
            const fpValues = chartData
                .filter((d) => d.axisId === data.axisId)
                .map((d) => d.fp);
            let maxValue = Math.max(...truthValues, ...fpValues);
             // Add step value to make sure the tags are visible
            maxValue += maxValue / STEP_COUNT;
            // Calculate max value for this axis to be multiple of STEP_COUNT
            const maxAxisValue = Math.ceil(maxValue / STEP_COUNT) * (STEP_COUNT);
            // Add empty label to make sure the axis is visible
            labels.push(undefined);
            currAxisId = data.axisId;
            scales[yAxisID] = {
                axis: "y",
                title: {
                    display: x == 0,
                    text: "Number of variants",
                },
                stacked: true,
                position: x == 0 ? "left" : { x: x },
                grid: {
                    display: x == 0,
                },
                min: -maxAxisValue,
                max: maxAxisValue,
                ticks: {
                    callback: function (value, index, values) {
                        if (value == 0 && firstAxis !== this.id)
                            return undefined;
                        else return Math.abs(value);
                    },
                    align: "end",
                    count: STEP_COUNT + 1,
                },
            };
            scales[yAxisIDTruth] = {
                axis: "y",
                position: {
                    x,
                },
                min: -maxAxisValue,
                max: maxAxisValue,
                count: STEP_COUNT + 1,
                display: false,
            };
            x++;
        }
        labels.push(data.xLabel1 + "; " + data.xLabel2);
        // Fill data with as undefined as x
        const dataTP = new Array(x).fill(undefined);
        dataTP.push(data.tp);
        const dataFP = new Array(x).fill(undefined);
        dataFP.push(-data.fp);
        // const dataFN = new Array(x).fill(undefined);
        // dataFN.push(data.fn);
        const dataTruth = new Array(x).fill(undefined);
        dataTruth.push(data.tp + data.fn);
        datasets.push({
            label: TRUTH_LABEL,
            data: dataTruth,
            backgroundColor: "#00000000",
            borderWidth: 1.5,
            borderColor: "#00000000", // Hide it because it will be overriden by the borderDash
            yAxisID: yAxisIDTruth,
            borderDash: TRUTH_BORDER_DASH,
            datalabels: {
                display: true,
                anchor: "end",
                align: "top",
                formatter: function (value, context) {
                    if (value == undefined) return undefined;
                    else if (data.recall < 0) return '';
                    else return data.recall.toFixed(3);
                },
                offset: -2,
            },
        });
        if (data.fp >= 0) {
            showFP = true;
            if (data.precision >= 0) showPrecision = true;
            datasets.push({
                label: FP_LABEL,
                data: dataFP,
                backgroundColor: FP_COLOR,
                yAxisID,
                datalabels: {
                    display: true,
                    anchor: "start",
                    align: "bottom",
                    formatter: function (value, context) {
                        if (value == undefined) return undefined;
                        else if (data.precision < 0) return '';
                        else return data.precision.toFixed(3);
                    },
                    offset: -2,
                },
            });
        }
        datasets.push({
            label: TP_LABEL,
            data: dataTP,
            backgroundColor: TP_COLOR,
            yAxisID,
        });
        // datasets.push({
        //     label: FN_LABEL,
        //     data: dataFN,
        //     backgroundColor: FN_COLOR,
        //     yAxisID,
        // });
    }
    // Remove from legend the labels that are not shown
    if (!showFP) legendLabels = legendLabels.filter((l) => l !== FP_LABEL);
    if (!showPrecision) legendLabels = legendLabels.filter((l) => l !== PRECISION_LABEL);
    // Add empty Recall and Precision datasets
    if (showPrecision) {
        datasets.unshift({
            label: PRECISION_LABEL,
            data: 0,
            backgroundColor: "#00000000",
            yAxisID: "yAxisExtra",
        });
    }
    datasets.unshift({
        label: RECALL_LABEL,
        data: 0,
        backgroundColor: "#00000000",
        yAxisID: "yAxisExtra",
    });
    // Add empty label to make sure the last bar is visible
    labels.push(undefined);
    const chart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: datasets,
        },
        plugins: [
            ChartDataLabels,
            {
                afterDatasetDraw: function (chart, args, options) {
                    if (args.meta.label != TRUTH_LABEL) return;

                    // Draw the TRUTH_LABEL bar border a dashed line
                    args.meta.data.forEach((element) => {
                        const { x, y, width, base } = element.getProps(
                            ["x", "y", "width", "base"],
                            false
                        );
                        if (Number.isNaN(x) || y == base) return;

                        const ctx = chart.ctx;
                        const half = width / 2;
                        const top = y;
                        const bottom = base;
                        const left = x - half;
                        const right = x + half;
                        
                        ctx.save();
                        ctx.beginPath();
                        ctx.lineWidth = element.options.borderWidth;
                        ctx.strokeStyle = TRUTH_BORDER_COLOR;
                        ctx.setLineDash([5, 5]);

                        ctx.moveTo(left, bottom);
                        ctx.lineTo(left, top);
                        ctx.lineTo(right, top);
                        ctx.lineTo(right, bottom);
                        ctx.stroke();
                        ctx.restore();
                    });
                },
            },
        ],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 18,
                        weight: "bold",
                    }
                },
                datalabels: {
                    display: false,
                    color: "black",
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            if (context.parsed.y === null) return null;
                            let label = context.dataset.label || "";
                            if (label) {
                                label += ": ";
                            }
                            if (context.parsed.y !== null) {
                                label += Math.abs(context.parsed.y); // Avoid negative values in FP
                            }
                            return label;
                        },
                    },
                },
                legend: {
                    display: true,
                    maxWidth: 200,
                    position: "right",
                    onClick: function (e, legendItem) {
                        // Get legend text
                        const text = legendItem.text;
                        // If it is the recall or precision, hide the corresponding datalabels
                        if (text == RECALL_LABEL) {
                            this.chart.data.datasets
                                .filter((d) => d.label == TRUTH_LABEL)
                                .forEach((d) => {
                                    d.datalabels.display =
                                        !d.datalabels.display;
                                });
                        } else if (text == PRECISION_LABEL) {
                            this.chart.data.datasets
                                .filter((d) => d.label == FP_LABEL)
                                .forEach((d) => {
                                    d.datalabels.display =
                                        !d.datalabels.display;
                                });
                        }
                        // Get all datasets with this text
                        const datasets = this.chart.data.datasets.filter(
                            (d) => d.label === text
                        );
                        // Toggle visibility
                        datasets.forEach((d) => {
                            d.hidden = !d.hidden;
                        });
                        // Update chart
                        this.chart.update();
                    },
                    labels: {
                        generateLabels: function (chart) {
                            const datasets = chart.data.datasets;
                            return chart
                                ._getSortedDatasetMetas()
                                .map((meta) => {
                                    const style = meta.controller.getStyle();
                                    // Edit style to show TRUTH_LABEL as a dashed line
                                    return {
                                        text: datasets[meta.index].label,
                                        fillStyle: style.backgroundColor,
                                        hidden: !meta.visible,
                                        lineDash: TRUTH_BORDER_DASH,
                                        lineWidth: style.borderWidth,
                                        strokeStyle: TRUTH_BORDER_COLOR,
                                        // Below is extra data used for toggling the datasets
                                        datasetIndex: meta.index,
                                    };
                                }, this);
                        },
                        filter: function (item, chart) {
                            // Avoid repeating labels
                            if (item.datasetIndex < legendLabels.length) return true;
                            else return false;
                        },
                        sort: function (a, b, data) {
                            return (
                                legendLabels.indexOf(a.text) - legendLabels.indexOf(b.text)
                            );
                        },
                    },
                },
            },
            barPercentage: 0.95,
            categoryPercentage: 1,
            scales: scales,
        },
    });

    return {
        getBase64Image: () => getBase64Image(chart)
    }
}
