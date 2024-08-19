document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('age-group-form');
    const portionSizesList = document.getElementById('portion-sizes-list');
    const loadMoreButton = document.getElementById('load-more');
    let currentOffset = 0;
    const itemsPerPage = 5;
    let totalItems = 0;
    let ageGroup = '';

    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent form submission from reloading the page
        ageGroup = document.getElementById('age_group').value;
        currentOffset = 0; // Reset the offset for new search
        portionSizesList.innerHTML = ''; // Clear any previous results
        loadMoreButton.style.display = 'none'; // Hide the "Load More" button initially
        fetchPortionSizes();
    });

    loadMoreButton.addEventListener('click', function() {
        currentOffset += itemsPerPage;
        fetchPortionSizes();
    });

    function fetchPortionSizes() {
        fetch(`/proxy?age_group=${encodeURIComponent(ageGroup)}&offset=${currentOffset}&limit=${itemsPerPage}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log(data); // Debugging: Log the entire fetched data

                const items = [...(data.branded || []), ...(data.common || [])];

                if (items.length > 0) {
                    totalItems = items.length;
                    items.slice(currentOffset, currentOffset + itemsPerPage).forEach(item => {
                        const listItem = document.createElement('li');
                        listItem.textContent = `${item.food_name}: ${item.serving_qty || 'N/A'} ${item.serving_unit || 'N/A'}`;
                        portionSizesList.appendChild(listItem);
                    });

                    // Show or hide the "Load More" button based on whether more items are available
                    if (currentOffset + itemsPerPage < totalItems) {
                        loadMoreButton.style.display = 'block';
                    } else {
                        loadMoreButton.style.display = 'none';
                    }
                } else {
                    loadMoreButton.style.display = 'none';
                    const noDataMessage = document.createElement('li');
                    noDataMessage.textContent = 'No data found for the selected age group.';
                    portionSizesList.appendChild(noDataMessage);
                }
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                const errorMessage = document.createElement('li');
                errorMessage.textContent = 'An error occurred while fetching data.';
                portionSizesList.appendChild(errorMessage);
            });
    }
});
