# ESSA Project - Growing Grubs Web Application

Growing Grubs is a web application designed to help parents find healthy recipes for their children at various stages of development. The application provides a range of features, including recipe search, user profiles, and feeding tips.

## Features
- Search for recipes based on age groups.
- View detailed recipe information.
- Manage user profiles and favourite recipes.
- Access feeding tips and healthy eating advice.

### Prerequisites
- Python 3.8 or higher

## Getting Started
### Clone the Repository:

`git clone https://github.com/Veebaa/Growing-Grubs` <br>
`cd <repository-directory>`

### Set Up the Virtual Environment:

`python3 -m venv` <br>
source `venv/bin/activate`  # On Windows use `venv\Scripts\activate`

### Install Dependencies:

`pip install -r requirements.txt`

### Set Up Environment Variables:

Create a .env file in the root directory and add your Spoonacular and CDC API keys.

### Initialize the Database:

`flask db init` <br>
`flask db migrate` <br>
`flask db upgrade` 

### Run the Application:

`flask run` <br>
The application should now be running at http://127.0.0.1:5000.