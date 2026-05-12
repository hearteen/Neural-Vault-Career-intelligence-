from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import joblib  # <--- IDHU MUKKIYAM
import numpy as np # <--- IDHU MUKKIYAM
import os
import csv
import io
import secrets
from flask import make_response
app = Flask(__name__)
app.secret_key = 'your_secret_key'


# --- 🎓 Complete Subject Intelligence Mapping (Sem 1-6) ---
SUBJECT_MAP = {
    1: {
        't1': 'Tamil-I', 't2': 'English-I', 't3': 'Programming in C', 
        't4': 'Digital Logic', 't5': 'Allied Maths-I', 't6': 'Prof. English-I', 
        'p1': 'C Practical', 'p2': 'Value Education'
    },
    2: {
        't1': 'Tamil-II', 't2': 'English-II', 't3': 'Object Oriented Programming', 
        't4': 'Microprocessor', 't5': 'Allied Maths-II', 't6': 'Environmental Studies', 
        'p1': 'OOP Practical', 'p2': 'Professional English-II'
    },
    3: {
        't1': 'Tamil-III', 't2': 'English-III', 't3': 'Data Structures', 
        't4': 'Java Programming', 't5': 'Financial Accounting', 't6': 'Soft Skills', 
        'p1': 'Data Structures Practical', 'p2': 'Java Practical'
    },
    4: {
        't1': 'Tamil-IV', 't2': 'English-IV', 't3': 'Internet Programming', 
        't4': 'Computer Architecture', 't5': 'Statistical Methods', 't6': 'Modern Banking', 
        'p1': 'IP Practical', 'p2': 'Statistics Practical'
    },
    5: {
        't1': 'RDBMS', 't2': 'Web Graphics', 't3': 'Software Engineering', 
        't4': 'Computer Networks', 't5': 'Open Source Tech (PHP)', 't6': 'Python Programming', 
        'p1': 'Oracle Practical', 'p2': 'Web Graphics Practical'
    },
    6: {
        't1': 'Operating Systems', 't2': 'Data Mining', 't3': 'Mobile Computing', 
        't4': 'Information Security', 't5': 'Software Testing', 't6': 'Cloud Computing', 
        'p1': 'OS Practical', 'p2': 'Project Work'
    }
}

# 🗄️ MySQL Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="", 
        database="student_intelligence",
        buffered=True  # <--- Ippo indha line "Unread Result" error-ah fix pannidum
    )
# --- ML Models Loading ---
# Model files correct-ana folder-la irukkanu check pannunga
try:
    perf_model = joblib.load('student_model.pkl')
    career_model = joblib.load('career_model.pkl')
    print("✅ All AI Models Loaded Successfully")
except Exception as e:
    perf_model = None
    career_model = None
    print(f"⚠️ Model Loading Error: {e}")

# 1. Route: Index ERP Login Page
@app.route('/')
def index():
    return render_template('index.html')

# 2. Route: Login Logic
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # User-ah check panrom (Admin or Student)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role'] # 'admin' or 'student'
        
        cursor.close()
        db.close()

        # Role base panni redirect panrom
        if user['role'] == 'admin':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    else:
        flash('Invalid Username or Password!')
        return redirect(url_for('index'))

# 3. Route: Admin Dashboard
# Dashboard-la Real Attendance Percentage kaatta indha logic-ah update pannunga
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as total FROM students")
        result_count = cursor.fetchone()
        student_count = result_count['total'] if result_count else 0

        # Overall Institution Average Attendance
        query = """
            SELECT (COUNT(CASE WHEN status='Present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)) as avg_att 
            FROM attendance_db.attendance_log
        """
        cursor.execute(query)
        result_att = cursor.fetchone()
        avg_attendance = round(result_att['avg_att'], 1) if result_att and result_att['avg_att'] else 0

        cursor.close()
        db.close()

        return render_template('dashboard.html', 
                               username=session['username'], 
                               student_count=student_count,
                               avg_attendance=avg_attendance)
                               
    except Exception as e:
        print(f"Admin Dashboard Error: {e}")
        return render_template('dashboard.html', username=session['username'], student_count=0, avg_attendance=0)
    
# 4. Route: ML Performance Prediction
@app.route('/predict/<roll_no>')
def predict(roll_no):
    if 'user_id' not in session: return redirect(url_for('index'))
    
    # Inga logic-ah unga student_model requirements-ku thagapadi mathikkalam
    result_text = "Analysis Pending"
    if perf_model:
        sample_input = np.array([[90, 8.5, 80, 9]]) # Format: Attendance, GPA, Skills, Behavior
        prediction = perf_model.predict(sample_input)[0]
        result_text = "Good Standing" if prediction == 1 else "Performance Alert"
    
    return render_template('prediction.html', result=result_text, username=session['username'])
# 5. Route: Career Recommendation
@app.route('/career_recommendation/<roll_no>')
def career_recommendation(roll_no):
    if 'user_id' not in session: return redirect(url_for('index'))
    
    roles = {0: 'Data Scientist', 1: 'Project Manager', 2: 'Web Developer'}
    try:
        if career_model:
            sample_input = np.array([[8.5, 90, 75, 95]]) 
            prediction = career_model.predict(sample_input)[0]
            suggested_role = roles.get(prediction, "Technology Analyst")
        else:
            suggested_role = "AI Model Offline"

        return render_template('career_rec.html', role=suggested_role, username=session['username'])
    except Exception as e:
        return f"Prediction Error: {e}"
    
@app.route('/register_students')
def register_students():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('register_students.html', username=session['username'])

@app.route('/upload_marks', methods=['POST']) # HTML-la irukura action name
def upload_marks():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    # HTML-la name="csv_file" nu kuduthurukkuradhala ingayum adhe name irukanum
    file = request.files.get('csv_file') 
    
    if not file:
        flash('❌ No file selected!')
        return redirect(url_for('admin_dashboard')) # Dashboard-ke redirect pannunga

    db = get_db_connection()
    cursor = db.cursor()

    try:
        # File reading logic
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        success_count = 0
        
        for row in csv_input:
            # Case-insensitive headers handle panna
            row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            current_roll = row['roll_no']
            
            # Marks extraction (T1 to T6 and P1 to P2)
            t_raw = [row.get(f't{i}', '').strip().upper() for i in range(1, 7)]
            p_raw = [row.get(f'p{i}', '').strip().upper() for i in range(1, 3)]
            all_raw = t_raw + p_raw
            
            # Marks Conversion & Pass Check
            active_marks = []
            db_marks = []
            is_absent = any(m in ['AAA', 'ABSENT', 'A'] for m in all_raw if m)
            
            for m in all_raw:
                if m == '' or m is None:
                    db_marks.append(None)
                    active_marks.append(None)
                elif m in ['AAA', 'ABSENT', 'A']:
                    active_marks.append(0.0)
                    db_marks.append(0)
                else:
                    val = float(m)
                    active_marks.append(val)
                    db_marks.append(val)

            # --- Status Logic ---
            if is_absent:
                final_status = 'ABSENT'
            # Unga priority: Pass Mark 30 (as mentioned in UI)
            elif any(m < 30 for m in active_marks if m is not None): 
                final_status = 'FAIL'
            else:
                final_status = 'PASS'

            semester = int(row.get('semester', 1))
            year = (semester + 1) // 2 
            
            # GPA Calculation
            valid_marks = [m for m in active_marks if m is not None]
            calculated_gpa = round((sum(valid_marks) / (len(valid_marks) * 100)) * 10, 2) if valid_marks else 0.0

            # DB Update: marks_register table
            query_marks = """
                INSERT INTO marks_register 
                (roll_no, semester, year, t1, t2, t3, t4, t5, t6, p1, p2, calculated_gpa, result) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                t1=%s, t2=%s, t3=%s, t4=%s, t5=%s, t6=%s, p1=%s, p2=%s, calculated_gpa=%s, result=%s
            """
            cursor.execute(query_marks, (
                current_roll, semester, year, *db_marks, calculated_gpa, final_status,
                *db_marks, calculated_gpa, final_status
            ))
            
            success_count += 1
        
        db.commit() 
        flash(f'✅ {success_count} Records Synced Successfully!')

    except Exception as e:
        db.rollback() 
        flash(f'❌ Error: {e}')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('dashboard'))



@app.route('/upload_students', methods=['POST'])
def upload_students():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    file = request.files.get('student_csv')
    if not file:
        flash('❌ No file uploaded!')
        return redirect(url_for('register_students'))

    db = get_db_connection()
    cursor = db.cursor()

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        success_count = 0
        
        for row in csv_input:
            row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            current_roll = row['roll_no']
            
            # --- 💡 Step A: Logic for Dynamic Subjects & Absenteeism ---
            t_raw = [row.get(f't{i}', '').strip().upper() for i in range(1, 7)]
            p_raw = [row.get(f'p{i}', '').strip().upper() for i in range(1, 3)]
            all_raw = t_raw + p_raw
            
            # Absent check
            is_absent = any(m in ['AAA', 'ABSENT', 'A'] for m in all_raw if m)
            
            # Marks Conversion logic
            active_marks = []
            db_marks = [] # Database-ku poga vendiya values
            
            for m in all_raw:
                if m == '' or m is None:
                    db_marks.append(None)
                elif m in ['AAA', 'ABSENT', 'A']:
                    active_marks.append(0.0) # Calculation-ku 0
                    db_marks.append(0)       # DB-la 0 store aagum
                else:
                    val = float(m)
                    active_marks.append(val)
                    db_marks.append(val)

            # --- 💡 Step B: Status Determination ---
            if is_absent:
                final_status = 'ABSENT'
            elif any(m < 40 for m in active_marks if m is not None): # Pass mark 40
                final_status = 'FAIL'
            else:
                final_status = 'PASS'

            # Semester and GPA Logic
            semester = int(row.get('semester', 1))
            year = (semester + 1) // 2 
            
            # GPA Calculation (Excluding NULL slots)
            valid_marks = [m for m in active_marks if m is not None]
            calculated_gpa = round((sum(valid_marks) / (len(valid_marks) * 100)) * 10, 2) if valid_marks else 0.0

            # --- 💡 Step C: Database Sync ---
            # Update Master Students Table
            cursor.execute("""
                INSERT INTO students (name, email, roll_no, department, batch, gpa, attendance) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE gpa = %s, attendance = %s
            """, (row['name'], row['email'], current_roll, row['department'], 
                  row['batch'], calculated_gpa, row['attendance'], calculated_gpa, row['attendance']))

            # Update Marks Register with Status
            query_marks = """
                INSERT INTO marks_register 
                (roll_no, semester, year, t1, t2, t3, t4, t5, t6, p1, p2, calculated_gpa, result) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                t1=%s, t2=%s, t3=%s, t4=%s, t5=%s, t6=%s, p1=%s, p2=%s, calculated_gpa=%s, result=%s
            """
            cursor.execute(query_marks, (
                current_roll, semester, year, *db_marks, calculated_gpa, final_status,
                *db_marks, calculated_gpa, final_status
            ))

            # Create User Login
            cursor.execute("INSERT IGNORE INTO users (username, password, role) VALUES (%s, %s, 'student')", 
                           (current_roll, current_roll))
            
            success_count += 1
        
        db.commit() 
        flash(f'✅ {success_count} Records Processed (Status: Pass/Fail/Absent synced)')

    except Exception as e:
        db.rollback() 
        flash(f'❌ Error: {e}')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('register_students'))


# --- 7. Route: Manual Student Registration ---
# 1. Manual Registration with Automatic User Account Creation
@app.route('/add_student_manual', methods=['POST'])
def add_student_manual():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    name = request.form.get('name')
    roll_no = request.form.get('roll_no')
    department = request.form.get('department')
    gpa = request.form.get('gpa')
    attendance = request.form.get('attendance')

    db = get_db_connection()
    cursor = db.cursor()

    try:
        # A. Students Table-la insert panrom
        query_student = """INSERT INTO students (name, roll_no, department, gpa, attendance) 
                           VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(query_student, (name, roll_no, department, gpa, attendance))
        
        # B. Users Table-la login account create panrom
        # Default password: 'password123'
        query_user = """INSERT INTO users (username, password, role) 
                        VALUES (%s, %s, 'student')"""
        cursor.execute(query_user, (roll_no, 'password123'))
        
        db.commit() # Rendu table-layum success aana dhaan save aagum
        flash(f'✅ Student {name} registered and Login account created!')
        return redirect(url_for('dashboard'))

    except Exception as e:
        db.rollback() # Error vandha change-ah cancel pannidum
        flash(f'❌ Manual Registration Error: {e}')
        return redirect(url_for('register_students'))
    finally:
        cursor.close()
        db.close()

# 2. Updated Student Profile with Database Sync
@app.route('/student_profile/<roll_no>')
def student_profile(roll_no):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Step A: Fetch Student Info using JOIN to ensure they exist in both tables
        query = """
            SELECT s.*, u.role FROM students s
            JOIN users u ON s.roll_no = u.username
            WHERE s.roll_no = %s
        """
        cursor.execute(query, (roll_no,))
        student = cursor.fetchone()

        if not student:
            return "Student profile or login account not found!"

        # Step B: Fetch Live Attendance Stats from attendance_db
        cursor.execute("""
            SELECT 
                COUNT(*) as total_days,
                COUNT(CASE WHEN status='Present' THEN 1 END) as present_days
            FROM attendance_db.attendance_log 
            WHERE student_id = %s
        """, (roll_no,))
        
        att_stats = cursor.fetchone()
        
        # Attendance Percentage Calculation
        calc_attendance = 0
        if att_stats and att_stats['total_days'] > 0:
            calc_attendance = round((att_stats['present_days'] / att_stats['total_days']) * 100, 1)

        cursor.close()
        db.close()

        # Render Profile with Data
        return render_template('student_profile.html', 
                               student=student, 
                               attendance=calc_attendance)

    except Exception as e:
        print(f"Profile Fetch Error: {e}")
        return f"Error fetching profile: {e}"    

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('index'))
    
    roll_no = session.get('username') 
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # 1. Fetch Student Basic Info
        cursor.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
        student_record = cursor.fetchone() 

        # 2. Fetch Complete Marks History
        cursor.execute("SELECT * FROM marks_register WHERE roll_no = %s ORDER BY semester ASC", (roll_no,))
        all_marks = cursor.fetchall()

        # 3. Calculate Arrears & Skills for AI Insight
        arrears_count = 0
        total_p = 0
        top_skills = []

        if all_marks:
            for sem_data in all_marks:
                # Arrear detection (Based on result column)
                if sem_data.get('result') in ['FAIL', 'ABSENT', 'AAA']:
                    arrears_count += 1
                
                # Practical marks sum for model input (Skills)
                total_p += (float(sem_data.get('p1') or 0) + float(sem_data.get('p2') or 0))

                # Identify strengths >= 75 for Career Reasoning
                s_num = sem_data.get('semester')
                if s_num in SUBJECT_MAP:
                    for col in ['t1','t2','t3','t4','t5','t6','p1','p2']:
                        mark = sem_data.get(col)
                        if mark and float(mark) >= 75:
                            sub_name = SUBJECT_MAP[s_num].get(col)
                            top_skills.append(sub_name)

        # 4. Live Attendance Calculation
        # Note: roll_no is used to match student_id in attendance logs
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   COUNT(CASE WHEN status='Present' THEN 1 END) as presents 
            FROM attendance_db.attendance_log WHERE student_id = %s
        """, (roll_no,))
        att_data = cursor.fetchone()
        calc_attendance = round((att_data['presents'] / att_data['total'] * 100), 1) if att_data and att_data['total'] > 0 else 0

        # 5. Advanced Neural Prediction (RandomForest Classifier Match)
        current_gpa = float(student_record['gpa']) if student_record and student_record['gpa'] else 0.0
        avg_practical = total_p / (len(all_marks) * 2) if (all_marks and len(all_marks) > 0) else 0
        
        # Scaling GPA to 0-100 to match Trainer's 'marks' feature
        gpa_as_marks = current_gpa * 10
        # Behavior Score logic: Starts at 10, drops per arrear (min 2 for active students)
        behavior_score = max(2, 10 - arrears_count)
        
        status_text = "Good Standing"
        if perf_model:
            try:
                # Features Order must match model_trainer.py: [attendance, marks, skills, behavior]
                input_features = np.array([[
                    float(calc_attendance), 
                    float(gpa_as_marks), 
                    float(avg_practical), 
                    float(behavior_score)
                ]])
                
                # Model returns 0 (At Risk) or 1 (Good)
                pred_class = perf_model.predict(input_features)[0]
                
                if pred_class == 1:
                    # If model says 'Good', we predict a slight growth trend
                    predicted_gpa = round(current_gpa + 0.25, 2)
                    status_text = "Good Standing"
                else:
                    # If model says 'At Risk', we predict a drop trend
                    predicted_gpa = round(current_gpa - 0.4, 2)
                    status_text = "Performance Alert"
                
                # Cap the GPA at 10.0
                predicted_gpa = min(10.0, predicted_gpa)
                
            except Exception as model_err:
                print(f"🤖 Model Error: {model_err}")
                predicted_gpa = current_gpa
        else:
            predicted_gpa = round(current_gpa + 0.1, 2)

        # 6. Intelligent Career Insight Reasoning
        career_suggestion = "Technology Analyst" 
        career_reason = "Based on your overall academic trajectory."
        
        web_skills = [s for s in top_skills if any(kw in s for kw in ['Web', 'Internet', 'PHP'])]
        prog_skills = [s for s in top_skills if any(kw in s for kw in ['Python', 'Java', 'C', 'Data Structures'])]
        data_skills = [s for s in top_skills if any(kw in s for kw in ['Statistics', 'Data Mining', 'RDBMS'])]

        if web_skills:
            career_suggestion = "Full-Stack Web Developer"
            career_reason = f"Excellent proficiency in {', '.join(web_skills[:2])}."
        elif prog_skills:
            career_suggestion = "Software Engineer"
            career_reason = f"Strong core programming foundation in {', '.join(prog_skills[:2])}."
        elif data_skills:
            career_suggestion = "Data Analyst"
            career_reason = f"Highly analytical; excels in {data_skills[0]}."

    except Exception as e:
        print(f"🔥 Dashboard Error: {e}")
        calc_attendance, predicted_gpa, career_suggestion, career_reason, status_text, arrears_count, all_marks = 0, 0, "Offline", "Error", "Error", 0, []
        student_record = None
    finally:
        cursor.close()
        db.close()

    return render_template('student_dashboard.html', 
                           student=student_record, 
                           marks_history=all_marks, 
                           attendance_percent=calc_attendance,
                           predicted_gpa=predicted_gpa,
                           career=career_suggestion,
                           career_reason=career_reason,
                           status=status_text,
                           arrears=arrears_count)

@app.route('/search_student', methods=['POST'])
def search_student():
    roll_no = request.form.get('roll_no')
    if roll_no:
        # Student profile page-ku direct-ah redirect pannum
        return redirect(url_for('view_student_profile', roll_no=roll_no))
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/search', methods=['POST'])
def admin_search():
    roll_no = request.form.get('roll_no').strip()
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Student database-la irukkaangala-nu check pannuvom
    cursor.execute("SELECT roll_no FROM students WHERE roll_no = %s", (roll_no,))
    student = cursor.fetchone()
    cursor.close()
    db.close()

    if student:
        # Student irundha, avanga profile page-ku redirect pannunga
        # Note: 'view_student' nu neenga enna function name vachirukingalo adhai kudunga
        return redirect(url_for('view_student_profile', roll_no=roll_no)) 
    else:
        # Student illana, oru error message-oda dashboard-ke thiruppi anupunga
        flash("Student Roll No not found!", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/view_student_profile/<roll_no>')
def view_student_profile(roll_no):
    # Indha function name 'view_student_profile' nu irundha dhaan url_for work aagum
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
        student = cursor.fetchone()
        
        # Simple attendance calculation for admin view
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   COUNT(CASE WHEN status='Present' THEN 1 END) as presents 
            FROM attendance_db.attendance_log WHERE student_id = %s
        """, (roll_no,))
        att_data = cursor.fetchone()
        calc_attendance = round((att_data['presents'] / att_data['total'] * 100), 1) if att_data and att_data['total'] > 0 else 0

        return render_template('view_student_profile.html', 
                               student=student, 
                               attendance_percent=calc_attendance,
                               status="Good Standing" if calc_attendance >= 75 else "Performance Alert",
                               career="Technology Analyst", 
                               career_reason="Based on academic records")
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('admin_dashboard'))
    finally:
        cursor.close()
        db.close()


@app.route('/edit_student/<roll_no>', methods=['GET', 'POST'])
def edit_student(roll_no):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        # Update logic (idhu neenga munnadiye vachirupinga)
        name = request.form['name']
        dept = request.form['department']
        gpa = request.form['gpa']
        cursor.execute("UPDATE students SET name=%s, department=%s, gpa=%s WHERE roll_no=%s", 
                       (name, dept, gpa, roll_no))
        db.commit()
        db.close()
        return redirect(url_for('view_student_profile', roll_no=roll_no))

    # --- IDHU DHAAN MUKKIYAM ---
    # GET request varumbodu, andha student data-va fetch panni HTML-ku anupuroam
    cursor.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
    student_data = cursor.fetchone()
    cursor.close()
    db.close()

    if not student_data:
        return "Student not found", 404

    # 'student' nu dhaan HTML-la access pandroam, so same name use pannunga
    return render_template('edit_student.html', student=student_data)

@app.route('/semester_marks')
def semester_marks():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('index'))
    
    roll_no = session.get('username')
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Fetching all semester records for the logged-in student
        cursor.execute("SELECT * FROM marks_register WHERE roll_no = %s ORDER BY semester ASC", (roll_no,))
        all_sem_marks = cursor.fetchall()
        
        # Student basic info (Name, Dept)
        cursor.execute("SELECT name, department, roll_no FROM students WHERE roll_no = %s", (roll_no,))
        student_info = cursor.fetchone()

    except Exception as e:
        print(f"Error fetching marks: {e}")
        all_sem_marks = []
        student_info = None
    finally:
        cursor.close()
        db.close()

    # Passing SUBJECT_MAP to HTML to convert t1, t2 to real names
    return render_template('semester_marks.html', 
                           marks=all_sem_marks, 
                           student=student_info,
                           subject_map=SUBJECT_MAP)

@app.route('/academic_trajectory')
def academic_trajectory():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('index'))
    
    roll_no = session.get('username')
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # 1. Fetch Student Info (Idhu dhaan Header-ku romba mukkiyamaana data)
        cursor.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
        student_record = cursor.fetchone() 

        # 2. Fetching Semester and GPA for the graph
        cursor.execute("SELECT semester, calculated_gpa FROM marks_register WHERE roll_no = %s ORDER BY semester ASC", (roll_no,))
        data = cursor.fetchall()
        
        # Formatting data for JavaScript (ApexCharts)
        semesters = [f"Sem {row['semester']}" for row in data]
        gpas = [float(row['calculated_gpa']) for row in data]
        
        # 3. Render template with 'student' variable
        return render_template('trajectory.html', 
                               semesters=semesters, 
                               gpas=gpas, 
                               student=student_record) # 'student' nu pass panna dhaan header-la error varaadhu

    except Exception as e:
        print(f"Error in Academic Trajectory: {e}")
        # Error vandha dashboard-ke thirumba anupuvom
        return redirect(url_for('student_dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/career_insight')
def career_insight():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('index'))
    
    roll_no = session.get('username')
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Fetch data for AI analysis
        cursor.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
        student = cursor.fetchone()
        
        cursor.execute("SELECT * FROM marks_register WHERE roll_no = %s", (roll_no,))
        marks = cursor.fetchall()

        # Simple Logic to find Top Skills (Example: Marks > 80 in specific subjects)
        skills = []
        if marks:
            for m in marks:
                sem = m['semester']
                for key in ['t1','t2','t3','t4','t5','t6','p1','p2']:
                    if m[key] and float(m[key]) >= 80:
                        skills.append(SUBJECT_MAP[sem].get(key))
        
        # Unique skills only
        skills = list(set(skills))[:5] 

    except Exception as e:
        print(f"Error: {e}")
        student, skills = None, []
    finally:
        cursor.close()
        db.close()

    return render_template('career_insight.html', student=student, skills=skills)
# 6. Route: Logout
@app.route('/logout')
def logout():
    session.clear()
    # Flash message kudutha innum nalla irukkum
    flash('You have been logged out successfully.', 'info')
    
    # Response-ah create panni cache-ah clear panroam
    response = make_response(redirect(url_for('index')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)