import csv
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('mod/database.db')
cur = conn.cursor()

# Open the CSV file
with open('recipes.csv', 'r') as f:
    reader = csv.reader(f)

    # Skip the header row if present
    next(reader)

    for row in reader:
        cur.execute("""
            INSERT INTO recipes (title, description, serves, prep_time, cook_time, age_group, ingredients, method, image_url, views, last_viewed, recipe_url, dietary_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

# Commit changes and close connection
conn.commit()
conn.close()

