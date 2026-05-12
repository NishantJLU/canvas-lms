# 🎓 EduFlow - Modern Learning Management System (LMS)

EduFlow is a premium, teacher-centric Learning Management System designed to provide a modern and intuitive experience for both educators and students. Built with Flask and a custom premium design system, it offers robust course management, interactive calendars, and streamlined communication.

![Dashboard Preview](https://via.placeholder.com/1200x600/0374B5/FFFFFF?text=EduFlow+Modern+Dashboard)

## ✨ Features

### 👨‍🏫 For Teachers
*   **Comprehensive Dashboard:** Track total courses, student enrollments, and upcoming tasks at a glance.
*   **Course Management:** Create and edit courses with custom themes, credits, and room locations.
*   **Action-Oriented Calendar:** Add and manage daily tasks and assignments with an intuitive modal interface.
*   **Student Tracking:** Manage gradebooks and attendance with a single click.
*   **User Switching:** Seamlessly toggle between different professor profiles to manage multiple course loads.

### 🎓 For Students
*   **Modern Course View:** Access modules, assignments, quizzes, and announcements in a clean, tabbed interface.
*   **Interactive Learning:** Track progress through course modules and stay updated with real-time notifications.
*   **Personalized Calendar:** View all upcoming deadlines and course events in one unified view.

## 🛠️ Technology Stack
*   **Backend:** Python 3.13 + Flask
*   **Database:** SQLAlchemy (SQLite for local development)
*   **Frontend:** Jinja2 Templates + Vanilla CSS (Premium Custom Design System)
*   **Authentication:** Flask-Login
*   **API:** Flask-CORS

## 🚀 Getting Started

### Prerequisites
*   Python 3.10 or higher
*   Pip (Python package manager)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NishantJLU/canvas-lms.git
   cd canvas-lms
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup the database:**
   The application will automatically seed itself on the first run, but you can also manually seed it:
   ```bash
   python seed_data.py
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the site:**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 📂 Project Structure
*   `app.py`: Main application logic and routing.
*   `models.py`: Database schemas and relationships.
*   `seed_data.py`: Initial data population script.
*   `templates/`: Jinja2 HTML templates.
*   `static/`: CSS and assets.

## 🤝 Contributing
Contributions are welcome! Feel free to open issues or submit pull requests to help improve EduFlow.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
