function toggleMealPlanDetails(mealPlanId) {
    const detailsElement = document.getElementById(`details-${mealPlanId}`);
    detailsElement.style.display = detailsElement.style.display === 'block' ? 'none' : 'block';
}
