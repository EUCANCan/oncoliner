// Requires IRadarChart.js

/**
 * @param {string} htmlContainerId
 * @param {string[]} titles
 * @param {string[]} labels
 * @param {number[][]} baseValues
 */
function createImprovementPlot(htmlContainerId, titles, labels, baseValues) {
    const htmlContainer = /** @type {HTMLElement} */ (
        document.querySelector(`#${htmlContainerId}`)
    );
    if (!htmlContainer)
        throw new Error(`Could not find element with id ${htmlContainerId}`);
    // Set htmlContainer style to grid with the same amount of columns as chartBaseDataList
    htmlContainer.style.display = "grid";
    htmlContainer.style.gridTemplateColumns = `repeat(${titles.length}, 1fr)`;
    // Make it 100% width
    htmlContainer.style.width = "100%";
    // Make it 100% height
    htmlContainer.style.height = "100%";
    // Create the same number HTMLDivElement as chartBaseDataList
    /** @type {ReturnType<typeof _buildImprovementChart>[]} */
    const charts = [];
    for (let i = 0; i < titles.length; i++) {
        const div = document.createElement("div");
        const ctx = document.createElement("canvas");
        // Set the div to the correct column
        div.style.gridColumn = i + 1 + "";
        div.appendChild(ctx);
        htmlContainer.appendChild(div);
        charts.push(
            _buildImprovementChart(ctx, i, titles[i], labels, baseValues[i])
        );
    }

    /**
     * @param {string[]} newVisibleLabels
     */
    function setLabelsVisible(newVisibleLabels) {
        for (const chart of charts) {
            chart.setLabelsVisible(newVisibleLabels);
        }
    }

    /**
     * @param {number[][]} values
     */
    function setImprovementData(values) {
        for (let i = 0; i < titles.length; i++) {
            charts[i].setImprovementData(values[i]);
        }
    }

    return {
        setLabelsVisible,
        setImprovementData,
        getBase64Images: () => charts.map((chart) => chart.getBase64Image()),
        getCanvas: () => concatCanvases(charts.map((chart) => chart.getCanvas()))
    };
}

/**
 * @param {HTMLCanvasElement} ctx
 * @param {number} index
 * @param {string} title
 * @param {string[]} labels
 * @param {number[]} baseValues
 */
function _buildImprovementChart(ctx, index, title, labels, baseValues) {
    const COLORS = ["#228833", "#bc629f", "#4477AA"];
    const DATALABEL_COLOR_IMPROVEMENT = "darkgreen";
    const DATALABEL_COLOR_DETERIORATION = "darkred";
    const DATALABEL_COLOR_NO_CHANGE = "black";
    // Create a dataset for the chartBaseData
    /** @type {ChartDataset[]} */
    const datasets = [
        {
            label: "Baseline",
            data: baseValues,
            borderColor: COLORS[index % COLORS.length],
            backgroundColor: `${COLORS[index % COLORS.length]}63`,
            borderWidth: 0,
            pointBorderWidth: 0,
            pointBackgroundColor: `rgba(0, 0, 0, 0)`,
            datalabels: {
                display: false,
            },
        },
        {
            label: "Improvement",
            data: baseValues,
            borderColor: COLORS[index % COLORS.length],
            pointBackgroundColor: COLORS[index % COLORS.length],
            // backgroundColor: `${COLORS[index % COLORS.length]}00`,
            backgroundColor: `rgba(0, 0, 0, 0)`,
            datalabels: {
                anchor: "center",
                align: "end",
                color: function (context) {
                    const baseValue =
                        context.chart.data.datasets[0].data[context.dataIndex];
                    const improvementValue =
                        context.chart.data.datasets[1].data[context.dataIndex];
                    if (baseValue === null || improvementValue === null)
                        return DATALABEL_COLOR_NO_CHANGE;
                    if (improvementValue > baseValue) {
                        return DATALABEL_COLOR_IMPROVEMENT;
                    } else if (improvementValue < baseValue) {
                        return DATALABEL_COLOR_DETERIORATION;
                    } else {
                        return DATALABEL_COLOR_NO_CHANGE;
                    }
                },
                formatter: function (value, context) {
                    // Show the difference between the baseline and the improvement
                    const baseValue =
                        context.chart.data.datasets[0].data[context.dataIndex];
                    const improvementValue =
                        context.chart.data.datasets[1].data[context.dataIndex];
                    if (baseValue === null || improvementValue === null) return;
                    // @ts-ignore
                    const difference = improvementValue - baseValue;
                    const sign =
                        difference == 0 ? "" : difference > 0 ? "+" : "-";
                    return `${sign}${Math.abs(difference).toFixed(2)}`;
                },
            },
        },
    ];

    // Copy the labels
    const originalLabels = [...labels];
    const originalValues = [...baseValues];
    let improvementValues = [...baseValues];

    const chart = buildRadarChart(labels, datasets, title, ctx);

    /**
     * @param {number[]} values
     */
    function setImprovementData(values) {
        improvementValues = values;
        // Get the indexes of the labels that are in the chart
        const indexes = [];
        // @ts-ignore
        for (const label of chart.data.labels) {
            const index = originalLabels.indexOf(label);
            if (index === -1) continue;
            indexes.push(index);
        }
        // Get the values of the labels that are in the chart
        datasets[1].data = indexes.map((index) => improvementValues[index]);
        chart.update();
    }

    /**
     * @param {string[]} newVisibleLabels
     */
    function setLabelsVisible(newVisibleLabels) {
        // Get the indexes of the newVisibleLabels
        const indexes = [];
        for (const label of newVisibleLabels) {
            const index = originalLabels.indexOf(label);
            if (index === -1) continue;
            indexes.push(index);
        }
        // Sort the indexes
        indexes.sort((a, b) => a - b);
        // Get the values of the labels that are in the chart
        chart.data.labels = indexes.map((index) => originalLabels[index]);
        datasets[0].data = indexes.map((index) => originalValues[index]);
        datasets[1].data = indexes.map((index) => improvementValues[index]);
        chart.update();
    }

    return {
        setImprovementData,
        setLabelsVisible,
        getBase64Image: () => getBase64Image(chart),
        getCanvas: () => {return chart}
    };
}
