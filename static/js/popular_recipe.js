async function fetchPopularRecipe() {
    const apiKey = 'c676336b8de04c04b131f2f91eb14b33';
    const response = await fetch(`https://api.spoonacular.com/recipes/random?number=1&apiKey=${apiKey}`);

    if (!response.ok) {
        console.error("Failed to fetch popular recipe:", response.statusText);
        return; // Early return if the fetch fails
    }

    const data = await response.json();
    console.log("Popular recipe data fetched:", data);

    const recipe = data.recipes[0];
    if (!recipe) {
        console.error("No recipe found in response");
        return; // Early return if no recipe is found
    }

    document.getElementById('toprecipe_image').src = recipe.image;
    document.getElementById('toprecipe_title').innerText = recipe.title;
    document.getElementById('toprecipe_link').href = `/meal/${recipe.id}`;
}

function showPopup(message) {
    const popup = document.getElementById('popup');
    const overlay = document.getElementById('overlay');
    popup.innerText = message;
    popup.classList.add('show');
    overlay.classList.add('show');

    setTimeout(() => {
        popup.classList.remove('show');
        overlay.classList.remove('show');
    }, 3000); // Auto-hide after 3 seconds
}

window.onload = function() {
    fetchPopularRecipe();
    const messagesJson = document.getElementById('flash-messages').textContent;
    const messages = JSON.parse(messagesJson);
    if (messages.length > 0) {
        showPopup(messages[0]); // Show the first message
    }
};