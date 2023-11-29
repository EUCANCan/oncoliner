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

    /**
     * @param {string[]} names
     */
    function setHarmonizationLegendNames(names) {
        for (const chart of charts) {
            chart.setHarmonizationLegendNames(names);
        }
    }

    return {
        setLabelsVisible,
        setHarmonizationData,
        setHarmonizationLegendNames,
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
    // Create a dataset for the chartBaseData
    /** @type {ChartDataset[]} */
    const datasets = [];

    for (let i = 0; i < datasetNames.length; i++) {
        const datasetName = datasetNames[i];
        const harmonizationValues = baseValues[i][index];
        datasets.push({
            customType: 'baseline',
            label: `${datasetName}`,
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
            customType: 'harmonization',
            label: `${datasetName} (baseline)`,
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
     * @param {string} datasetType
     * @param {number[]} values
     */
    function applyValuesToDataset(datasetName, datasetType, values) {
        const dataset = chart.data.datasets.find(
            (dataset) => dataset.label.split(' (')[0] === datasetName && dataset.customType === datasetType
        );
        if (!dataset) {
            throw new Error(
                `Could not find dataset with label ${datasetName} and type ${datasetType}`
            );
        }
        dataset.data = values;
    }

    /**
     * @param {number[][]} newValues
     * @param {number[]} indexes
     * @param {string} datasetType
     */
    function updateDatasetValues(newValues, indexes, datasetType) {
        for (let i = 0; i < newValues.length; i++) {
            const newValue = newValues[i];
            const values = indexes.map((index) => newValue[index]);
            applyValuesToDataset(datasetNames[i], datasetType, values);
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
        updateDatasetValues(harmonizationValues, indexes, 'harmonization');
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
        updateDatasetValues(harmonizationValues, indexes, 'harmonization');
        updateDatasetValues(originalValues, indexes, 'baseline');
        chart.update();
    }

    /**
     * @param {string[]} operationNames
     */
    function setHarmonizationLegendNames(operationNames) {
        // Get all the datasets that are harmonization
        const harmonizationDatasets = chart.data.datasets.filter(
            (dataset) => dataset.customType === 'harmonization'
        );
        // Change the text of the label between brackets
        for (let i = 0; i < harmonizationDatasets.length; i++) {
            const harmonizationDataset = harmonizationDatasets[i];
            const pipelineName = harmonizationDataset.label.split(' (')[0];
            harmonizationDataset.label = `${pipelineName} (${operationNames[i]})`;
        }
        chart.update();
    }

    return {
        setHarmonizationData,
        setLabelsVisible,
        setHarmonizationLegendNames,
        getBase64Image: () => getBase64Image(chart),
        getCanvas: () => {return chart}
    };
}
