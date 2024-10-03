function showMealPlanDetails(mealPlanId) {
    fetch(`/meal-plan/${mealPlanId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const mealPlanDetailsDiv = document.getElementById('meal-plan-details');
            mealPlanDetailsDiv.innerHTML = ''; // Clear previous details
            mealPlanDetailsDiv.style.display = 'block';

            const title = document.createElement('h3');
            title.textContent = data.name;
            mealPlanDetailsDiv.appendChild(title);

            const daysList = document.createElement('ul');
            data.days.forEach(day => {
                const listItem = document.createElement('li');
                listItem.textContent = `${day.day}: Breakfast: ${day.breakfast}, Lunch: ${day.lunch}, Dinner: ${day.dinner}`;
                daysList.appendChild(listItem);
            });

            mealPlanDetailsDiv.appendChild(daysList);
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}
