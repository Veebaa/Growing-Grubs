document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('age-group-form');
    const portionSizesList = document.getElementById('portion-sizes-list');
    const previousButton = document.getElementById('previous');
    const nextButton = document.getElementById('next');

    let currentOffset = 0;
    const itemsPerPage = 5;
    let totalItems = 0;
    let ageGroup = '';

    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent form submission from reloading the page
        ageGroup = document.getElementById('age_group').value;
        currentOffset = 0; // Reset the offset for new search
        portionSizesList.innerHTML = ''; // Clear any previous results
        fetchPortionSizes();
    });

    previousButton.addEventListener('click', function() {
        if (currentOffset > 0) {
            currentOffset -= itemsPerPage;
            fetchPortionSizes();
        }
    });

    nextButton.addEventListener('click', function() {
        if (currentOffset + itemsPerPage < totalItems) {
            currentOffset += itemsPerPage;
            fetchPortionSizes();
        }
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

                const items = data.portion_sizes || [];

                if (items.length > 0) {
                    totalItems = data.total_items; // Update totalItems from the response
                    portionSizesList.innerHTML = ''; // Clear the list before adding new items
                    items.forEach(item => {
                        const listItem = document.createElement('li');
                        listItem.textContent = `${item.food_name}: ${item.serving_qty || 'N/A'} ${item.serving_unit || 'N/A'}`;
                        portionSizesList.appendChild(listItem);
                    });

                    // Show or hide buttons based on currentOffset and totalItems
                    previousButton.style.display = currentOffset > 0 ? 'block' : 'none';
                    nextButton.style.display = currentOffset + itemsPerPage < totalItems ? 'block' : 'none';
                } else {
                    previousButton.style.display = 'none';
                    nextButton.style.display = 'none';
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
