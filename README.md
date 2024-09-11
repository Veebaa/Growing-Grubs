# ESSA Project - Growing Grubs Web Application

Growing Grubs is a web application aimed at parents and caregivers of children aged 6 months to 4 years. It consolidates healthy eating guidelines, weaning advice, and simple, child-friendly recipes in one place. The app is designed to help parents find and manage recipes tailored to different stages of their children's development, making it easier to incorporate nutritious meals into their daily routines.

## Features
- Recipe Search: Search for recipes based on the child's age group or specific ingredients.
- Detailed Recipe View: Each recipe comes with portion sizes, ingredients, preparation instructions, and additional notes for easy understanding.
- User Profiles: Create an account, log in, and save favorite recipes for future access.
- Weaning and Feeding Tips: Access up-to-date guidelines on healthy eating, portion sizes, and weaning based on resources from Healthy Ireland and the NHS.
- Responsive Design: Mobile-friendly layout, ensuring the app works smoothly on all devices.

## Future Functionality
- Portion Size Adjustment: Allow users to adjust recipes based on their child's portion size requirements.
- Add Your Own Recipes: Feature enabling users to contribute their own recipes.
- Meal Planning: Simple meal plan suggestions based on age groups.

## Prerequisites
- Python 3.8 or higher
- Flask 2.x or higher
- NHS API Key (for health information integration)
  - Go to `https://developer.api.nhs.uk/nhs-api`
  - Create an account
  - Your Primary Key and Secondary Key will be located under your profile page.

## Getting Started
### Clone the Repository:

```comandline
git clone https://github.com/Veebaa/Growing-Grubs
cd <repository-directory>
```

### Set Up the Virtual Environment:
For Linux/Mac:

```comandline
python3 -m venv venv
source venv/bin/activate
```

For Windows:

```comandline
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies:
Install all the necessary Python libraries:

```comandline
pip install -r requirements.txt
```

### Set Up Environment Variables:

You need to create a `.env` file in the root directory of the project. 
Inside `.env`, add your NHS API key for health information integration:

```
NHS_API_KEY=<your_nhs_api_key>
```

### Initialize the Database:

The app uses SQLite for storing recipe, user profile, and favorites data. 
Set up the database with the following commands:

`flask db init` <br>
`flask db migrate` <br>
`flask db upgrade` 

### Run the Application:

Once the dependencies are installed and the database is set up, run the application:

`flask run` <br>

The application should now be running at http://127.0.0.1:5000.

## Development Overview
- Backend: The app uses Flask to handle routing and backend logic. Python scripts manage the server-side operations and API calls.
- Frontend: HTML, CSS, and JavaScript (including jQuery) are used to design the user interface and manage dynamic interactions.
- Database: SQLite is used for storing user profiles, favorite recipes, and other relevant information.
- Templating Engine: Jinja2 is used for rendering HTML templates dynamically.
- Version Control: Git was used to manage project versions, ensuring that changes were tracked throughout development.

## Design Considerations
The project was designed to be user-friendly and accessible:

- A ***mobile-first*** approach ensures the application is responsive across devices.
- ***Intuitive navigation*** allows users to search recipes easily, save favorites, and access feeding tips.
- The ***colour scheme*** and UI layout were kept simple and subtle to reduce visual strain, particularly on mobile screens.

## Agile Approach
The project followed Agile methodologies with user stories and feature prioritization. Feedback was gathered through research, including discussions with parents in user groups, and iteratively implemented:

- ***Must Have***: Recipe search, user authentication, feeding tips, responsive design.
- ***Should Have***: Save favorite recipes, adjust portion sizes, user profile management.
- ***Could Have***: Meal planning, personalized recipe suggestions, adding user-generated content.

## Mockups and Design Prototypes
During the planning phase, mockups were created using Figma to visualize the 
layout and user flow. Wireframes focused on clean design, mobile responsiveness, 
and ease of navigation. The designs were refined based on user feedback, ensuring 
that key features were easy to access on both desktop and mobile views.