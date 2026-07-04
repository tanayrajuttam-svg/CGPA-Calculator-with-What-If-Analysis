from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import bcrypt
import io
import os
from db import get_connection
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

app = Flask(__name__)
CORS(app, origins=[
    "https://stellular-sprite-c8c016.netlify.app",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5000"
], supports_credentials=True)

# JWT Config
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "gradeiq-secret-key-2026")
jwt = JWTManager(app)

# Grade to points mapping
GRADE_POINTS = {
    "O": 10, "A+": 9, "A": 8,
    "B+": 7, "B": 6, "C": 5, "F": 0
}

# --- Register ---
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, hashed.decode("utf-8"))
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- Login ---
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        # Create JWT token with user_id as identity
        token = create_access_token(identity=str(user["id"]))
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user_id": user["id"],
            "username": user["username"]
        }), 200
    else:
        return jsonify({"error": "Incorrect password"}), 401

# --- Add a course ---
@app.route("/courses", methods=["POST"])
@jwt_required()
def add_course():
    user_id = get_jwt_identity()
    data = request.json
    course_name = data.get("course_name")
    credits = data.get("credits")
    grade = data.get("grade", "").upper()
    semester = data.get("semester")

    if not all([course_name, credits, grade, semester]):
        return jsonify({"error": "All fields required"}), 400

    if grade not in GRADE_POINTS:
        return jsonify({"error": f"Invalid grade. Use: {list(GRADE_POINTS.keys())}"}), 400

    grade_points = GRADE_POINTS[grade]

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO courses (user_id, course_name, credits, grade, grade_points, semester) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, course_name, credits, grade, grade_points, semester)
        )
        conn.commit()
        return jsonify({"message": "Course added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- Get all courses + CGPA ---
@app.route("/courses", methods=["GET"])
@jwt_required()
def get_courses():
    user_id = get_jwt_identity()
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE user_id = %s ORDER BY semester", (user_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    cgpa = calculate_cgpa(courses)
    return jsonify({"courses": courses, "cgpa": cgpa})

# --- Delete a course ---
@app.route("/courses/<int:course_id>", methods=["DELETE"])
@jwt_required()
def delete_course(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Course deleted"})

# --- Edit a course ---
@app.route("/courses/<int:course_id>", methods=["PUT"])
@jwt_required()
def edit_course(course_id):
    data = request.json
    course_name = data.get("course_name")
    credits = data.get("credits")
    grade = data.get("grade", "").upper()
    semester = data.get("semester")

    if not all([course_name, credits, grade, semester]):
        return jsonify({"error": "All fields required"}), 400

    if grade not in GRADE_POINTS:
        return jsonify({"error": "Invalid grade"}), 400

    grade_points = GRADE_POINTS[grade]

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE courses SET course_name=%s, credits=%s, grade=%s, grade_points=%s, semester=%s WHERE id=%s",
            (course_name, credits, grade, grade_points, semester, course_id)
        )
        conn.commit()
        return jsonify({"message": "Course updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- What-If Analysis ---
@app.route("/whatif", methods=["POST"])
@jwt_required()
def what_if():
    user_id = get_jwt_identity()
    data = request.json
    grade = data.get("grade", "").upper()
    credits = data.get("credits")

    if grade not in GRADE_POINTS:
        return jsonify({"error": "Invalid grade"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE user_id = %s", (user_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    hypothetical = {"credits": credits, "grade_points": GRADE_POINTS[grade]}
    new_cgpa = calculate_cgpa(courses + [hypothetical])
    return jsonify({"hypothetical_cgpa": new_cgpa})

# --- Target CGPA ---
@app.route("/target", methods=["POST"])
@jwt_required()
def target_cgpa():
    user_id = get_jwt_identity()
    data = request.json
    target = data.get("target_cgpa")
    sem_credits = data.get("semester_credits")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE user_id = %s", (user_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    current_credits = sum(c["credits"] for c in courses)
    current_weighted = sum(c["credits"] * c["grade_points"] for c in courses)

    needed_weighted = (target * (current_credits + sem_credits)) - current_weighted
    needed_sgpa = round(needed_weighted / sem_credits, 2)

    if needed_sgpa > 10:
        return jsonify({"message": "Target not achievable this semester", "needed_sgpa": needed_sgpa})
    return jsonify({"needed_sgpa": needed_sgpa})

# --- Semester Breakdown ---
@app.route("/semesters", methods=["GET"])
@jwt_required()
def semester_breakdown():
    user_id = get_jwt_identity()
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE user_id = %s ORDER BY semester", (user_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    semesters = {}
    for c in courses:
        sem = c["semester"]
        if sem not in semesters:
            semesters[sem] = []
        semesters[sem].append(c)

    result = {}
    for sem, sem_courses in semesters.items():
        result[sem] = {
            "courses": sem_courses,
            "sgpa": calculate_cgpa(sem_courses)
        }
    return jsonify(result)

# --- PDF Export ---
@app.route("/export/pdf", methods=["GET"])
@jwt_required()
def export_pdf():
    user_id = get_jwt_identity()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM courses WHERE user_id = %s ORDER BY semester", (user_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    cgpa = calculate_cgpa(courses)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm)

    elements = []

    header_style = ParagraphStyle('header',
        fontSize=28, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#7c6bff'),
        spaceAfter=2, leading=32)
    tagline_style = ParagraphStyle('tagline',
        fontSize=11, fontName='Helvetica',
        textColor=colors.HexColor('#999999'),
        spaceAfter=0)

    elements.append(Paragraph("GradeIQ", header_style))
    elements.append(Paragraph("Academic Transcript", tagline_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(HRFlowable(width="100%", thickness=1.5,
        color=colors.HexColor('#7c6bff'), spaceAfter=6*mm))

    info_data = [
        ['Student', user['username']],
        ['Total Courses', str(len(courses))],
        ['Total Credits', str(sum(c['credits'] for c in courses))],
        ['Overall CGPA', str(cgpa)],
    ]
    info_table = Table(info_data, colWidths=[50*mm, 120*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#555555')),
        ('TEXTCOLOR', (1,0), (1,-2), colors.HexColor('#222222')),
        ('TEXTCOLOR', (1,3), (1,3), colors.HexColor('#7c6bff')),
        ('FONTNAME', (1,3), (1,3), 'Helvetica-Bold'),
        ('FONTSIZE', (1,3), (1,3), 13),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.HexColor('#eeeeee')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    semesters = {}
    for c in courses:
        sem = c['semester']
        if sem not in semesters:
            semesters[sem] = []
        semesters[sem].append(c)

    for sem, sem_courses in sorted(semesters.items()):
        sgpa = calculate_cgpa(sem_courses)
        elements.append(Paragraph(f"Semester {sem}   —   SGPA: {sgpa}",
            ParagraphStyle('sem', fontSize=12, fontName='Helvetica-Bold',
                textColor=colors.HexColor('#38bdf8'), spaceAfter=8)))

        course_name_style = ParagraphStyle('cn',
            fontSize=9, fontName='Helvetica',
            textColor=colors.HexColor('#333333'),
            leading=13, wordWrap='CJK')
        header_cn_style = ParagraphStyle('hcn',
            fontSize=10, fontName='Helvetica-Bold',
            textColor=colors.white, leading=13)

        table_data = [[
            Paragraph('Course Name', header_cn_style),
            Paragraph('Credits', header_cn_style),
            Paragraph('Grade', header_cn_style),
            Paragraph('Points', header_cn_style),
        ]]
        for c in sem_courses:
            table_data.append([
                Paragraph(c['course_name'], course_name_style),
                Paragraph(str(c['credits']), ParagraphStyle('cv', fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#333333'), alignment=1)),
                Paragraph(c['grade'], ParagraphStyle('gv', fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#7c6bff'), alignment=1)),
                Paragraph(str(c['grade_points']), ParagraphStyle('gpv', fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#333333'), alignment=1)),
            ])

        t = Table(table_data, colWidths=[100*mm, 25*mm, 25*mm, 25*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#7c6bff')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f9f9f9'), colors.white]),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (0,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e0e0e0')),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 8*mm))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf',
        download_name=f'GradeIQ_Transcript_{user["username"]}.pdf')

# --- Helper: Calculate CGPA ---
def calculate_cgpa(courses):
    total_credits = sum(c["credits"] for c in courses)
    if total_credits == 0:
        return 0
    weighted = sum(c["credits"] * c["grade_points"] for c in courses)
    return round(weighted / total_credits, 2)

if __name__ == "__main__":
    app.run(debug=True)
