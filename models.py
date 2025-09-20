from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Initialize the SQLAlchemy extension.
db = SQLAlchemy()


class Course(db.Model):
    """
    Represents a complete course that can contain multiple subjects/books.
    This is the top-level organizational unit.
    """
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Course metadata
    academic_level = db.Column(db.String(50), default='masters')  # undergraduate, masters, phd, professional
    institution = db.Column(db.String(100), nullable=True)
    instructor = db.Column(db.String(100), nullable=True)
    semester = db.Column(db.String(50), nullable=True)

    # Course analytics
    total_subjects = db.Column(db.Integer, default=0)
    total_chapters = db.Column(db.Integer, default=0)
    estimated_study_hours = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subjects = db.relationship('Subject', backref='course', lazy=True, cascade="all, delete-orphan")
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Course {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'academic_level': self.academic_level,
            'total_subjects': self.total_subjects,
            'total_chapters': self.total_chapters,
            'estimated_study_hours': self.estimated_study_hours,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Subject(db.Model):
    """
    Represents a single subject/book within a course.
    Each PDF upload creates one subject with adaptive content based on domain analysis.
    """
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    # Subject content
    preface = db.Column(db.Text, nullable=True)  # JSON: welcome, objectives, relevance
    overall_summary = db.Column(db.Text, nullable=True)  # JSON: themes, applications, difficulty

    # Subject metadata from AI analysis
    subject_domain = db.Column(db.String(50), default='general')  # economics, computer_science, etc.
    learning_style = db.Column(db.String(20), default='mixed')  # theoretical, practical, mixed
    complexity_level = db.Column(db.String(20), default='intermediate')
    subject_analysis = db.Column(db.Text, nullable=True)  # JSON: full AI analysis results

    # Book/PDF metadata
    original_filename = db.Column(db.String(255), nullable=True)
    file_size_mb = db.Column(db.Float, nullable=True)
    processing_time_seconds = db.Column(db.Integer, nullable=True)

    # Subject analytics
    total_chapters = db.Column(db.Integer, default=0)
    estimated_read_time = db.Column(db.Integer, default=0)  # in minutes
    interactive_elements_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    # Relationships
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")
    user_progress = db.relationship('UserProgress', backref='subject', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Subject {self.name} ({self.subject_domain})>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject_domain': self.subject_domain,
            'learning_style': self.learning_style,
            'complexity_level': self.complexity_level,
            'total_chapters': self.total_chapters,
            'estimated_read_time': self.estimated_read_time,
            'course_id': self.course_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_domain_display_name(self):
        """Get user-friendly display name for subject domain."""
        domain_names = {
            'computer_science': 'Computer Science',
            'economics': 'Economics',
            'mathematics': 'Mathematics',
            'psychology': 'Psychology',
            'engineering': 'Engineering',
            'medicine': 'Medicine',
            'business': 'Business',
            'history': 'History',
            'literature': 'Literature',
            'physics': 'Physics',
            'chemistry': 'Chemistry',
            'biology': 'Biology',
            'law': 'Law'
        }
        return domain_names.get(self.subject_domain, self.subject_domain.replace('_', ' ').title())


class Chapter(db.Model):
    """
    Enhanced chapter model with adaptive content based on subject domain.
    """
    __tablename__ = 'chapter'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=True)

    # Core content fields (JSON)
    intro_summary = db.Column(db.Text, nullable=True)  # JSON: concepts, objectives, context
    content_blocks = db.Column(db.Text, nullable=True)  # JSON: adaptive content blocks
    chapter_metadata = db.Column(db.Text, nullable=True)  # JSON: difficulty, study time, skills

    # Chapter characteristics
    difficulty_level = db.Column(db.String(20), default='intermediate')
    estimated_study_time = db.Column(db.Integer, default=30)  # in minutes

    # Content analytics
    total_content_blocks = db.Column(db.Integer, default=0)
    concept_count = db.Column(db.Integer, default=0)
    visualization_count = db.Column(db.Integer, default=0)
    exercise_count = db.Column(db.Integer, default=0)
    case_study_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

    # Relationships
    user_progress = db.relationship('UserProgress', backref='chapter', lazy=True)
    bookmarks = db.relationship('Bookmark', backref='chapter', lazy=True, cascade="all, delete-orphan")
    quiz_results = db.relationship('QuizResult', backref='chapter', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Chapter {self.title} ({self.subject.subject_domain})>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'chapter_number': self.chapter_number,
            'difficulty_level': self.difficulty_level,
            'estimated_study_time': self.estimated_study_time,
            'total_content_blocks': self.total_content_blocks,
            'concept_count': self.concept_count,
            'visualization_count': self.visualization_count,
            'exercise_count': self.exercise_count,
            'case_study_count': self.case_study_count,
            'subject_id': self.subject_id,
            'subject_domain': self.subject.subject_domain if self.subject else 'unknown'
        }


class CourseEnrollment(db.Model):
    """
    Track user enrollment and progress in courses.
    """
    __tablename__ = 'course_enrollment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)

    # Enrollment details
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    target_completion_date = db.Column(db.DateTime, nullable=True)
    study_goal_hours_per_week = db.Column(db.Integer, default=10)

    # Progress tracking
    overall_progress_percentage = db.Column(db.Float, default=0.0)
    subjects_completed = db.Column(db.Integer, default=0)
    chapters_completed = db.Column(db.Integer, default=0)
    total_study_time_minutes = db.Column(db.Integer, default=0)

    # Learning preferences
    preferred_difficulty = db.Column(db.String(20), default='intermediate')
    learning_style_preference = db.Column(db.String(20), default='mixed')

    # Timestamps
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Foreign key
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),)

    def __repr__(self):
        return f'<CourseEnrollment {self.user_id} - Course {self.course_id}>'


class UserProgress(db.Model):
    """
    Enhanced progress tracking for adaptive learning across subjects and chapters.
    """
    __tablename__ = 'user_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)

    # Progress location
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=True)

    # Progress status
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed, mastered
    completion_percentage = db.Column(db.Float, default=0.0)
    mastery_level = db.Column(db.String(20), default='novice')  # novice, developing, proficient, expert

    # Time and engagement tracking
    time_spent_minutes = db.Column(db.Integer, default=0)
    sessions_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Interaction tracking
    questions_asked = db.Column(db.Integer, default=0)
    concepts_bookmarked = db.Column(db.Integer, default=0)
    quizzes_taken = db.Column(db.Integer, default=0)
    avg_quiz_score = db.Column(db.Float, default=0.0)

    # Adaptive learning data
    difficulty_preference = db.Column(db.String(20), default='intermediate')
    learning_velocity = db.Column(db.Float, default=1.0)  # multiplier for study time estimates
    struggle_areas = db.Column(db.Text, nullable=True)  # JSON: areas where user needs help

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'subject_id', 'chapter_id', name='unique_progress'),)

    def __repr__(self):
        return f'<UserProgress {self.user_id} - Subject {self.subject_id} - Chapter {self.chapter_id}>'


class Bookmark(db.Model):
    """
    Enhanced bookmark system for adaptive learning content.
    """
    __tablename__ = 'bookmark'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)

    # Bookmark location
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    content_block_index = db.Column(db.Integer, nullable=True)
    content_block_type = db.Column(db.String(50), nullable=True)  # concept_explanation, case_study, etc.

    # Bookmark details
    title = db.Column(db.String(200), nullable=False)
    note = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON: user-defined tags

    # Learning context
    difficulty_when_bookmarked = db.Column(db.String(20), nullable=True)
    reason_for_bookmark = db.Column(db.String(50), default='important')  # important, difficult, review_later, example

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_reviewed = db.Column(db.DateTime, nullable=True)

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'chapter_id', 'content_block_index', name='unique_bookmark'),)

    def __repr__(self):
        return f'<Bookmark {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'note': self.note,
            'content_block_type': self.content_block_type,
            'reason_for_bookmark': self.reason_for_bookmark,
            'chapter_id': self.chapter_id,
            'content_block_index': self.content_block_index,
            'created_at': self.created_at.isoformat()
        }


class QuizResult(db.Model):
    """
    Enhanced quiz results with adaptive difficulty and domain-specific analytics.
    """
    __tablename__ = 'quiz_result'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)

    # Quiz context
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    quiz_title = db.Column(db.String(200), nullable=False)
    quiz_type = db.Column(db.String(50), default='practice')  # practice, assessment, review
    subject_domain = db.Column(db.String(50), nullable=True)

    # Results
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    difficulty_level = db.Column(db.String(20), default='intermediate')

    # Performance analytics
    time_taken_seconds = db.Column(db.Integer, nullable=True)
    questions_by_type = db.Column(db.Text, nullable=True)  # JSON: performance by question type
    concept_mastery = db.Column(db.Text, nullable=True)  # JSON: which concepts were mastered
    areas_for_improvement = db.Column(db.Text, nullable=True)  # JSON: concepts needing work

    # Timestamps
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Quiz data for review
    questions_and_answers = db.Column(db.Text, nullable=True)  # JSON: full quiz data

    def __repr__(self):
        return f'<QuizResult {self.user_id} - {self.percentage}% ({self.subject_domain})>'

    def to_dict(self):
        return {
            'id': self.id,
            'quiz_title': self.quiz_title,
            'quiz_type': self.quiz_type,
            'subject_domain': self.subject_domain,
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': self.percentage,
            'difficulty_level': self.difficulty_level,
            'time_taken_seconds': self.time_taken_seconds,
            'completed_at': self.completed_at.isoformat(),
            'chapter_id': self.chapter_id
        }


class StudySession(db.Model):
    """
    Track individual study sessions for analytics and adaptive recommendations.
    """
    __tablename__ = 'study_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)

    # Session details
    session_start = db.Column(db.DateTime, default=datetime.utcnow)
    session_end = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)

    # Study context
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=True)

    # Session activities
    activities = db.Column(db.Text, nullable=True)  # JSON: list of activities in session
    concepts_studied = db.Column(db.Text, nullable=True)  # JSON: concepts covered
    difficulty_adjustments = db.Column(db.Integer, default=0)  # how many times user changed difficulty

    # Session outcomes
    completion_progress = db.Column(db.Float, default=0.0)  # progress made in this session
    questions_asked = db.Column(db.Integer, default=0)
    bookmarks_created = db.Column(db.Integer, default=0)
    quizzes_completed = db.Column(db.Integer, default=0)

    # Session quality metrics
    engagement_score = db.Column(db.Float, default=0.0)  # calculated engagement metric
    focus_score = db.Column(db.Float, default=0.0)  # calculated focus metric
    learning_effectiveness = db.Column(db.Float, default=0.0)  # calculated learning metric

    # Relationships
    course = db.relationship('Course', backref='study_sessions', lazy=True)
    subject = db.relationship('Subject', backref='study_sessions', lazy=True)
    chapter = db.relationship('Chapter', backref='study_sessions', lazy=True)

    def __repr__(self):
        return f'<StudySession {self.user_id} - {self.duration_minutes}min>'


# =========================================================================
# --- Utility Functions ---
# =========================================================================

def update_course_stats(course_id: int):
    """Update course statistics based on contained subjects."""
    course = Course.query.get(course_id)
    if course:
        subjects = Subject.query.filter_by(course_id=course_id).all()
        course.total_subjects = len(subjects)
        course.total_chapters = sum(subject.total_chapters for subject in subjects)
        course.estimated_study_hours = sum(subject.estimated_read_time for subject in subjects) // 60
        db.session.commit()


def update_subject_stats(subject_id: int):
    """Update subject statistics based on contained chapters."""
    subject = Subject.query.get(subject_id)
    if subject:
        chapters = Chapter.query.filter_by(subject_id=subject_id).all()
        subject.total_chapters = len(chapters)
        subject.estimated_read_time = sum(chapter.estimated_study_time or 30 for chapter in chapters)
        subject.interactive_elements_count = sum(
            (chapter.visualization_count or 0) + (chapter.exercise_count or 0)
            for chapter in chapters
        )
        db.session.commit()

        # Update parent course stats
        if subject.course_id:
            update_course_stats(subject.course_id)


def update_chapter_stats(chapter_id: int):
    """Update chapter statistics based on content blocks."""
    chapter = Chapter.query.get(chapter_id)
    if chapter and chapter.content_blocks:
        try:
            content_blocks = json.loads(chapter.content_blocks)
            chapter.total_content_blocks = len(content_blocks)

            # Count different types of content blocks
            chapter.concept_count = len([b for b in content_blocks if b.get('type') == 'concept_explanation'])
            chapter.visualization_count = len(
                [b for b in content_blocks if b.get('type') == 'interactive_visualization'])
            chapter.exercise_count = len([b for b in content_blocks if b.get('type') == 'problem_solving'])
            chapter.case_study_count = len([b for b in content_blocks if b.get('type') == 'case_study'])

            db.session.commit()

            # Update parent subject stats
            if chapter.subject_id:
                update_subject_stats(chapter.subject_id)

        except json.JSONDecodeError:
            pass


def get_user_course_progress(user_id: str, course_id: int) -> dict:
    """Get comprehensive progress summary for a user in a specific course."""
    enrollment = CourseEnrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if not enrollment:
        return {"error": "User not enrolled in course"}

    progress_entries = UserProgress.query.join(Subject).filter(
        UserProgress.user_id == user_id,
        Subject.course_id == course_id
    ).all()

    total_subjects = Subject.query.filter_by(course_id=course_id).count()
    completed_subjects = len(set(
        entry.subject_id for entry in progress_entries
        if entry.status == 'completed' and entry.chapter_id is None
    ))

    total_chapters = db.session.query(Chapter).join(Subject).filter(
        Subject.course_id == course_id
    ).count()
    completed_chapters = len([
        entry for entry in progress_entries
        if entry.status == 'completed' and entry.chapter_id is not None
    ])

    total_time = sum(entry.time_spent_minutes for entry in progress_entries)
    quiz_results = QuizResult.query.join(Chapter).join(Subject).filter(
        QuizResult.user_id == user_id,
        Subject.course_id == course_id
    ).all()

    avg_quiz_score = (
        sum(qr.percentage for qr in quiz_results) / len(quiz_results)
        if quiz_results else 0
    )

    return {
        'course_id': course_id,
        'enrollment_date': enrollment.enrollment_date.isoformat(),
        'overall_progress': enrollment.overall_progress_percentage,
        'subjects_completed': f"{completed_subjects}/{total_subjects}",
        'chapters_completed': f"{completed_chapters}/{total_chapters}",
        'total_study_time_hours': round(total_time / 60, 1),
        'average_quiz_score': round(avg_quiz_score, 1),
        'quizzes_taken': len(quiz_results),
        'last_activity': enrollment.last_activity.isoformat() if enrollment.last_activity else None
    }


def get_adaptive_recommendations(user_id: str, course_id: int) -> dict:
    """Generate adaptive learning recommendations based on user progress."""
    progress_data = get_user_course_progress(user_id, course_id)

    # Analyze user's learning patterns
    progress_entries = UserProgress.query.join(Subject).filter(
        UserProgress.user_id == user_id,
        Subject.course_id == course_id
    ).all()

    # Calculate learning velocity
    total_time = sum(entry.time_spent_minutes for entry in progress_entries)
    completed_chapters = len([e for e in progress_entries if e.status == 'completed'])
    avg_time_per_chapter = total_time / completed_chapters if completed_chapters > 0 else 30

    # Identify struggle areas
    low_quiz_scores = QuizResult.query.join(Chapter).join(Subject).filter(
        QuizResult.user_id == user_id,
        Subject.course_id == course_id,
        QuizResult.percentage < 70
    ).all()

    struggle_domains = list(set(qr.subject_domain for qr in low_quiz_scores if qr.subject_domain))

    # Generate recommendations
    recommendations = {
        'study_schedule': {
            'recommended_minutes_per_day': max(30, min(120, int(avg_time_per_chapter * 0.7))),
            'optimal_study_times': ['morning', 'evening'],  # Could be personalized
            'break_intervals': 25  # Pomodoro-style
        },
        'content_focus': {
            'review_subjects': struggle_domains[:3],
            'next_chapters': _get_next_recommended_chapters(user_id, course_id),
            'difficulty_adjustment': _recommend_difficulty_level(progress_entries)
        },
        'learning_strategies': _get_domain_specific_strategies(struggle_domains),
        'progress_goals': {
            'weekly_chapters': max(1, min(5, int(7 * 60 / avg_time_per_chapter))),
            'target_quiz_score': 85,
            'mastery_focus': struggle_domains[:2]
        }
    }

    return recommendations


def _get_next_recommended_chapters(user_id: str, course_id: int) -> list:
    """Get recommended next chapters for study."""
    completed_chapter_ids = [
        entry.chapter_id for entry in UserProgress.query.join(Subject).filter(
            UserProgress.user_id == user_id,
            Subject.course_id == course_id,
            UserProgress.status == 'completed',
            UserProgress.chapter_id.isnot(None)
        ).all()
    ]

    next_chapters = Chapter.query.join(Subject).filter(
        Subject.course_id == course_id,
        ~Chapter.id.in_(completed_chapter_ids)
    ).order_by(Subject.created_at, Chapter.chapter_number).limit(3).all()

    return [{'id': ch.id, 'title': ch.title, 'subject': ch.subject.name} for ch in next_chapters]


def _recommend_difficulty_level(progress_entries: list) -> str:
    """Recommend difficulty level based on user performance."""
    if not progress_entries:
        return 'intermediate'

    chapter_progress_entries = [e for e in progress_entries if e.chapter_id]
    if not chapter_progress_entries:
        return 'intermediate'

    avg_time_ratio = sum(
        entry.time_spent_minutes / (
            int(Chapter.query.get(entry.chapter_id).estimated_study_time or 30)
        )
        for entry in chapter_progress_entries
    ) / len(chapter_progress_entries)

    if avg_time_ratio > 1.5:
        return 'beginner'  # Taking longer than expected
    elif avg_time_ratio < 0.7:
        return 'advanced'  # Going faster than expected
    else:
        return 'intermediate'


def _get_domain_specific_strategies(struggle_domains: list) -> list:
    """Get learning strategies specific to domains where user is struggling."""
    strategies = {
        'economics': [
            'Focus on real-world examples and current events',
            'Practice with economic calculators and models',
            'Review graphical representations of economic concepts'
        ],
        'computer_science': [
            'Code along with examples in your preferred language',
            'Build small projects to apply concepts',
            'Use visualization tools for algorithms and data structures'
        ],
        'mathematics': [
            'Work through problems step-by-step',
            'Use visual aids and geometric interpretations',
            'Practice regularly with spaced repetition'
        ],
        'business': [
            'Analyze real company case studies',
            'Connect theories to current business news',
            'Practice with business simulation tools'
        ]
    }

    recommended = []
    for domain in struggle_domains[:3]:  # Top 3 struggle areas
        if domain in strategies:
            recommended.extend(strategies[domain])

    return recommended or [
        'Review difficult concepts multiple times',
        'Take breaks between study sessions',
        'Ask questions when concepts are unclear',
        'Use active recall techniques'
    ]