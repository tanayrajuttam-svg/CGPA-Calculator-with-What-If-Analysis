# GradeIQ — Academic Intelligence Platform

> **Know your grades. Own your future.**

GradeIQ is a full-stack web application that helps students track their CGPA across semesters, simulate what-if grade scenarios, calculate target SGPA, and export a professional academic transcript — all in one place.

---

## 🚀 Live Demo

> Deployment coming soon on Railway + Netlify

---

## 📸 Screenshots

| Landing Page | Dashboard | PDF Export |
|---|---|---|
| Animated particle background with scrollable sections | Real-time CGPA, Chart.js trend, semester breakdown | Clean A4 transcript with course tables |

---

## ✨ Features

- 🔐 **User Authentication** — Secure register/login with bcrypt password hashing and JWT tokens
- 📊 **Live CGPA Calculation** — Weighted grade point average updates instantly on every add/delete
- 🤔 **What-If Analysis** — Simulate any hypothetical grade and see the CGPA impact in real time
- 🎯 **Target CGPA Calculator** — Enter your target and get the exact SGPA you need this semester
- 📅 **Semester-wise Breakdown** — SGPA for each semester with full course listing
- 📈 **SGPA Trend Chart** — Animated Chart.js line graph showing performance across semesters
- 📄 **PDF Transcript Export** — Download a professional A4 transcript with all courses and grades
- 🌌 **Animated Landing Page** — Particle + star system with mouse interactivity

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Backend | Python 3.14, Flask |
| Database | MySQL 8.0 |
| Authentication | Flask-JWT-Extended + bcrypt |
| Charts | Chart.js |
| PDF Export | ReportLab |
| Deployment | Railway (backend) + Netlify (frontend) |

---

## 📁 Project Structure

```
cgpa-calculator/
├── backend/
│   ├── app.py              # Flask app — all API routes
│   ├── db.py               # MySQL connection helper
│   ├── test_connection.py  # DB connection test script
│   ├── requirements.txt    # Python dependencies
│   └── Procfile            # Railway deployment config
├── frontend/
│   ├── index.html          # Landing page (scrollable, animated)
│   ├── login.html          # Login + Register page
│   └── dashboard.html      # Main app dashboard
└── schema.sql              # Database schema
```

---

## 🗄 Database Schema

```sql
-- Users table
CREATE TABLE users (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses table
CREATE TABLE courses (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    course_name  VARCHAR(100) NOT NULL,
    credits      FLOAT NOT NULL,
    grade        VARCHAR(5) NOT NULL,
    grade_points FLOAT NOT NULL,
    semester     INT NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🔌 API Routes

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/register` | ❌ | Register a new user |
| POST | `/login` | ❌ | Login and receive JWT token |
| GET | `/courses` | ✅ | Get all courses + CGPA |
| POST | `/courses` | ✅ | Add a new course |
| DELETE | `/courses/<id>` | ✅ | Delete a course |
| POST | `/whatif` | ✅ | Hypothetical CGPA simulation |
| POST | `/target` | ✅ | Calculate required SGPA |
| GET | `/semesters` | ✅ | Semester-wise breakdown |
| GET | `/export/pdf` | ✅ | Download PDF transcript |

> ✅ = Requires JWT token in `Authorization: Bearer <token>` header

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.10+
- MySQL 8.0
- Git

### Step 1 — Clone the repository
```bash
git clone https://github.com/yourusername/cgpa-calculator.git
cd cgpa-calculator
```

### Step 2 — Set up the database
```bash
mysql -u root -p < schema.sql
```

### Step 3 — Install Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 4 — Configure database connection
Edit `backend/db.py` and update your MySQL credentials:
```python
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="cgpa_db"
    )
```

### Step 5 — Start the Flask server
```bash
python app.py
```
Flask will run at `http://127.0.0.1:5000`

### Step 6 — Open the frontend
Open `frontend/index.html` in your browser.

---

## 🧮 CGPA Formula

```
CGPA = Σ(Credits × Grade Points) / Σ(Credits)
```

### Grade → Points Mapping

| Grade | Points |
|---|---|
| O | 10 |
| A+ | 9 |
| A | 8 |
| B+ | 7 |
| B | 6 |
| C | 5 |
| F | 0 |

---

## 🚀 Deployment

### Backend → Railway
1. Push code to GitHub
2. Connect repo to [Railway](https://railway.app)
3. Set environment variables (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET_KEY`)
4. Railway auto-deploys on every push

### Frontend → Netlify
1. Update `API` variable in `dashboard.html` to your Railway URL
2. Drag and drop `frontend/` folder to [Netlify](https://netlify.com)
3. Done — live in 2 minutes

---

## 🔮 Upcoming Features

- [ ] Edit course grades
- [ ] Grade distribution pie chart
- [ ] Dark / Light mode toggle
- [ ] Grade predictor for remaining exams
- [ ] Course search and filter
- [ ] Share transcript via public link

---

## 👨‍💻 Author

**Tanay**
- Built with Flask + MySQL + Vanilla JS
- Project: GradeIQ — Academic Intelligence Platform

---

## 📄 License

This project is built for educational purposes as a college portfolio project.
