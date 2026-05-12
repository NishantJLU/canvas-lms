from app import app
from models import db, Course, User, UserRole, Enrollment, Module, Assignment, Announcement
from datetime import datetime, timedelta

def seed_all():
    with app.app_context():
        db.create_all()
        
        # ==================== TEACHERS ====================
        teachers = {}
        teacher_data = [
            {
                'username': 'prof_jadhav',
                'email': 'jadhav@university.edu',
                'first_name': 'Ravi Kumar Vasantarao',
                'last_name': 'Jadhav',
            },
            {
                'username': 'prof_singh',
                'email': 'shweta.singh@university.edu',
                'first_name': 'Shweta',
                'last_name': 'Singh',
            },
            {
                'username': 'prof_kundu',
                'email': 'sukanta.kundu@university.edu',
                'first_name': 'Sukanta',
                'last_name': 'Kundu',
            },
            {
                'username': 'prof_pachori',
                'email': 'nishan.pachori@university.edu',
                'first_name': 'Nishan',
                'last_name': 'Pachori',
            },
            {
                'username': 'prof_venkatesh',
                'email': 'bharti.venkatesh@university.edu',
                'first_name': 'Bharti',
                'last_name': 'Venkatesh',
            },
        ]
        
        for td in teacher_data:
            user = User.query.filter_by(username=td['username']).first()
            if not user:
                user = User(
                    username=td['username'],
                    email=td['email'],
                    first_name=td['first_name'],
                    last_name=td['last_name'],
                    role=UserRole.TEACHER
                )
                user.set_password('password123')
                db.session.add(user)
                db.session.flush()
            teachers[td['username']] = user
        
        db.session.commit()
        
        # ==================== STUDENTS ====================
        student1 = User.query.filter_by(username='alice_smith').first()
        if not student1:
            student1 = User(
                username='alice_smith',
                email='alice@university.edu',
                first_name='Alice',
                last_name='Smith',
                role=UserRole.STUDENT
            )
            student1.set_password('password123')
            db.session.add(student1)
        
        student2 = User.query.filter_by(username='bob_jones').first()
        if not student2:
            student2 = User(
                username='bob_jones',
                email='bob@university.edu',
                first_name='Bob',
                last_name='Jones',
                role=UserRole.STUDENT
            )
            student2.set_password('password123')
            db.session.add(student2)
        
        db.session.commit()
        
        # ==================== COURSES ====================
        courses_data = [
            {
                'code': 'ROB301',
                'name': 'Robotics',
                'description': 'Fundamentals of robotics, kinematics, dynamics, and automation systems.',
                'color': '#ef4444',
                'instructor': 'prof_jadhav',
                'room_location': 'Lab 204',
                'credits': 4.0,
                'term': 'Spring 2025',
            },
            {
                'code': 'MATH201',
                'name': 'Engineering Mathematics',
                'description': 'Advanced mathematical methods for engineering including linear algebra, calculus, and differential equations.',
                'color': '#10b981',
                'instructor': 'prof_singh',
                'room_location': 'Room 102',
                'credits': 3.0,
                'term': 'Spring 2025',
            },
            {
                'code': 'CS101',
                'name': 'Programming',
                'description': 'Introduction to programming concepts, data structures, and algorithms.',
                'color': '#4f46e5',
                'instructor': 'prof_pachori',
                'room_location': 'Room 301',
                'credits': 3.0,
                'term': 'Spring 2025',
            },
            {
                'code': 'PSYCH101',
                'name': 'Psychology',
                'description': 'Introduction to human psychology and cognitive science.',
                'color': '#f59e0b',
                'instructor': 'prof_venkatesh',
                'room_location': 'Hall A',
                'credits': 2.0,
                'term': 'Spring 2025',
            },
            {
                'code': 'DES101',
                'name': 'Design Thinking',
                'description': 'Creative problem solving and human-centered design.',
                'color': '#8b5cf6',
                'instructor': 'prof_kundu',
                'room_location': 'Studio 3',
                'credits': 2.0,
                'term': 'Spring 2025',
            },
        ]
        
        course_objs = {}
        for cd in courses_data:
            course = Course.query.filter_by(code=cd['code']).first()
            if not course:
                course = Course(
                    code=cd['code'],
                    name=cd['name'],
                    description=cd['description'],
                    color=cd['color'],
                    instructor_id=teachers[cd['instructor']].id,
                    room_location=cd['room_location'],
                    credits=cd['credits'],
                    term=cd['term'],
                )
                db.session.add(course)
                db.session.flush()
            else:
                # Update instructor if course already exists
                course.instructor_id = teachers[cd['instructor']].id
                course.room_location = cd['room_location']
                course.credits = cd['credits']
                course.term = cd['term']
                course.description = cd['description']
            course_objs[cd['code']] = course
        
        db.session.commit()
        
        # ==================== ENROLLMENTS ====================
        for code, course in course_objs.items():
            for student in [student1, student2]:
                existing = Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first()
                if not existing:
                    enrollment = Enrollment(
                        student_id=student.id,
                        course_id=course.id,
                        total_classes=30,
                        attendance_count=25,
                        final_grade='A-'
                    )
                    db.session.add(enrollment)
        
        db.session.commit()
        
        # ==================== MODULES ====================
        modules_data = {
            'ROB301': [
                'Module 1: Introduction to Robotics',
                'Module 2: Kinematics & Motion',
                'Module 3: Sensors & Actuators',
                'Module 4: Robot Programming',
            ],
            'MATH201': [
                'Module 1: Linear Algebra',
                'Module 2: Multivariable Calculus',
                'Module 3: Differential Equations',
                'Module 4: Probability & Statistics',
            ],
            'CS101': [
                'Module 1: Programming Basics',
                'Module 2: Data Structures',
            ],
        }
        
        for code, module_titles in modules_data.items():
            course = course_objs[code]
            for i, title in enumerate(module_titles, start=1):
                existing = Module.query.filter_by(course_id=course.id, title=title).first()
                if not existing:
                    module = Module(course_id=course.id, title=title, order=i)
                    db.session.add(module)
        
        db.session.commit()
        
        # ==================== ASSIGNMENTS ====================
        assignments_data = [
            {
                'course': 'ROB301',
                'title': 'Robot Arm Kinematics Report',
                'description': 'Analyze forward and inverse kinematics of a 3-DOF robot arm.',
                'points': 100,
                'due_days': 7,
            },
            {
                'course': 'ROB301',
                'title': 'Sensor Integration Lab',
                'description': 'Integrate ultrasonic and IR sensors with Arduino.',
                'points': 80,
                'due_days': 14,
            },
            {
                'course': 'MATH201',
                'title': 'Linear Algebra Problem Set',
                'description': 'Solve problems on eigenvalues, eigenvectors, and matrix decomposition.',
                'points': 50,
                'due_days': 5,
            },
            {
                'course': 'MATH201',
                'title': 'Differential Equations Midterm',
                'description': 'Solve first and second order ODEs.',
                'points': 100,
                'due_days': 21,
            },
            {
                'course': 'CS101',
                'title': 'Programming Assignment 1',
                'description': 'Write a simple Python program.',
                'points': 100,
                'due_days': 7,
            },
        ]
        
        for ad in assignments_data:
            course = course_objs[ad['course']]
            existing = Assignment.query.filter_by(course_id=course.id, title=ad['title']).first()
            if not existing:
                assignment = Assignment(
                    course_id=course.id,
                    title=ad['title'],
                    description=ad['description'],
                    points_possible=ad['points'],
                    due_date=datetime.utcnow() + timedelta(days=ad['due_days']),
                )
                db.session.add(assignment)
        
        db.session.commit()
        
        # ==================== ANNOUNCEMENTS ====================
        announcements_data = [
            {
                'course': 'ROB301',
                'title': 'Lab Schedule Updated',
                'content': 'The robotics lab will now be available on weekends as well. Please book your slots in advance.',
                'created_by': 'prof_jadhav',
            },
            {
                'course': 'MATH201',
                'title': 'Extra Revision Class',
                'content': 'There will be an extra revision class this Saturday for Differential Equations.',
                'created_by': 'prof_singh',
            },
        ]
        
        for ann in announcements_data:
            course = course_objs[ann['course']]
            existing = Announcement.query.filter_by(course_id=course.id, title=ann['title']).first()
            if not existing:
                announcement = Announcement(
                    course_id=course.id,
                    title=ann['title'],
                    content=ann['content'],
                    created_by=teachers[ann['created_by']].id,
                )
                db.session.add(announcement)
        
        db.session.commit()
        
        print("Database seeded successfully!")
        print(f"   Teachers: {len(teachers)}")
        print(f"   Students: 2")
        print(f"   Courses: {len(course_objs)}")

if __name__ == "__main__":
    seed_all()
