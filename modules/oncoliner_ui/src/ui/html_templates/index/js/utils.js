/**
 * @param {string} operationName 
 * @param {boolean} [includeVersionSubtext]
 * @param {number} [maxCharLength]
 */
function parseOperationName(operationName, includeVersionSubtext = true, maxCharLength) {
    const INTERSECTION_SYMBOL = '{{intersection_symbol}}'
    const UNION_SYMBOL = '{{union_symbol}}'

    if (operationName === 'baseline') return operationName;

    // Replace all the intersection symbols with the actual symbol
    operationName = operationName.replaceAll(INTERSECTION_SYMBOL, ' ∩ ');
    // Replace all the union symbols with the actual symbol
    operationName = operationName.replaceAll(UNION_SYMBOL, ' ∪ ');
    // Prettify variant callers names
    {% for caller_id, caller_info in conf["commons"]["variant_callers"].items() %}
    operationName = operationName.replaceAll('{{caller_id}}', '{{caller_info["name"]}}' + (includeVersionSubtext ? '<sub>{{caller_info["version"]}}</sub>' : ''));
    {% endfor %}
    if (maxCharLength && operationName.length > maxCharLength) {
        operationName = operationName.slice(0, maxCharLength) + '...';
    }
    return operationName;
}

/**
 * @param {HTMLElement} cell 
 */
function setOperationCell(cell) {
    cell.setAttribute('original-data-value', cell.textContent);
    const parsedText = parseOperationName(cell.textContent);
    // Clean the cell
    cell.innerHTML = '';
    // Set innerHTML to the cell
    const span = document.createElement('span');
    span.setAttribute('title', parsedText.replaceAll('<sub>', ' (').replaceAll('</sub>', ')'));
    span.innerHTML = parsedText.replace('baseline ', '')
    span.classList.add('viz-cell-operation-name');
    cell.appendChild(span);
}

window.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.viz-operation-name.viz-to-parse').forEach((element) => {
        element.innerHTML = parseOperationName(element.textContent);
        element.classList.remove('viz-to-parse');
    });
});
