/**
 * @param {import("chart.js").Chart} chart
 *
 * @returns {Promise<string>} The base64 image
 */
function getBase64Image(chart) {
    // The image is blank, we have to listen to the animation finish event
    const promise = new Promise((resolve) => {
        if (!chart.options.animation) chart.options.animation = {};
        chart.options.animation.onComplete = () => {
            const url = chart.toBase64Image();
            resolve(url);
        };
    });
    chart.update();
    return promise;
}

/* assumes each canvas has the same height */
function concatCanvases(canvases) {
    var newCanvas = document.createElement('canvas'),
        ctx = newCanvas.getContext('2d'),
        width = canvases.reduce((x, y) => {
            return (x.width || x) + y.width
        }),
        height = canvases[0].height;

    newCanvas.width = width;
    newCanvas.height = height;

    var currX = 0;

    canvases.forEach(function(cnv) {
        ctx.beginPath();
        ctx.drawImage(cnv.canvas, currX, 0, cnv.width, cnv.height);
        currX += cnv.width;
    });

    return newCanvas;
};

function saveCanvas(canvas, filename) {
    canvas.toBlob(function(blob) {
        saveAs(blob, filename);
    });
}