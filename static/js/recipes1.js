document.addEventListener("DOMContentLoaded", function () {
    fetch('/recipes1/json')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log('Data received:', data);  // Debug print statement

            const recipesContainer = document.querySelector('.recipes');

            if (Array.isArray(data)) {
                recipesContainer.innerHTML = ''; // Clear previous content

                data.forEach(meal => {
                    const recipeCard = document.createElement('a');
                    recipeCard.classList.add('recipe-card');
                    recipeCard.href = `/meal/${meal.id}`;

                    const recipeImg = document.createElement('img');
                    recipeImg.src = meal.image || '/static/images/default-recipe.jpg';
                    recipeImg.alt = meal.title;

                    const title = document.createElement('h2');
                    title.textContent = meal.title;

                    const description = document.createElement('p');
                    description.textContent = meal.dishTypes ? meal.dishTypes.join(", ") : "No type available";

                    recipeCard.appendChild(recipeImg);
                    recipeCard.appendChild(title);
                    recipeCard.appendChild(description);
                    recipesContainer.appendChild(recipeCard);
                });
            } else {
                console.error('Unexpected data structure:', data);
                recipesContainer.innerHTML = '<p>No suitable recipes available. Please check back later.</p>';
            }
        })
        .catch(error => {
            console.error('Error fetching recipes:', error);
            const recipesContainer = document.querySelector('.recipes');
            recipesContainer.innerHTML = '<p>Failed to load recipes. Please try again later.</p>';
        });
});
