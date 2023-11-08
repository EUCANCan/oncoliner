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
            cell.innerHTML = `<input type="text" placeholder="${title}" id="filter_${tableId}_${title}" />`;
            // Listen to the filter input
            cell.querySelector("input").addEventListener("keyup", function (e) {
                // Get the value searched
                const search = this.value;
                console.log(search);
                // Search the column for that value
                api.column(colIdx).search(search, true, false).draw();
            });
        });
}

/**
 * @param {string} tableId
 * @param {number} [defaultSortColumnIndex]
 */
function makeTableDynamic(tableId, defaultSortColumnIndex) {
    // Set the table width to 100%
    document.querySelector(`#${tableId}`).style.width = "100%";
    // Get the table header
    const headerTr = document.querySelector(`#${tableId} thead tr`);
    // Create a row for each column filter
    _createFilterHeader(headerTr);
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
    new DataTable(`#${tableId}`, config);
}

/**
 * @param {string} tableId
 * @param {() => void} callback
 */
function addButtonsToTable(tableId, callback) {
    const table = document.querySelector(`#${tableId}`);
    // Add a new column to the table at the start
    const rows = table.querySelectorAll("tr");
    rows.forEach((row, index) => {
        if (index == 0) {
            const cell = row.insertCell(0);
            cell.style.width = "0";
            return;
        } else if (index < 2) {
            row.insertCell(0);
            return;
        }
        // Get all the strings in the row
        const strings = [];
        row.querySelectorAll("td").forEach((cell) => {
            strings.push(cell.innerText);
        });
        const cell = row.insertCell(0);
        const a = document.createElement("a");
        a.classList.add("icon-search");
        a.onclick = () => callback(strings);
        cell.appendChild(a);
    });
}
