from flask import Flask, jsonify
import pandas as pd
import requests
from io import StringIO

app = Flask(__name__)

# Google Drive Direct Download Link
GOOGLE_DRIVE_CSV_LINK = "https://drive.google.com/uc?export=download&id=1lHpFWrloby5BMN3BChYnKdhpIFodMVNO"

@app.route('/')
def home():
    return '✅ Welcome to SGS Academy Attendance API 🚀'

@app.route('/attendance', methods=['GET'])
def get_attendance():
    try:
        # Fetch CSV from Google Drive
        response = requests.get(GOOGLE_DRIVE_CSV_LINK)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download CSV file."}), 500

        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)

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

        # Convert dates
        df["Start Date"] = pd.to_datetime(df["Start Date/Time"], format="%m/%d/%Y %H:%M:%S", errors='coerce').dt.date

        # Fill missing values
        df = df.fillna("")

        # Build final JSON structure
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

        return jsonify(final_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
