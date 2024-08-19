async function fetchTopics() {
    try {
    const response = await fetch('/topics');
    if (!response.ok) throw new Error('Failed to fetch topics');
    const data = await response.json();

    let sidebarContent = '';
    data.forEach(topic => {
      sidebarContent += `<li><a href="${topic.url}">${topic.title}</a></li>`;
    });

    document.getElementById('sidebar').innerHTML = `<ul>${sidebarContent}</ul>`;
    } catch (error) {
    console.error('Error fetching topics:', error);
    document.getElementById('sidebar').innerHTML = '<p>Error loading topics. Please try again later.</p>';
    }
};