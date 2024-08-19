document.addEventListener("DOMContentLoaded", function () {
    const apiKey = 'c676336b8de04c04b131f2f91eb14b33';
    const endpoint = `https://api.spoonacular.com/recipes/complexSearch?apiKey=${apiKey}&number=10&diet=vegetarian&maxReadyTime=30&sort=random&cuisine=Italian,American,Indian,Asian&intolerances=gluten,peanut`;

    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            // Check if the data and results are defined
            if (data && Array.isArray(data.results)) {
                const recipes = data.results;
                const recipesContainer = document.querySelector('.recipes');

                if (!recipesContainer) return;

                // Clear only existing recipes
                const existingRecipes = recipesContainer.querySelectorAll('.recipe-card');
                existingRecipes.forEach(card => card.remove());

                // Process and display recipes
                recipes.forEach(meal => {
                    const recipeCard = document.createElement('a');
                    recipeCard.classList.add('recipe-card');
                    recipeCard.href = `/meal/${meal.id}`;

                    const recipeImg = document.createElement('img');
                    recipeImg.src = meal.image || 'default_image_url.jpg';
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
                const recipesContainer = document.querySelector('.recipes');
                if (recipesContainer) {
                    recipesContainer.innerHTML += '<p>No popular recipes available. Please check back later.</p>';
                }
            }
        })
        .catch(error => {
            console.error('Error fetching recipes:', error);
            const recipesContainer = document.querySelector('.recipes');
            if (recipesContainer) {
                // Keep existing content, show error message
                recipesContainer.innerHTML += '<p>Failed to load new recipes. Please try again later.</p>';
            }
        });
});