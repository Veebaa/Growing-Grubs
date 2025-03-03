import csv
import logging
import os
from flask import Flask
from mod.app import db
from mod.models import Recipe  # Import your Recipe model
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.DEBUG)

# Create a temporary app context
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
db.init_app(app)

def import_recipes():
    logging.debug("📥 Starting recipe import...")
    with app.app_context():
        csv_file = "clean_recipes.csv"

        with open(csv_file, newline='', encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                recipe = Recipe(
                    title=row["title"],
                    description=row["description"],
                    serves=row["serves"],
                    prep_time=row["prep_time"],
                    cook_time=row["cook_time"],
                    age_group=row["age_group"],
                    ingredients=row["ingredients"],
                    method=row["method"],
                    recipe_url=row["recipe_url"],
                    dietary_info=row["dietary_info"],
                    image_url=row["image_url"],
                    views=0  # Default value
                )
                db.session.add(recipe)

            db.session.commit()
            logging.debug("✅ Recipes imported successfully!")

if __name__ == "__main__":
    import_recipes()
