//search bar function
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');

searchButton.addEventListener('click', function() {
  // Process the search query here
  const query = searchInput.value;
  console.log('Searching for: ' + query);
});

