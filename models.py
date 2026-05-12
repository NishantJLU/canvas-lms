from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

class UserRole(enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    avatar = db.Column(db.String(255), default="https://via.placeholder.com/48")
    bio = db.Column(db.Text, default="")
    role = db.Column(db.Enum(UserRole), default=UserRole.STUDENT)
    theme_preference = db.Column(db.String(10), default="light")  # light, dark, auto
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    courses_teaching = db.relationship('Course', backref='instructor', lazy='dynamic')
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')
    assignments_submitted = db.relationship('SubmittedAssignment', backref='student', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', backref='student', lazy='dynamic')
    messages_sent = db.relationship('Message', backref='sender', lazy='dynamic', foreign_keys='Message.sender_id')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_gpa(self):
        enrollments = self.enrollments.all()
        if not enrollments:
            return 0.0
        total_grade = sum(e.get_grade_point() for e in enrollments)
        return round(total_grade / len(enrollments), 2)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    color = db.Column(db.String(7), default="#0374B5")
    room_location = db.Column(db.String(100))
    credits = db.Column(db.Float, default=3.0)
    capacity = db.Column(db.Integer, default=50)
    term = db.Column(db.String(20))  # e.g., "Spring 2024"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    modules = db.relationship('Module', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    discussions = db.relationship('Discussion', backref='course', lazy='dynamic', cascade='all, delete-orphan')

    def get_enrolled_count(self):
        return self.enrollments.filter_by().count()

    def get_completion_percentage(self):
        modules = self.modules.all()
        if not modules:
            return 0
        completed = sum(1 for m in modules if m.status == 'completed')
        return int((completed / len(modules)) * 100)

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    final_grade = db.Column(db.String(5))
    attendance_count = db.Column(db.Integer, default=0)
    total_classes = db.Column(db.Integer, default=0)
    current_score = db.Column(db.Float, default=0.0)

    def get_attendance_percentage(self):
        if self.total_classes == 0:
            return 0
        return int((self.attendance_count / self.total_classes) * 100)

    def get_grade_point(self):
        # Convert letter grade to GPA point
        grade_map = {'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D': 1.0, 'F': 0.0}
        return grade_map.get(self.final_grade, 0.0)

class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="upcoming")  # upcoming, in_progress, completed
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    items = db.relationship('ModuleItem', backref='module', lazy='dynamic', cascade='all, delete-orphan')

class ModuleItem(db.Model):
    __tablename__ = 'module_items'
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    item_type = db.Column(db.String(50))  # page, assignment, quiz, video, discussion, file
    content = db.Column(db.Text)
    file_url = db.Column(db.String(255))
    video_url = db.Column(db.String(255))
    external_url = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    points_possible = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    points_possible = db.Column(db.Float, default=100.0)
    due_date = db.Column(db.DateTime, nullable=False)
    submission_type = db.Column(db.String(50), default="file")  # file, text, url, choice
    allowed_attempts = db.Column(db.Integer, default=1)
    rubric = db.Column(db.JSON)  # Stores rubric criteria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submissions = db.relationship('SubmittedAssignment', backref='assignment', lazy='dynamic', cascade='all, delete-orphan')

    def is_overdue(self):
        return datetime.utcnow() > self.due_date

    def get_days_until_due(self):
        delta = self.due_date - datetime.utcnow()
        return max(0, delta.days)

class SubmittedAssignment(db.Model):
    __tablename__ = 'submitted_assignments'
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_text = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float)
    feedback = db.Column(db.Text)
    status = db.Column(db.String(20), default="submitted")  # submitted, graded, draft
    is_late = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, default=1)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    points_possible = db.Column(db.Float, default=100.0)
    due_date = db.Column(db.DateTime)
    time_limit_minutes = db.Column(db.Integer)
    show_answers = db.Column(db.Boolean, default=True)
    shuffle_questions = db.Column(db.Boolean, default=False)
    attempts_allowed = db.Column(db.Integer, default=1)
    passing_score = db.Column(db.Float, default=70.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_type = db.Column(db.String(50))  # multiple_choice, short_answer, essay, true_false
    question_text = db.Column(db.Text, nullable=False)
    points_possible = db.Column(db.Float, default=1.0)
    order = db.Column(db.Integer, default=0)
    options = db.Column(db.JSON)  # For multiple choice
    correct_answer = db.Column(db.String(500))  # For short answer/true-false
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    responses = db.relationship('QuizResponse', backref='question', lazy='dynamic', cascade='all, delete-orphan')

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Float)
    status = db.Column(db.String(20), default="in_progress")  # in_progress, submitted, graded
    attempt_number = db.Column(db.Integer, default=1)

    # Relationships
    responses = db.relationship('QuizResponse', backref='attempt', lazy='dynamic', cascade='all, delete-orphan')

    def get_duration_minutes(self):
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0

class QuizResponse(db.Model):
    __tablename__ = 'quiz_responses'
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    answer_text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)

    creator = db.relationship('User', backref='announcements_created')

class Discussion(db.Model):
    __tablename__ = 'discussions'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)

    creator = db.relationship('User', backref='discussions_created')
    posts = db.relationship('DiscussionPost', backref='discussion', lazy='dynamic', cascade='all, delete-orphan')

class DiscussionPost(db.Model):
    __tablename__ = 'discussion_posts'
    id = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussions.id'), nullable=False)
    parent_post_id = db.Column(db.Integer, db.ForeignKey('discussion_posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship('User', backref='discussion_posts')
    replies = db.relationship('DiscussionPost', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipient = db.relationship('User', backref='messages_received', foreign_keys=[recipient_id])

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50))  # assignment_due, grade_posted, announcement, message, etc
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudyGroup(db.Model):
    __tablename__ = 'study_groups'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    max_members = db.Column(db.Integer, default=5)

    creator = db.relationship('User', backref='study_groups_created')
    members = db.relationship('User', secondary='study_group_members', backref='study_groups')

# Association table for study group members
study_group_members = db.Table(
    'study_group_members',
    db.Column('study_group_id', db.Integer, db.ForeignKey('study_groups.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    class_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="present")  # present, absent, late, excused
    notes = db.Column(db.Text)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', backref='attendance_records')
    course = db.relationship('Course', backref='attendance_records')

class CalendarEvent(db.Model):
    __tablename__ = 'calendar_events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='calendar_events')
