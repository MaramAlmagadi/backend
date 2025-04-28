from flask import Flask, jsonify
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)

def generate_attendance_json():
    # Fetch CSV from Google Drive
    csv_url = "https://drive.google.com/uc?export=download&id=1lHpFWrloby5BMN3BChYnKdhpIFodMVNO"
    df = pd.read_csv(csv_url)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Columns to keep
    columns_to_keep = [
        "User ID", "First Name", "Last Name", "Middle Name", "Class ID",
        "Course ID", "Title", "Start Date/Time", "End Date/Time",
        "Venue", "Instructor First Name", "Instructor Last Name"
    ]
    df = df[columns_to_keep]

    # Clean timezone text
    df["Start Date/Time"] = df["Start Date/Time"].str.replace(r' [A-Za-z]+/[A-Za-z]+$', '', regex=True)
    df["End Date/Time"] = df["End Date/Time"].str.replace(r' [A-Za-z]+/[A-Za-z]+$', '', regex=True)

    # Convert date
    df["Start Date"] = pd.to_datetime(df["Start Date/Time"], format="%m/%d/%Y %H:%M:%S", errors='coerce').dt.date

    # Clean NaNs
    df = df.fillna("")

    # Build final JSON
    final_data = {}

    for date, date_group in df.groupby("Start Date"):
        date_str = str(date)
        day_name = date.strftime("%A")

        final_data[date_str] = {
            "day": day_name,
            "classes": {}
        }

        for class_id, class_group in date_group.groupby("Class ID"):
            class_info = class_group.iloc[0]
            students = class_group[["User ID", "First Name", "Middle Name", "Last Name"]].to_dict(orient="records")

            final_data[date_str]["classes"][str(class_id)] = {
                "title": class_info["Title"],
                "start_time": class_info["Start Date/Time"],
                "end_time": class_info["End Date/Time"],
                "venue": class_info["Venue"],
                "instructor": f"{class_info['Instructor First Name']} {class_info['Instructor Last Name']}",
                "students": students,
                "student_count": len(students)
            }

    return final_data

@app.route('/')
def home():
    return "Welcome to SGS Academy Attendance API 🚀"

@app.route('/attendance')
def attendance():
    attendance_json = generate_attendance_json()
    return jsonify(attendance_json)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
