function removeFromFavourites(recipeId) {
    // Send the POST request using fetch
    fetch(`/unfavourite/${recipeId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'  // Add CSRF token if needed
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove the recipe card from the DOM
            const recipeCard = document.getElementById(`recipe-${recipeId}`);
            if (recipeCard) {
                recipeCard.remove();
            }
            // Display a success message
            alert(data.message);
        } else {
            // Display an error message
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

