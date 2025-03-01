// static/js/script.js
async function fetchCVEs() {
    const response = await fetch('/cves/'); // Fetch from our API
    const cves = await response.json();

    const tableBody = document.querySelector('#cve-table tbody');
    tableBody.innerHTML = ''; // Clear previous results

        // Display Total Records
    const totalRecordsElement = document.getElementById('total-records');
    totalRecordsElement.textContent = `Total Records: ${cves.length}`;


    cves.forEach(cve => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><a href="/cves/details?cve_id=${cve.cve_id}">${cve.cve_id}</a></td>
            <td>${cve.published ? new Date(cve.published).toLocaleDateString() : 'N/A'}</td>
            <td>${cve.description || 'N/A'}</td>
            <td>${cve.base_score_v3 !== null ? cve.base_score_v3 : 'N/A'}</td>
        `;
        // Add click event to navigate to details page
        row.addEventListener('click', () => {
            window.location.href = `/cves/details?cve_id=${cve.cve_id}`;
        });
        tableBody.appendChild(row);
    });
    setupPagination(cves);
}


async function fetchCVEDetails(cveId) {
    const response = await fetch(`/cves/${cveId}`);
    const cve = await response.json();

    const detailsDiv = document.querySelector('#cve-details');
    detailsDiv.innerHTML = `
        <h2>${cve.cve_id}</h2>
        <p><strong>Published:</strong> ${cve.published ? new Date(cve.published).toLocaleDateString() : 'N/A'}</p>
        <p><strong>Description:</strong> ${cve.description || 'N/A'}</p>
        <p><strong>CVSS v3 Base Score:</strong> ${cve.base_score_v3 !== null ? cve.base_score_v3 : 'N/A'}</p>
        <p><strong>CVSS v2 Base Score:</strong> ${cve.base_score_v2 !== null ? cve.base_score_v2 : 'N/A'}</p>
        `;
}

        //Pagination
        function setupPagination(cves) {
            const resultsPerPageSelect = document.getElementById('results-per-page');
            const currentPageElement = document.getElementById('current-page');
            const prevPageButton = document.getElementById('prev-page');
            const nextPageButton = document.getElementById('next-page');

            let currentPage = 1;
            let resultsPerPage = parseInt(resultsPerPageSelect.value, 10);

            function updateTable() {
                const startIndex = (currentPage - 1) * resultsPerPage;
                const endIndex = startIndex + resultsPerPage;
                const paginatedCVEs = cves.slice(startIndex, endIndex);

                const tableBody = document.querySelector('#cve-table tbody');
                tableBody.innerHTML = ''; // Clear previous results

                paginatedCVEs.forEach(cve => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><a href="/cves/details?cve_id=${cve.cve_id}">${cve.cve_id}</a></td>
                        <td>${cve.published ? new Date(cve.published).toLocaleDateString() : 'N/A'}</td>
                        <td>${cve.description || 'N/A'}</td>
                        <td>${cve.base_score_v3 !== null ? cve.base_score_v3 : 'N/A'}</td>
                    `;
                row.addEventListener('click', () => {
                        window.location.href = `/cves/details?cve_id=${cve.cve_id}`;
                    });
                    tableBody.appendChild(row);
                });

            currentPageElement.textContent = `Page ${currentPage}`;

            }

            // Event listener for changing results per page
            resultsPerPageSelect.addEventListener('change', () => {
                resultsPerPage = parseInt(resultsPerPageSelect.value, 10);
                currentPage = 1; // Reset to the first page
                updateTable();
            });

            // Event listeners for pagination buttons
            prevPageButton.addEventListener('click', () => {
                if (currentPage > 1) {
                    currentPage--;
                    updateTable();
                }
            });

            nextPageButton.addEventListener('click', () => {
                const totalPages = Math.ceil(cves.length / resultsPerPage);
                if(currentPage < totalPages) {
                currentPage++;
                updateTable();
                }

            });

            updateTable(); // Initial table update
        }



// Call the appropriate function when the page loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/cves/list') {
        fetchCVEs();
    } else if (window.location.pathname.startsWith('/cves/details')) {
        const urlParams = new URLSearchParams(window.location.search);
        const cveId = urlParams.get('cve_id');
        if (cveId) {
            fetchCVEDetails(cveId);
        }
    }
});