import random
import pandas as pd
import sqlite3
import json
import streamlit as st
import os

# Initialize SQLite database
DB_NAME = "characters.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age TEXT,
            gender TEXT,
            residence TEXT,
            background TEXT,
            profession TEXT,
            attributes TEXT,
            allocated_points TEXT
        )
    """)
    conn.commit()
    conn.close()

# Save character to SQLite database
def save_character_to_db(character_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO characters (name, age, gender, residence, background, profession, attributes, allocated_points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        character_data["Name"],
        character_data["Age"],
        character_data["Gender"],
        character_data["Residence"],
        character_data["Background"],
        character_data["Profession"]["Profession"],
        json.dumps(character_data["Attributes"]),
        json.dumps(character_data["Allocated Points"])
    ))
    conn.commit()
    conn.close()

# Load all characters from SQLite database
def load_characters_from_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM characters")
    rows = c.fetchall()
    conn.close()
    return rows

# Define attribute generation function
def roll_attribute(num_dice, sides, multiplier=1):
    return sum(random.randint(1, sides) for _ in range(num_dice)) * multiplier

# Professions data
professions_data = [
    {
        "Profession": "Accountant",
        "Skill Points Formula": "EDU × 4",
        "Credit Rating Range": "30-70",
        "Key Skills": ["Accounting", "Library Use", "Law", "Listen", "Persuade", "Spot Hidden", "Two personal skills"],
        "Background": "Accountants are meticulous and skilled in financial analysis."
    },
    {
        "Profession": "Actor",
        "Skill Points Formula": "EDU × 2 + APP × 2",
        "Credit Rating Range": "9-40",
        "Key Skills": ["Art (Acting)", "Disguise", "Fighting (Brawl)", "History", "Psychology", "Two social skills"],
        "Background": "Actors are performers who can navigate social and cultural circles."
    },
    {
        "Profession": "Archaeologist",
        "Skill Points Formula": "EDU × 4",
        "Credit Rating Range": "10-40",
        "Key Skills": ["Archaeology", "Appraise", "History", "Language (Other)", "Library Use", "Spot Hidden", "Mechanical Repair", "Navigate"],
        "Background": "Archaeologists study ancient sites and artifacts, often working with museums and universities."
    }
]

# Generate basic attributes for CoC character
def generate_character():
    return {
        "Strength (STR)": roll_attribute(3, 6, 5),
        "Constitution (CON)": roll_attribute(3, 6, 5),
        "Size (SIZ)": roll_attribute(2, 6, 5) + 30,
        "Dexterity (DEX)": roll_attribute(3, 6, 5),
        "Appearance (APP)": roll_attribute(3, 6, 5),
        "Intelligence (INT)": roll_attribute(2, 6, 5) + 30,
        "Power (POW)": roll_attribute(3, 6, 5),
        "Education (EDU)": roll_attribute(2, 6, 5) + 30,
        "Luck": roll_attribute(3, 6, 5),
    }

# Calculate skill points based on formula
def calculate_skill_points(profession, attributes):
    formula = profession["Skill Points Formula"]
    components = formula.split(" + ")
    total_points = 0
    for component in components:
        attr, multiplier = component.split(" × ")
        attr = attr.strip()
        if attr == "EDU":
            attr = "Education (EDU)"
        elif attr == "APP":
            attr = "Appearance (APP)"
        total_points += attributes[attr] * int(multiplier)
    return total_points

# Main application
def main():
    init_db()  # Initialize the database
    st.title("Call of Cthulhu Character Creator")

    if "step" not in st.session_state:
        st.session_state.step = 1
    if "character" not in st.session_state:
        st.session_state.character = {}

    # Step 1: Input basic character info
    if st.session_state.step == 1:
        st.header("Step 1: Enter Basic Information")
        st.session_state.character["Name"] = st.text_input("Name", st.session_state.character.get("Name", ""))
        st.session_state.character["Age"] = st.text_input("Age", st.session_state.character.get("Age", ""))
        st.session_state.character["Gender"] = st.text_input("Gender", st.session_state.character.get("Gender", ""))
        st.session_state.character["Residence"] = st.text_input("Residence", st.session_state.character.get("Residence", ""))
        st.session_state.character["Background"] = st.text_area("Background/Description", st.session_state.character.get("Background", ""))
        if st.button("Proceed to Profession Selection"):
            if all(st.session_state.character.values()):
                st.session_state.step = 2
            else:
                st.error("Please complete all fields before proceeding.")

    # Step 2: Select profession
    elif st.session_state.step == 2:
        st.header("Step 2: Select Profession")
        profession_choice = st.selectbox("Choose your profession:", [p["Profession"] for p in professions_data])
        profession = next(p for p in professions_data if p["Profession"] == profession_choice)
        st.session_state.character["Profession"] = profession
        st.write(f"**Key Skills:** {profession['Key Skills']}")
        st.write(f"**Background:** {profession['Background']}")
        if st.button("Generate Attributes"):
            if "Attributes" not in st.session_state.character:
                st.session_state.character["Attributes"] = generate_character()
            st.session_state.step = 3

    # Step 3: Allocate skill points
    elif st.session_state.step == 3:
        st.header("Step 3: Allocate Skill Points")
        st.json(st.session_state.character["Attributes"])

        profession = st.session_state.character["Profession"]
        total_points = calculate_skill_points(profession, st.session_state.character["Attributes"])
        remaining_points = st.session_state.get("remaining_points", total_points)

        allocated_points = {}
        for skill in profession["Key Skills"]:
            max_points = remaining_points + st.session_state.character.get("Allocated Points", {}).get(skill, 0)
            allocated_points[skill] = st.slider(f"Allocate points to {skill}", 0, max_points, st.session_state.character.get("Allocated Points", {}).get(skill, 0))
            remaining_points -= allocated_points[skill] - st.session_state.character.get("Allocated Points", {}).get(skill, 0)

        st.session_state.character["Allocated Points"] = allocated_points
        st.session_state.remaining_points = remaining_points
        st.write(f"Remaining Points: {remaining_points}")

        if st.button("Finish Character Creation"):
            save_character_to_db(st.session_state.character)
            st.success("Character saved successfully!")
            st.download_button("Download as JSON", json.dumps(st.session_state.character), "character.json")
            st.download_button("Download as CSV", pd.DataFrame([st.session_state.character]).to_csv(index=False), "character.csv")

    # Step 4: View saved characters
    elif st.session_state.step == 4:
        st.header("Saved Characters")
        characters = load_characters_from_db()
        if characters:
            for char in characters:
                st.json({
                    "Name": char[1],
                    "Age": char[2],
                    "Gender": char[3],
                    "Residence": char[4],
                    "Background": char[5],
                    "Profession": char[6],
                    "Attributes": json.loads(char[7]),
                    "Allocated Points": json.loads(char[8]),
                })
        else:
            st.write("No characters saved yet.")

if __name__ == "__main__":
    main()
