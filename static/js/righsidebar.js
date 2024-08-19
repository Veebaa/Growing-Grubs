//File Reading and XML Parsing
const express = require('express');
const fs = require('fs');
const xml2js = require('xml2js');

const app = express();
const port = 5000;

app.get('/topics', (req, res) => {
  fs.readFile('path/to/mplus_topics_2024-07-30.xml', (err, data) => {
    if (err) {
      res.status(500).send('Error reading XML file');
      return;
    }

    xml2js.parseString(data, (err, result) => {
      if (err) {
        res.status(500).send('Error parsing XML');
        return;
      }

      const topics = result.Topics.Topic; // Adjust based on XML structure
      res.json(topics);
    });
  });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});

//Fetching Data from the Server
document.addEventListener('DOMContentLoaded', () => {
  fetch('http://localhost:5000/topics')
    .then(response => response.json())
    .then(data => {
      let sidebarContent = '';
      data.forEach(topic => {
        sidebarContent += `<li>${topic.title}</li>`;
      });
      document.getElementById('sidebar').innerHTML = `<ul>${sidebarContent}</ul>`;
    })
    .catch(error => {
      console.error('Error fetching topics:', error);
      document.getElementById('sidebar').innerHTML = '<p>Error loading topics. Please try again later.</p>';
    });
});


