import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps
import json

from models import (
    db, User, Course, Enrollment, Module, Assignment, Quiz, 
    Announcement, Discussion, DiscussionPost, Message, Notification, StudyGroup,
    SubmittedAssignment, QuizAttempt, QuizQuestion, QuizResponse, UserRole,
    CalendarEvent
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize extensions
db.init_app(app)
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== AUTHENTICATION ROUTES ====================

@app.before_request
def auto_login():
    if not current_user.is_authenticated and request.endpoint != 'static':
        # Default to the primary teacher account for testing admin features
        user = User.query.filter_by(username='prof_jadhav').first()
        if not user:
            user = User.query.first()
        if user:
            login_user(user)

@app.route('/switch_user/<username>')
def switch_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        login_user(user)
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already exists')
        
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole[role.upper()]
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ==================== DASHBOARD ROUTES ====================

@app.route('/')
@login_required
def dashboard():
    # Get courses based on role
    if current_user.role == UserRole.TEACHER:
        courses = current_user.courses_teaching.all()
        course_ids = [c.id for c in courses]
    else:
        enrollments = current_user.enrollments.all()
        courses = [e.course for e in enrollments]
        course_ids = [e.course_id for e in enrollments]
    
    # Get upcoming assignments
    upcoming_assignments = db.session.query(Assignment).join(Course).filter(
        Course.id.in_(course_ids),
        Assignment.due_date > datetime.utcnow(),
        Assignment.due_date <= datetime.utcnow() + timedelta(days=30)
    ).order_by(Assignment.due_date).limit(5).all()
    
    # Get notifications
    notifications = current_user.notifications.filter_by(is_read=False).limit(10).all()
    
    # Get recent announcements
    announcements = db.session.query(Announcement).join(Course).filter(
        Course.id.in_(course_ids)
    ).order_by(Announcement.created_at.desc()).limit(5).all()
    
    # Get calendar events
    calendar_events = []
    for assignment in db.session.query(Assignment).join(Course).filter(
        Course.id.in_(course_ids),
        Assignment.due_date >= datetime.utcnow()
    ).all():
        calendar_events.append({
            'type': 'assignment',
            'title': f"Due: {assignment.title}",
            'date': assignment.due_date.strftime('%Y-%m-%d'),
            'course': assignment.course.code
        })
    
    # Calculate GPA / attendance (student only)
    gpa = current_user.get_gpa() if current_user.role == UserRole.STUDENT else 0.0
    
    if current_user.role == UserRole.STUDENT:
        enrollments = current_user.enrollments.all()
        total_classes = sum(e.total_classes for e in enrollments)
        total_attended = sum(e.attendance_count for e in enrollments)
        attendance_pct = int((total_attended / total_classes * 100) if total_classes > 0 else 0)
    else:
        attendance_pct = 0
    
    return render_template(
        'dashboard_modern.html',
        courses=courses,
        upcoming_assignments=upcoming_assignments,
        notifications=notifications,
        announcements=announcements,
        calendar_events=json.dumps(calendar_events),
        gpa=gpa,
        attendance_pct=attendance_pct,
        active='dashboard'
    )

# ==================== CALENDAR ROUTES ====================

@app.route('/calendar')
@login_required
def calendar_view():
    events = current_user.calendar_events
    
    if current_user.role == UserRole.STUDENT:
        enrollments = current_user.enrollments.all()
        assignments = db.session.query(Assignment).join(Course).filter(
            Course.id.in_([e.course_id for e in enrollments]),
            Assignment.due_date >= datetime.utcnow()
        ).all()
    else:
        courses = current_user.courses_teaching.all()
        assignments = db.session.query(Assignment).filter(
            Assignment.course_id.in_([c.id for c in courses]),
            Assignment.due_date >= datetime.utcnow()
        ).all()
        
    return render_template(
        'calendar.html',
        events=events,
        assignments=assignments,
        active='calendar'
    )

@app.route('/calendar/add', methods=['POST'])
@login_required
def add_calendar_task():
    title = request.form.get('title')
    date_str = request.form.get('date')
    description = request.form.get('description', '')
    
    if title and date_str:
        try:
            start_date = datetime.strptime(date_str, '%Y-%m-%d')
            event = CalendarEvent(
                user_id=current_user.id,
                title=title,
                description=description,
                start_date=start_date
            )
            db.session.add(event)
            db.session.commit()
        except ValueError:
            pass
            
    return redirect(url_for('calendar_view'))

# ==================== COURSE ROUTES ====================

@app.route('/courses')
@login_required
def courses_list():
    if current_user.role == UserRole.TEACHER:
        courses = Course.query.all()
    else:
        enrollments = current_user.enrollments.all()
        courses = [e.course for e in enrollments]
    
    return render_template('courses_list.html', courses=courses, active='courses')

@app.route('/courses/<course_slug>')
@login_required
def course_detail(course_slug):
    course = Course.query.filter_by(code=course_slug).first()
    if not course:
        return redirect(url_for('courses_list'))
    
    # Check if student is enrolled
    if current_user.role == UserRole.STUDENT:
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course.id
        ).first()
        if not enrollment:
            return redirect(url_for('courses_list'))
    
    # Get course modules
    modules = course.modules.order_by(Module.order).all()
    
    # Get assignments
    assignments = course.assignments.order_by(Assignment.due_date).all()
    
    # Get quizzes
    quizzes = course.quizzes.all()
    
    # Get announcements
    announcements = course.announcements.order_by(Announcement.created_at.desc()).all()
    
    # Get course enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course.id
    ).first()
    
    progress = course.get_completion_percentage() if enrollment else 0
    
    return render_template(
        'course_detail.html',
        course=course,
        modules=modules,
        assignments=assignments,
        quizzes=quizzes,
        announcements=announcements,
        progress=progress,
        enrollment=enrollment,
        active='courses'
    )

@app.route('/courses/<course_slug>/settings', methods=['GET', 'POST'])
@login_required
def course_settings(course_slug):
    course = Course.query.filter_by(code=course_slug).first_or_404()
    
    # Only teachers can access settings
    if current_user.role != UserRole.TEACHER:
        return redirect(url_for('course_detail', course_slug=course_slug))
    
    if request.method == 'POST':
        course.name = request.form.get('name')
        course.code = request.form.get('code')
        course.description = request.form.get('description')
        course.room_location = request.form.get('room_location')
        course.credits = request.form.get('credits')
        db.session.commit()
        return redirect(url_for('course_detail', course_slug=course.code))
        
    return render_template('course_settings.html', course=course, active='courses')

@app.route('/courses/<course_id>/modules/<module_id>')
@login_required
def module_detail(course_id, module_id):
    course = Course.query.get(course_id)
    if not course:
        return redirect(url_for('courses_list'))
    
    module = Module.query.get(module_id)
    if not module or module.course_id != course.id:
        return redirect(url_for('course_detail', course_slug=course.code))
    
    items = module.items.order_by(Module.order).all()
    
    return render_template(
        'module_detail.html',
        course=course,
        module=module,
        items=items,
        active='courses'
    )

# ==================== ASSIGNMENT ROUTES ====================

@app.route('/assignments/<assignment_id>')
@login_required
def assignment_detail(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return redirect(url_for('dashboard'))
    
    # Check enrollment
    if current_user.role == UserRole.STUDENT:
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=assignment.course_id
        ).first()
        if not enrollment:
            return redirect(url_for('courses_list'))
    
    submission = None
    if current_user.role == UserRole.STUDENT:
        submission = SubmittedAssignment.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
    
    # Get all submissions if teacher
    submissions = []
    if current_user.role == UserRole.TEACHER:
        submissions = assignment.submissions.all()
    
    days_until_due = assignment.get_days_until_due()
    is_overdue = assignment.is_overdue()
    
    return render_template(
        'assignment_detail.html',
        assignment=assignment,
        submission=submission,
        submissions=submissions,
        days_until_due=days_until_due,
        is_overdue=is_overdue,
        active='courses'
    )

@app.route('/assignments/<assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    if current_user.role != UserRole.STUDENT:
        return jsonify({'error': 'Unauthorized'}), 403
    
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404
    
    # Check if already submitted beyond allowed attempts
    previous_submissions = SubmittedAssignment.query.filter_by(
        assignment_id=assignment_id,
        student_id=current_user.id
    ).count()
    
    if previous_submissions >= assignment.allowed_attempts:
        return jsonify({'error': 'Maximum attempts exceeded'}), 403
    
    submission_text = request.form.get('submission_text', '')
    file = request.files.get('file')
    
    submission = SubmittedAssignment(
        assignment_id=assignment_id,
        student_id=current_user.id,
        submission_text=submission_text,
        status='submitted',
        is_late=assignment.is_overdue(),
        attempt_number=previous_submissions + 1
    )
    
    if file:
        # Save file (simplified - in production use proper file storage)
        filename = f"{current_user.id}_{assignment_id}_{file.filename}"
        submission.file_name = file.filename
        submission.file_path = f"uploads/{filename}"
    
    db.session.add(submission)
    db.session.commit()
    
    # Create notification for teacher
    notification = Notification(
        user_id=assignment.course.instructor_id,
        type='submission',
        title=f"New submission: {assignment.title}",
        description=f"{current_user.get_full_name()} submitted {assignment.title}",
        link=f"/assignments/{assignment_id}/submissions/{submission.id}"
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'submission_id': submission.id})

@app.route('/assignments/<assignment_id>/submissions/<submission_id>/grade', methods=['POST'])
@login_required
def grade_submission(assignment_id, submission_id):
    if current_user.role != UserRole.TEACHER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    submission = SubmittedAssignment.query.get(submission_id)
    if not submission or submission.assignment_id != int(assignment_id):
        return jsonify({'error': 'Submission not found'}), 404
    
    score = request.json.get('score')
    feedback = request.json.get('feedback')
    
    submission.score = score
    submission.feedback = feedback
    submission.status = 'graded'
    
    db.session.commit()
    
    # Create notification for student
    notification = Notification(
        user_id=submission.student_id,
        type='grade_posted',
        title=f"Grade posted: {submission.assignment.title}",
        description=f"Your assignment has been graded: {score}/{submission.assignment.points_possible}",
        link=f"/assignments/{assignment_id}"
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

# ==================== QUIZ ROUTES ====================

@app.route('/quizzes/<quiz_id>')
@login_required
def quiz_detail(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return redirect(url_for('dashboard'))
    
    # Check enrollment
    if current_user.role == UserRole.STUDENT:
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=quiz.course_id
        ).first()
        if not enrollment:
            return redirect(url_for('courses_list'))
    
    # Get previous attempts
    previous_attempts = QuizAttempt.query.filter_by(
        quiz_id=quiz_id,
        student_id=current_user.id
    ).all()
    
    can_attempt = len(previous_attempts) < quiz.attempts_allowed
    
    return render_template(
        'quiz_detail.html',
        quiz=quiz,
        previous_attempts=previous_attempts,
        can_attempt=can_attempt,
        active='courses'
    )

@app.route('/quizzes/<quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    if current_user.role != UserRole.STUDENT:
        return jsonify({'error': 'Unauthorized'}), 403
    
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    
    # Check attempts
    attempts = QuizAttempt.query.filter_by(
        quiz_id=quiz_id,
        student_id=current_user.id
    ).count()
    
    if attempts >= quiz.attempts_allowed:
        return jsonify({'error': 'Maximum attempts exceeded'}), 403
    
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=current_user.id,
        attempt_number=attempts + 1
    )
    
    db.session.add(attempt)
    db.session.commit()
    
    session['quiz_attempt_id'] = attempt.id
    session['quiz_start_time'] = datetime.utcnow().isoformat()
    
    return jsonify({'success': True, 'attempt_id': attempt.id})

@app.route('/quizzes/<quiz_id>/attempt/<attempt_id>')
@login_required
def take_quiz(quiz_id, attempt_id):
    quiz = Quiz.query.get(quiz_id)
    attempt = QuizAttempt.query.get(attempt_id)
    
    if not quiz or not attempt or attempt.student_id != current_user.id:
        return redirect(url_for('dashboard'))
    
    # Get questions
    questions = quiz.questions.order_by(QuizQuestion.order).all()
    
    return render_template(
        'take_quiz.html',
        quiz=quiz,
        attempt=attempt,
        questions=questions,
        active='courses'
    )

# ==================== DISCUSSION ROUTES ====================

@app.route('/courses/<course_id>/discussions')
@login_required
def discussions_list(course_id):
    course = Course.query.get(course_id)
    if not course:
        return redirect(url_for('courses_list'))
    
    discussions = course.discussions.order_by(Discussion.created_at.desc()).all()
    
    return render_template(
        'discussions_list.html',
        course=course,
        discussions=discussions,
        active='courses'
    )

@app.route('/discussions/<discussion_id>')
@login_required
def discussion_detail(discussion_id):
    discussion = Discussion.query.get(discussion_id)
    if not discussion:
        return redirect(url_for('courses_list'))
    
    posts = discussion.posts.filter_by(parent_post_id=None).order_by(
        DiscussionPost.created_at.desc()
    ).all()
    
    return render_template(
        'discussion_detail.html',
        discussion=discussion,
        posts=posts,
        active='courses'
    )

@app.route('/discussions/<discussion_id>/post', methods=['POST'])
@login_required
def post_to_discussion(discussion_id):
    discussion = Discussion.query.get(discussion_id)
    if not discussion:
        return jsonify({'error': 'Discussion not found'}), 404
    
    content = request.json.get('content')
    parent_post_id = request.json.get('parent_post_id')
    
    post = DiscussionPost(
        discussion_id=discussion_id,
        author_id=current_user.id,
        content=content,
        parent_post_id=parent_post_id
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'post': {
            'id': post.id,
            'author': current_user.get_full_name(),
            'content': content,
            'created_at': post.created_at.isoformat()
        }
    })

# ==================== MESSAGING ROUTES ====================

@app.route('/messages')
@login_required
def messages_list():
    # Get conversations
    sent_messages = current_user.messages_sent.all()
    received_messages = current_user.messages_received
    
    conversations = {}
    for msg in sent_messages + received_messages:
        other_user = msg.recipient if msg.sender_id == current_user.id else msg.sender
        if other_user.id not in conversations:
            conversations[other_user.id] = other_user
    
    return render_template(
        'messages_list.html',
        conversations=list(conversations.values()),
        active='messages'
    )

@app.route('/messages/user/<user_id>')
@login_required
def conversation(user_id):
    other_user = User.query.get(user_id)
    if not other_user:
        return redirect(url_for('messages_list'))
    
    messages = db.session.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.created_at).all()
    
    # Mark as read
    for msg in messages:
        if msg.recipient_id == current_user.id:
            msg.is_read = True
    db.session.commit()
    
    return render_template(
        'conversation.html',
        other_user=other_user,
        messages=messages,
        active='messages'
    )

@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    recipient_id = request.json.get('recipient_id')
    subject = request.json.get('subject', '')
    body = request.json.get('body')
    
    if not body:
        return jsonify({'error': 'Message body required'}), 400
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        subject=subject,
        body=body
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'success': True, 'message_id': message.id})

# ==================== NOTIFICATION ROUTES ====================

@app.route('/notifications')
@login_required
def notifications_view():
    notifications = current_user.notifications.order_by(
        Notification.created_at.desc()
    ).all()
    
    return render_template(
        'notifications.html',
        notifications=notifications,
        active='notifications'
    )

@app.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404

# ==================== TEACHER/ADMIN ROUTES ====================

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        return redirect(url_for('dashboard'))
    
    if current_user.role == UserRole.TEACHER:
        courses = current_user.courses_teaching.all()
    else:
        courses = Course.query.all()
    
    total_students = User.query.filter_by(role=UserRole.STUDENT).count()
    total_courses = len(courses)
    
    return render_template(
        'admin_dashboard.html',
        courses=courses,
        total_students=total_students,
        total_courses=total_courses,
        active='admin'
    )

@app.route('/admin/courses/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.role != UserRole.TEACHER:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        course = Course(
            code=request.form.get('code'),
            name=request.form.get('name'),
            description=request.form.get('description'),
            instructor_id=current_user.id,
            color=request.form.get('color', '#0374B5'),
            room_location=request.form.get('room_location'),
            credits=float(request.form.get('credits', 3.0)),
            term=request.form.get('term')
        )
        
        db.session.add(course)
        db.session.commit()
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_course.html', active='admin')



@app.route('/admin/gradebook/<course_id>')
@login_required
def gradebook(course_id):
    course = Course.query.get(course_id)
    if not course:
        return redirect(url_for('admin_dashboard'))
    
    enrollments = course.enrollments.all()
    assignments = course.assignments.all()
    
    return render_template(
        'gradebook.html',
        course=course,
        enrollments=enrollments,
        assignments=assignments,
        active='admin'
    )

@app.route('/admin/attendance/<course_id>')
@login_required
def attendance(course_id):
    course = Course.query.get(course_id)
    if not course:
        return redirect(url_for('admin_dashboard'))
    
    enrollments = course.enrollments.all()
    
    return render_template(
        'attendance.html',
        course=course,
        enrollments=enrollments,
        active='admin'
    )

# ==================== SETTINGS ====================

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', active='settings')

@app.route('/settings/profile', methods=['POST'])
@login_required
def update_profile():
    current_user.first_name = request.form.get('first_name', current_user.first_name)
    current_user.last_name = request.form.get('last_name', current_user.last_name)
    current_user.bio = request.form.get('bio', current_user.bio)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/settings/theme', methods=['POST'])
@login_required
def set_theme():
    theme = request.json.get('theme', 'light')
    current_user.theme_preference = theme
    db.session.commit()
    return jsonify({'success': True})

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

# ==================== CLI COMMANDS ====================

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

@app.cli.command()
def seed_db():
    """Seed the database with sample data."""
    # Create sample users
    teacher = User(
        username='prof_smith',
        email='smith@university.edu',
        first_name='John',
        last_name='Smith',
        role=UserRole.TEACHER
    )
    teacher.set_password('password123')
    
    student1 = User(
        username='alice_smith',
        email='alice@university.edu',
        first_name='Alice',
        last_name='Smith',
        role=UserRole.STUDENT
    )
    student1.set_password('password123')
    
    student2 = User(
        username='bob_jones',
        email='bob@university.edu',
        first_name='Bob',
        last_name='Jones',
        role=UserRole.STUDENT
    )
    student2.set_password('password123')
    
    db.session.add_all([teacher, student1, student2])
    db.session.commit()
    
    # Create sample courses
    course = Course(
        code='CS101',
        name='Introduction to Computer Science',
        description='Learn the basics of programming and computer science.',
        instructor_id=teacher.id,
        color='#0374B5',
        term='Spring 2024'
    )
    
    db.session.add(course)
    db.session.commit()
    
    # Enroll students
    enrollment1 = Enrollment(student_id=student1.id, course_id=course.id)
    enrollment2 = Enrollment(student_id=student2.id, course_id=course.id)
    
    db.session.add_all([enrollment1, enrollment2])
    db.session.commit()
    
    # Create modules
    module1 = Module(course_id=course.id, title='Module 1: Basics', order=1)
    module2 = Module(course_id=course.id, title='Module 2: Advanced', order=2)
    
    db.session.add_all([module1, module2])
    db.session.commit()
    
    # Create assignment
    assignment = Assignment(
        course_id=course.id,
        title='Programming Assignment 1',
        description='Write a simple Python program.',
        points_possible=100,
        due_date=datetime.utcnow() + timedelta(days=7),
        submission_type='file'
    )
    
    db.session.add(assignment)
    db.session.commit()
    
    print('Database seeded with sample data.')


# ==================== ASSIGNMENT MANAGEMENT ====================

@app.route('/courses/<course_slug>/assignments/add', methods=['POST'])
@login_required
def add_assignment(course_slug):
    course = Course.query.filter_by(code=course_slug).first_or_404()
    title = request.form.get('title')
    description = request.form.get('description', '')
    points = float(request.form.get('points', 100))
    due_date_str = request.form.get('due_date')
    
    if title and due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        assignment = Assignment(
            course_id=course.id,
            title=title,
            description=description,
            points_possible=points,
            due_date=due_date
        )
        db.session.add(assignment)
        db.session.commit()
    return redirect(url_for('course_detail', course_slug=course.code))

@app.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    course_slug = assignment.course.code
    db.session.delete(assignment)
    db.session.commit()
    return redirect(url_for('course_detail', course_slug=course_slug))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Auto-seed if the database is empty
        if User.query.count() == 0:
            from seed_data import seed_all
            seed_all()
    app.run(debug=True)