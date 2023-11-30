/**
 * @param {HTMLElement} headerTr
 */
function _createFilterHeader(headerTr) {
    const clone = headerTr.cloneNode(true);
    clone.classList.add("viz-filters");
    headerTr.parentNode.appendChild(clone);
}

/**
 * @param {HTMLElement} headerTr
 */
function _getSortableColumns(headerTr) {
    // Iterate over the header cells
    const sortableColumns = [];
    headerTr.querySelectorAll("th").forEach((cell, index) => {
        // If data-sortable is present, add the column index to the list
        if (cell.hasAttribute("data-sortable")) sortableColumns.push(index);
    });
    return sortableColumns;
}

/**
 * @param {string} tableId
 * @param {number} fixedRowIndex
 */
function _createFixedRow(tableId, fixedRowIndex) {
    const table = document.querySelector(`#${tableId}`);
    const selectedRow = table.querySelector(`tbody tr:nth-child(${fixedRowIndex+1})`);
    const clone = selectedRow.cloneNode(true);
    // Add class to the cloned row
    clone.classList.add("viz-fixed-row");
    // Add at the end of the table header
    table.querySelector("thead").appendChild(clone);
}

function _initComplete() {
    const api = this.api();
    const tableId = api.table().node().id;
    api.columns()
        .eq(0)
        .each(function (colIdx) {
            const cell = document.querySelector(
                `#${tableId} .viz-filters th:nth-child(${colIdx + 1})`
            );
            // Remove tooltip
            cell.removeAttribute("data-bs-toggle");
            cell.removeAttribute("data-bs-placement");
            cell.removeAttribute("data-bs-title");
            // If data-filterable is not present, don't add a filter
            if (!cell.hasAttribute("data-filterable")) {
                cell.innerHTML = "";
                return;
            }
            // Add filter text field
            const title = cell.innerText;
            cell.innerHTML = `<input type="text" placeholder="Filter ${title.toLowerCase()}" id="filter_${tableId}_${title}" />`;
            // Listen to the filter input
            cell.querySelector("input").addEventListener("keyup", function (e) {
                // Get the value searched
                const search = this.value;
                // Search the column for that value
                api.column(colIdx).search(search).draw();
            });
        });
}

/**
 * @param {string} tableId
 * @param {[number, string][]} [defaultOrder]
 * @param {number} [defaultSortColumnIndex]
 * @param {number} [fixedRowIndex]
 */
function makeTableDynamic(tableId, defaultOrder=[], defaultSortColumnIndex, fixedRowIndex) {
    // Set the table width to 100%
    document.querySelector(`#${tableId}`).style.width = "100%";
    // Get the table header
    const headerTr = document.querySelector(`#${tableId} thead tr`);
    // Create a row for each column filter
    _createFilterHeader(headerTr);
    // If a fixed row index is specified, make it fixed
    if (fixedRowIndex !== undefined) {
        _createFixedRow(tableId, fixedRowIndex);
    }
    // Get the list of sortable columns
    const sortableColumns = _getSortableColumns(headerTr);
    // Get the list of non-sortable columns
    const nonSortableColumns = Array.from(
        { length: headerTr.querySelectorAll("th").length },
        (_, i) => i
    ).filter((i) => !sortableColumns.includes(i));
    // Create the datatable config
    const config = {
        orderCellsTop: true,
        fixedHeader: true,
        responsive: true,
        bPaginate: false,
        columnDefs: [
            {
                targets: sortableColumns,
                orderable: true,
            },
            {
                targets: nonSortableColumns,
                orderable: false,
            },
        ],
        dom: "lrtip", // Hide the search bar
        initComplete: _initComplete,
    };
    // If a default sort column is specified, add it to the config
    if (defaultSortColumnIndex !== undefined) {
        config.order = [defaultSortColumnIndex, "desc"];
    } else {
        config.order = [];
    }
    // Build the DataTable
    const dtTable = new DataTable(`#${tableId}`, config);
    dtTable.order(defaultOrder).draw();
    return dtTable;
}

/**
 * @param {string} tableId
 * @param {() => void} callback
 */
function addButtonsToTable(tableId, callback) {
    const table = document.querySelector(`#${tableId}`);
    // Add a empty cell to the table header
    table.querySelectorAll("thead tr").forEach((row) => {
        const cell = row.insertCell(0);
        cell.style.width = 0;
    });
    // Add a new column to the table at the start in the body
    table.querySelectorAll("tbody tr").forEach((row) => {
        // Get all the strings in the row
        const cells = [];
        row.querySelectorAll("td").forEach((cell) => {
            cells.push(cell);
        });
        const cell = row.insertCell(0);
        cell.classList.add("icon-cell");
        const a = document.createElement("a");
        a.classList.add("icon-circle-empty");
        a.onclick = () => callback(cells);
        cell.appendChild(a);
    });
}
