// Requires IRadarChart.js
/**
 * @param {string} htmlContainerId
 * @param {string[]} datasetNames
 * @param {string[]} titles
 * @param {string[]} labels
 * @param {number[][][]} baseValues
 */
function createHarmonizationPlot(htmlContainerId, datasetNames, titles, labels, baseValues) {
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
    /** @type {ReturnType<typeof _buildHarmonizationChart>[]} */
    const charts = [];
    for (let i = 0; i < titles.length; i++) {
        const div = document.createElement("div");
        const ctx = document.createElement("canvas");
        // Set the div to the correct column
        div.style.gridColumn = i + 1 + "";
        div.appendChild(ctx);
        htmlContainer.appendChild(div);
        charts.push(
            _buildHarmonizationChart(ctx, i, datasetNames, titles, labels, baseValues)
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
     * @param {number[][][]} values
     */
    function setHarmonizationData(values) {
        for (let i = 0; i < titles.length; i++) {
            const chartValues = values.map((datasetValues) => datasetValues[i]);
            charts[i].setHarmonizationData(chartValues);
        }
    }

    return {
        setLabelsVisible,
        setHarmonizationData,
        getBase64Images : () => charts.map(chart => chart.getBase64Image()),
        getCanvas: () => concatCanvases(charts.map((chart) => chart.getCanvas()))
    };
}

/**
 * @param {HTMLCanvasElement} ctx
 * @param {number} index
 * @param {string[]} datasetNames
 * @param {string[]} titles
 * @param {string[]} labels
 * @param {number[][][]} baseValues
 */
function _buildHarmonizationChart(ctx, index, datasetNames, titles, labels, baseValues) {
    const COLORS = ["#228833", "#bc629f", "#4477AA", "#E3B505", "#95190C"];
    const HARMONIZATION_SUFFIX = " (harmonization)";
    const BASELINE_SUFFIX = " (baseline)";
    // Create a dataset for the chartBaseData
    /** @type {ChartDataset[]} */
    const datasets = [];

    for (let i = 0; i < datasetNames.length; i++) {
        const datasetName = datasetNames[i];
        const harmonizationValues = baseValues[i][index];
        datasets.push({
            label: `${datasetName}${BASELINE_SUFFIX}`,
            data: harmonizationValues,
            backgroundColor: `${COLORS[i % COLORS.length]}50`,
            borderWidth: 0,
            pointBorderWidth: 0,
            pointBackgroundColor: `rgba(0, 0, 0, 0)`,
            datalabels: {
                display: false,
            },
        });
        datasets.push({
            label: `${datasetName}${HARMONIZATION_SUFFIX}`,
            data: harmonizationValues,
            borderColor: COLORS[i % COLORS.length],
            pointBackgroundColor: COLORS[i % COLORS.length],
            // backgroundColor: `${COLORS[i % COLORS.length]}00`,
            backgroundColor: `rgba(0, 0, 0, 0)`,
            datalabels: {
                display: false,
            },
        });
    }

    // Copy the labels
    const originalLabels = [...labels];
    const originalValues = datasetNames.map((_, i ) => baseValues[i][index]);
    let harmonizationValues = datasetNames.map((_, i ) => baseValues[i][index]);

    const chart = buildRadarChart(labels, datasets, titles[index], ctx);

    /**
     * @param {string} datasetName
     * @param {number[]} values
     */
    function applyValuesToDataset(datasetName, values) {
        const dataset = chart.data.datasets.find(
            (dataset) => dataset.label === datasetName
        );
        if (!dataset) return;
        dataset.data = values;
    }

    /**
     * @param {number[][]} newValues
     * @param {number[]} indexes
     * @param {string} suffix
     */
    function updateDatasetValues(newValues, indexes, suffix) {
        for (let i = 0; i < newValues.length; i++) {
            const datasetName = `${datasetNames[i]}${suffix}`;
            const newValue = newValues[i];
            const values = indexes.map((index) => newValue[index]);
            applyValuesToDataset(datasetName, values);
        }
    }

    /**
     * @param {number[][]} values
     */
    function setHarmonizationData(values) {
        harmonizationValues = values;
        // Get the indexes of the labels that are in the chart
        const indexes = [];
        // @ts-ignore
        for (const label of chart.data.labels) {
            const index = originalLabels.indexOf(label);
            if (index === -1) continue;
            indexes.push(index);
        }
        // Get the values of the labels that are in the chart
        updateDatasetValues(harmonizationValues, indexes, HARMONIZATION_SUFFIX);
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
        updateDatasetValues(harmonizationValues, indexes, HARMONIZATION_SUFFIX);
        updateDatasetValues(originalValues, indexes, BASELINE_SUFFIX);
        chart.update();
    }

    return {
        setHarmonizationData,
        setLabelsVisible,
        getBase64Image: () => getBase64Image(chart),
        getCanvas: () => {return chart}
    };
}
