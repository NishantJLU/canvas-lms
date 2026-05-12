from app import app
from models import db, User, Course, Enrollment

def enroll():
    with app.app_context():
        student = User.query.filter_by(username='alice_smith').first()
        if not student:
            student = User.query.first()
            
        courses = Course.query.all()
        for course in courses:
            existing = Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first()
            if not existing:
                enrollment = Enrollment(student_id=student.id, course_id=course.id)
                db.session.add(enrollment)
        db.session.commit()
        print(f"Enrolled {student.username} in all courses.")

if __name__ == "__main__":
    enroll()
