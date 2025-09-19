import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from models import (
    db, Course, Subject, Chapter, CourseEnrollment, UserProgress, Bookmark,
    QuizResult, StudySession, update_course_stats, update_subject_stats,
    update_chapter_stats, get_user_course_progress, get_adaptive_recommendations
)
import ai_service


def create_app():
    """
    Adaptive factory function for creating multi-subject learning applications.
    """
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'adaptive-learning-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adaptive_study_app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB for large PDFs

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # --- Helper Functions ---
    def get_user_id():
        """Get or create session-based user ID."""
        if 'user_id' not in session:
            import uuid
            session['user_id'] = str(uuid.uuid4())
        return session['user_id']

    def start_study_session(course_id=None, subject_id=None, chapter_id=None):
        """Start a new study session for analytics."""
        user_id = get_user_id()

        # End any existing active session
        active_session = StudySession.query.filter_by(
            user_id=user_id, session_end=None
        ).first()

        if active_session:
            active_session.session_end = datetime.utcnow()
            active_session.duration_minutes = int(
                (active_session.session_end - active_session.session_start).total_seconds() / 60
            )

        # Start new session
        new_session = StudySession(
            user_id=user_id,
            course_id=course_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            activities=json.dumps([])
        )
        db.session.add(new_session)
        db.session.commit()

        session['active_study_session'] = new_session.id
        return new_session.id

    def log_study_activity(activity_type: str, details: dict = None):
        """Log an activity in the current study session."""
        if 'active_study_session' not in session:
            return

        study_session = StudySession.query.get(session['active_study_session'])
        if study_session and not study_session.session_end:
            activities = json.loads(study_session.activities or '[]')
            activities.append({
                'type': activity_type,
                'timestamp': datetime.utcnow().isoformat(),
                'details': details or {}
            })
            study_session.activities = json.dumps(activities)
            db.session.commit()

    # =========================================================================
    # --- Course Management Routes ---
    # =========================================================================

    @app.route('/')
    def index():
        """Enhanced homepage with course-based organization."""
        user_id = get_user_id()

        # Get user's enrolled courses
        enrollments = CourseEnrollment.query.filter_by(user_id=user_id).all()
        enrolled_courses = [enrollment.course for enrollment in enrollments]

        # Get all available courses
        all_courses = Course.query.order_by(Course.created_at.desc()).all()

        # Get recent study activity
        recent_sessions = StudySession.query.filter_by(user_id=user_id) \
            .order_by(StudySession.session_start.desc()).limit(5).all()

        # Get recommendations if user has courses
        recommendations = {}
        if enrolled_courses:
            # Get recommendations for the most recently active course
            latest_course = max(enrolled_courses, key=lambda c: max(
                e.last_activity for e in c.enrollments if e.user_id == user_id
            ))
            recommendations = get_adaptive_recommendations(user_id, latest_course.id)

        return render_template('index.html',
                               enrolled_courses=enrolled_courses,
                               all_courses=all_courses,
                               recent_sessions=recent_sessions,
                               recommendations=recommendations)

    @app.route('/course/create', methods=['GET', 'POST'])
    def create_course():
        """Create a new course with enhanced intelligence gathering."""
        if request.method == 'POST':
            course_name = request.form.get('course_name')
            description = request.form.get('description', '')
            academic_level = request.form.get('academic_level', 'masters')
            institution = request.form.get('institution', '')
            course_code = request.form.get('course_code', '')
            career_goals = request.form.getlist('career_goals')
            learning_objectives = request.form.get('learning_objectives', '').split('\n')
            learning_objectives = [obj.strip() for obj in learning_objectives if obj.strip()]

            if not course_name:
                flash('Course name is required.', 'danger')
                return redirect(request.url)

            # Check if course already exists
            existing = Course.query.filter_by(name=course_name).first()
            if existing:
                flash('A course with this name already exists.', 'warning')
                return redirect(request.url)

            # Gather enhanced course intelligence
            student_input = {
                "course_name": course_name,
                "university": institution,
                "course_code": course_code,
                "learning_objectives": learning_objectives,
                "career_goals": career_goals,
                "academic_level": academic_level
            }

            # Get AI-enhanced course context
            try:
                enhanced_context = ai_service.enhance_course_with_web_intelligence(
                    course_name, institution, student_input
                )
                course_intelligence = json.dumps(enhanced_context)

                # Extract domain information
                synthesis = enhanced_context.get("synthesis", {})
                estimated_hours = synthesis.get("difficulty_level", "intermediate")
                if "advanced" in str(estimated_hours).lower():
                    estimated_hours = 120
                elif "beginner" in str(estimated_hours).lower():
                    estimated_hours = 60
                else:
                    estimated_hours = 90

            except Exception as e:
                print(f"Course intelligence gathering failed: {e}")
                course_intelligence = json.dumps({"error": str(e), "fallback": True})
                estimated_hours = 80

            # Create course with enhanced metadata
            new_course = Course(
                name=course_name,
                description=description,
                academic_level=academic_level,
                institution=institution,
                estimated_study_hours=estimated_hours
            )

            db.session.add(new_course)
            db.session.commit()

            # Create enrollment for the creator
            enrollment = CourseEnrollment(
                user_id=get_user_id(),
                course_id=new_course.id,
                preferred_difficulty=academic_level
            )
            db.session.add(enrollment)
            db.session.commit()

            flash(f'Course "{course_name}" created successfully with AI-enhanced context!', 'success')
            return redirect(url_for('view_course', course_id=new_course.id))

        return render_template('create_course.html')

    @app.route('/course/<int:course_id>')
    def view_course(course_id):
        """View course with all subjects and progress tracking."""
        course = db.get_or_404(Course, course_id)
        user_id = get_user_id()

        # Enroll user if not already enrolled
        enrollment = CourseEnrollment.query.filter_by(
            user_id=user_id, course_id=course_id
        ).first()

        if not enrollment:
            enrollment = CourseEnrollment(user_id=user_id, course_id=course_id)
            db.session.add(enrollment)
            db.session.commit()

        # Update last activity
        enrollment.last_activity = datetime.utcnow()
        db.session.commit()

        # Get subjects with progress info
        subjects_with_progress = []
        for subject in course.subjects:
            progress = UserProgress.query.filter_by(
                user_id=user_id, subject_id=subject.id, chapter_id=None
            ).first()

            chapter_progress = UserProgress.query.filter_by(
                user_id=user_id, subject_id=subject.id
            ).filter(UserProgress.chapter_id.isnot(None)).all()

            subjects_with_progress.append({
                'subject': subject,
                'overall_progress': progress,
                'chapter_progress': {cp.chapter_id: cp for cp in chapter_progress}
            })

        # Get course progress summary
        progress_summary = get_user_course_progress(user_id, course_id)
        recommendations = get_adaptive_recommendations(user_id, course_id)

        # Start study session for this course
        start_study_session(course_id=course_id)

        return render_template('course.html',
                               course=course,
                               subjects_with_progress=subjects_with_progress,
                               progress_summary=progress_summary,
                               recommendations=recommendations)

    @app.route('/course/<int:course_id>/subject/<int:subject_id>')
    def view_subject(course_id, subject_id):
        """View subject with adaptive content and progress tracking."""
        subject = db.get_or_404(Subject, subject_id)
        if subject.course_id != course_id:
            abort(404)

        user_id = get_user_id()

        # Get chapter progress
        chapter_progress = {}
        progress_entries = UserProgress.query.filter_by(
            user_id=user_id, subject_id=subject_id
        ).all()

        for progress in progress_entries:
            if progress.chapter_id:
                chapter_progress[progress.chapter_id] = progress

        # Update subject-level progress
        subject_progress = UserProgress.query.filter_by(
            user_id=user_id, subject_id=subject_id, chapter_id=None
        ).first()

        if not subject_progress:
            subject_progress = UserProgress(
                user_id=user_id,
                subject_id=subject_id,
                status='in_progress'
            )
            db.session.add(subject_progress)
            db.session.commit()

        # Parse subject analysis for adaptive features
        subject_analysis = {}
        if subject.subject_analysis:
            try:
                subject_analysis = json.loads(subject.subject_analysis)
            except json.JSONDecodeError:
                pass

        # Start study session for this subject
        start_study_session(course_id=course_id, subject_id=subject_id)
        log_study_activity('subject_access', {'subject_name': subject.name})

        return render_template('subject.html',
                               course=subject.course,
                               subject=subject,
                               chapter_progress=chapter_progress,
                               subject_analysis=subject_analysis)

    @app.route('/course/<int:course_id>/subject/<int:subject_id>/chapter/<int:chapter_id>')
    def view_chapter(course_id, subject_id, chapter_id):
        """Enhanced chapter view with domain-adaptive content."""
        chapter = db.get_or_404(Chapter, chapter_id)
        if chapter.subject_id != subject_id or chapter.subject.course_id != course_id:
            abort(404)

        user_id = get_user_id()

        # Clear Q&A when moving between chapters
        if session.get('qna_chapter_id') != chapter_id:
            session.pop('last_question', None)
            session.pop('last_answer', None)
        session['qna_chapter_id'] = chapter_id

        # Parse content blocks
        content_blocks = []
        if chapter.content_blocks:
            try:
                content_blocks = json.loads(chapter.content_blocks)
            except json.JSONDecodeError:
                flash('Error decoding chapter content.', 'danger')

        # Get user bookmarks for this chapter
        user_bookmarks = Bookmark.query.filter_by(
            user_id=user_id, chapter_id=chapter_id
        ).all()
        bookmark_indices = {bookmark.content_block_index for bookmark in user_bookmarks}

        # Update chapter progress
        chapter_progress = UserProgress.query.filter_by(
            user_id=user_id, subject_id=subject_id, chapter_id=chapter_id
        ).first()

        if not chapter_progress:
            chapter_progress = UserProgress(
                user_id=user_id,
                subject_id=subject_id,
                chapter_id=chapter_id,
                status='in_progress'
            )
            db.session.add(chapter_progress)
        else:
            chapter_progress.last_accessed = datetime.utcnow()
            chapter_progress.sessions_count += 1

        db.session.commit()

        # Start study session for this chapter
        start_study_session(course_id=course_id, subject_id=subject_id, chapter_id=chapter_id)
        log_study_activity('chapter_access', {
            'chapter_title': chapter.title,
            'subject_domain': chapter.subject.subject_domain
        })

        return render_template('chapter.html',
                               course_id=course_id,
                               subject=chapter.subject,
                               chapter=chapter,
                               content_blocks=content_blocks,
                               bookmark_indices=bookmark_indices,
                               chapter_progress=chapter_progress)

    # =========================================================================
    # --- PDF Upload and Processing Routes ---
    # =========================================================================

    @app.route('/course/<int:course_id>/upload', methods=['GET', 'POST'])
    def upload_pdf(course_id):
        """Enhanced PDF upload with adaptive processing."""
        course = db.get_or_404(Course, course_id)

        if request.method == 'POST':
            subject_name = request.form.get('subject_name')
            pdf_file = request.files.get('pdf_file')
            course_description = request.form.get('course_description', course.description)

            if not subject_name or not pdf_file or pdf_file.filename == '':
                flash('Missing subject name or file.', 'danger')
                return redirect(request.url)

            if pdf_file and pdf_file.filename.endswith('.pdf'):
                filename = secure_filename(pdf_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf_file.save(filepath)

                # Get existing books in course for context
                existing_subjects = Subject.query.filter_by(course_id=course_id).all()
                existing_books = [
                    {'name': s.name, 'summary': s.overall_summary, 'domain': s.subject_domain}
                    for s in existing_subjects
                ]

                flash(f'File "{filename}" uploaded. Processing with adaptive AI... This may take a moment.', 'info')

                start_time = datetime.utcnow()

                # Enhanced processing with course intelligence
                try:
                    # Get course intelligence for context
                    user_id = get_user_id()
                    enrollment = CourseEnrollment.query.filter_by(
                        user_id=user_id, course_id=course_id
                    ).first()

                    student_input = {
                        "course_name": course.name,
                        "university": course.institution or "",
                        "academic_level": course.academic_level,
                        "career_goals": [],  # Could be enhanced from user profile
                        "learning_objectives": []
                    }

                    # Get enhanced course context
                    enhanced_context = ai_service.enhance_course_with_web_intelligence(
                        course.name, course.institution or "", student_input
                    )

                    # Process PDF with full course intelligence
                    processed_data = ai_service.process_pdf_with_course_intelligence(
                        filepath, subject_name, enhanced_context
                    )

                except Exception as e:
                    print(f"Enhanced processing failed, falling back to basic: {e}")
                    # Fallback to basic processing
                    processed_data = ai_service.process_pdf_and_extract_chapters(
                        filepath, subject_name, course_description, existing_books
                    )

                processing_time = int((datetime.utcnow() - start_time).total_seconds())

                if 'error' in processed_data:
                    flash(f"AI processing failed: {processed_data['error']}", 'danger')
                    return redirect(request.url)

                try:
                    # Extract subject analysis and metadata
                    subject_analysis = processed_data.get('subject_analysis', {})
                    course_intelligence = processed_data.get('course_intelligence', {})
                    processing_metadata = processed_data.get('processing_metadata', {})

                    # Create the new subject with adaptive metadata
                    new_subject = Subject(
                        name=processed_data.get('subject_name', subject_name),
                        preface=json.dumps(processed_data.get('preface', {})),
                        overall_summary=json.dumps(processed_data.get('overall_summary', {})),
                        subject_domain=subject_analysis.get('subject_domain', 'general'),
                        learning_style=subject_analysis.get('learning_style', 'mixed'),
                        complexity_level=subject_analysis.get('complexity_level', 'intermediate'),
                        subject_analysis=json.dumps(subject_analysis),
                        original_filename=filename,
                        file_size_mb=round(os.path.getsize(filepath) / (1024 * 1024), 2),
                        processing_time_seconds=processing_time,
                        course_id=course_id
                    )
                    db.session.add(new_subject)

                    # Add chapters with enhanced metadata
                    for i, ch_data in enumerate(processed_data.get('chapters', []), 1):
                        chapter_metadata = ch_data.get('chapter_metadata', {})

                        new_chapter = Chapter(
                            title=ch_data.get('title'),
                            chapter_number=i,
                            intro_summary=json.dumps(ch_data.get('intro_summary', {})),
                            content_blocks=json.dumps(ch_data.get('content_blocks', [])),
                            chapter_metadata=json.dumps(chapter_metadata),
                            difficulty_level=chapter_metadata.get('difficulty_level', 'intermediate'),
                            estimated_study_time=chapter_metadata.get('estimated_study_time', 30),
                            subject=new_subject
                        )
                        db.session.add(new_chapter)

                    db.session.commit()

                    # Update statistics
                    update_subject_stats(new_subject.id)
                    for chapter in new_subject.chapters:
                        update_chapter_stats(chapter.id)

                    domain_display = subject_analysis.get('subject_domain', 'general').replace('_', ' ').title()
                    flash(f'Successfully processed "{filename}" as {domain_display} content!', 'success')
                    return redirect(url_for('view_subject', course_id=course_id, subject_id=new_subject.id))

                except Exception as e:
                    db.session.rollback()
                    flash(f"Database error: Failed to save subject. Reason: {e}", 'danger')
            else:
                flash('Please upload a PDF file.', 'danger')

        return render_template('upload_pdf.html', course=course)

    # =========================================================================
    # --- Adaptive Content Routes ---
    # =========================================================================

    @app.route('/api/simplify-concept', methods=['POST'])
    def simplify_concept():
        """Simplify concepts with domain-adaptive approaches."""
        data = request.get_json()
        concept_text = data.get('concept_text')
        difficulty_level = data.get('difficulty_level', 'beginner')
        subject_domain = data.get('subject_domain', 'general')
        learning_style = data.get('learning_style', 'mixed')

        if not concept_text:
            return jsonify({'error': 'No concept text provided'}), 400

        simplified = ai_service.simplify_concept(
            concept_text, difficulty_level, subject_domain, learning_style
        )

        # Log the activity
        log_study_activity('concept_simplification', {
            'difficulty_level': difficulty_level,
            'subject_domain': subject_domain
        })

        return jsonify({'simplified_text': simplified})

    @app.route('/api/generate-visualization', methods=['POST'])
    def generate_visualization():
        """Generate domain-appropriate visualizations."""
        data = request.get_json()
        description = data.get('description')
        data_context = data.get('data_context', '')
        subject_domain = data.get('subject_domain', 'general')

        if not description:
            return jsonify({'error': 'No description provided'}), 400

        visualization_data = ai_service.generate_interactive_visualization(
            description, data_context, subject_domain
        )

        log_study_activity('visualization_generation', {
            'subject_domain': subject_domain,
            'visualization_type': visualization_data.get('visualization_type')
        })

        return jsonify(visualization_data)

    # =========================================================================
    # --- Enhanced Q&A Routes ---
    # =========================================================================

    @app.route('/ask/<int:chapter_id>', methods=['POST'])
    def ask_question(chapter_id):
        """Domain-adaptive Q&A system."""
        chapter = db.get_or_404(Chapter, chapter_id)
        question = request.form.get('question')

        if not question:
            flash("Please enter a question.", 'warning')
        else:
            context = chapter.intro_summary
            subject_domain = chapter.subject.subject_domain

            answer = ai_service.answer_question_from_context(
                question, context, subject_domain
            )

            session['last_question'] = question
            session['last_answer'] = answer
            session['qna_chapter_id'] = chapter_id

            # Update progress - user asked a question
            user_id = get_user_id()
            progress = UserProgress.query.filter_by(
                user_id=user_id, chapter_id=chapter_id
            ).first()
            if progress:
                progress.questions_asked += 1
                db.session.commit()

            log_study_activity('question_asked', {
                'subject_domain': subject_domain,
                'question_length': len(question)
            })

        return redirect(url_for(
            'view_chapter',
            course_id=chapter.subject.course_id,
            subject_id=chapter.subject_id,
            chapter_id=chapter.id
        ))

    # =========================================================================
    # --- Enhanced Quiz Routes ---
    # =========================================================================

    @app.route('/generate-quiz/<int:chapter_id>')
    def generate_quiz(chapter_id):
        """Generate domain-adaptive quiz."""
        chapter = db.get_or_404(Chapter, chapter_id)
        user_id = get_user_id()

        # Get user's preferred difficulty
        user_progress = UserProgress.query.filter_by(
            user_id=user_id, chapter_id=chapter_id
        ).first()

        difficulty = user_progress.difficulty_preference if user_progress else 'intermediate'
        subject_domain = chapter.subject.subject_domain

        quiz_data = ai_service.generate_quiz_from_summary(
            chapter.intro_summary, subject_domain, difficulty
        )

        if not quiz_data or 'error' in quiz_data:
            flash(quiz_data.get('error', 'Could not generate quiz.'), 'danger')
            return redirect(url_for(
                'view_chapter',
                course_id=chapter.subject.course_id,
                subject_id=chapter.subject_id,
                chapter_id=chapter.id
            ))

        log_study_activity('quiz_started', {
            'subject_domain': subject_domain,
            'difficulty': difficulty,
            'question_count': len(quiz_data.get('questions', []))
        })

        return render_template('quiz.html',
                               chapter=chapter,
                               quiz_data=quiz_data,
                               difficulty=difficulty)

    @app.route('/submit-quiz/<int:chapter_id>', methods=['POST'])
    def submit_quiz(chapter_id):
        """Enhanced quiz grading with adaptive analytics."""
        chapter = db.get_or_404(Chapter, chapter_id)
        user_id = get_user_id()

        try:
            quiz_data_json = request.form.get('quiz_data')
            quiz_data = json.loads(quiz_data_json)
            questions = quiz_data.get('questions', [])
            quiz_start_time = request.form.get('start_time')

            score = 0
            total = len(questions)
            user_answers = {}
            concept_performance = {}

            # Analyze performance by question type and concept
            for i, question in enumerate(questions):
                user_answer = request.form.get(f'question_{i}')
                correct_answer = question.get('correct_answer_index')
                is_correct = user_answer is not None and int(user_answer) == correct_answer

                user_answers[i] = {
                    'user_answer': int(user_answer) if user_answer is not None else None,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                    'question_type': question.get('question_type', 'multiple_choice'),
                    'concept_tested': question.get('concept_tested', 'general')
                }

                if is_correct:
                    score += 1

                # Track concept mastery
                concept = question.get('concept_tested', 'general')
                if concept not in concept_performance:
                    concept_performance[concept] = {'correct': 0, 'total': 0}
                concept_performance[concept]['total'] += 1
                if is_correct:
                    concept_performance[concept]['correct'] += 1

            percentage = (score / total * 100) if total > 0 else 0

            # Calculate time taken
            time_taken = None
            if quiz_start_time:
                try:
                    start_dt = datetime.fromisoformat(quiz_start_time)
                    time_taken = int((datetime.utcnow() - start_dt).total_seconds())
                except:
                    pass

            # Determine areas for improvement
            weak_concepts = [
                concept for concept, perf in concept_performance.items()
                if perf['correct'] / perf['total'] < 0.7
            ]

            # Save enhanced quiz result
            quiz_result = QuizResult(
                user_id=user_id,
                chapter_id=chapter_id,
                quiz_title=quiz_data.get('title', f'{chapter.title} Quiz'),
                quiz_type='practice',
                subject_domain=chapter.subject.subject_domain,
                score=score,
                total_questions=total,
                percentage=percentage,
                difficulty_level=quiz_data.get('difficulty', 'intermediate'),
                time_taken_seconds=time_taken,
                concept_mastery=json.dumps(concept_performance),
                areas_for_improvement=json.dumps(weak_concepts),
                questions_and_answers=json.dumps({
                    'questions': questions,
                    'user_answers': user_answers
                })
            )
            db.session.add(quiz_result)

            # Update user progress with detailed analytics
            progress = UserProgress.query.filter_by(
                user_id=user_id, chapter_id=chapter_id
            ).first()

            if progress:
                progress.quizzes_taken += 1
                # Update average quiz score
                if progress.avg_quiz_score == 0:
                    progress.avg_quiz_score = percentage
                else:
                    progress.avg_quiz_score = (progress.avg_quiz_score + percentage) / 2

                # Update struggle areas
                if weak_concepts:
                    existing_struggles = json.loads(progress.struggle_areas or '[]')
                    updated_struggles = list(set(existing_struggles + weak_concepts))
                    progress.struggle_areas = json.dumps(updated_struggles)

                # Update mastery level based on consistent performance
                if progress.avg_quiz_score >= 90:
                    progress.mastery_level = 'expert'
                elif progress.avg_quiz_score >= 80:
                    progress.mastery_level = 'proficient'
                elif progress.avg_quiz_score >= 70:
                    progress.mastery_level = 'developing'
                else:
                    progress.mastery_level = 'novice'

                db.session.commit()

            log_study_activity('quiz_completed', {
                'subject_domain': chapter.subject.subject_domain,
                'score': score,
                'total': total,
                'percentage': percentage,
                'time_taken': time_taken,
                'weak_concepts': weak_concepts
            })

            return render_template('quiz_result.html',
                                   chapter=chapter,
                                   score=score,
                                   total=total,
                                   percentage=percentage,
                                   quiz_data=quiz_data,
                                   user_answers=user_answers,
                                   concept_performance=concept_performance,
                                   weak_concepts=weak_concepts,
                                   time_taken=time_taken)

        except Exception as e:
            flash(f"An error occurred while grading the quiz: {e}", 'danger')
            return redirect(url_for(
                'view_chapter',
                course_id=chapter.subject.course_id,
                subject_id=chapter.subject_id,
                chapter_id=chapter.id
            ))

    # =========================================================================
    # --- Bookmark Routes ---
    # =========================================================================

    @app.route('/api/bookmark/add', methods=['POST'])
    def add_bookmark():
        """Enhanced bookmark system with learning context."""
        user_id = get_user_id()
        data = request.get_json()

        chapter_id = data.get('chapter_id')
        content_block_index = data.get('content_block_index')
        title = data.get('title')
        note = data.get('note', '')
        content_block_type = data.get('content_block_type', 'concept')
        reason = data.get('reason', 'important')

        if not all([chapter_id, title]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if bookmark already exists
        existing = Bookmark.query.filter_by(
            user_id=user_id,
            chapter_id=chapter_id,
            content_block_index=content_block_index
        ).first()

        if existing:
            return jsonify({'error': 'Bookmark already exists'}), 400

        # Get current difficulty level from progress
        progress = UserProgress.query.filter_by(
            user_id=user_id, chapter_id=chapter_id
        ).first()
        current_difficulty = progress.difficulty_preference if progress else 'intermediate'

        bookmark = Bookmark(
            user_id=user_id,
            chapter_id=chapter_id,
            content_block_index=content_block_index,
            content_block_type=content_block_type,
            title=title,
            note=note,
            reason_for_bookmark=reason,
            difficulty_when_bookmarked=current_difficulty
        )

        db.session.add(bookmark)

        # Update progress bookmarks count
        if progress:
            progress.concepts_bookmarked += 1

        db.session.commit()

        log_study_activity('bookmark_created', {
            'content_type': content_block_type,
            'reason': reason
        })

        return jsonify({
            'message': 'Bookmark added successfully',
            'bookmark_id': bookmark.id
        })

    @app.route('/bookmark/remove/<int:bookmark_id>', methods=['DELETE'])
    def remove_bookmark(bookmark_id):
        """Remove a bookmark."""
        user_id = get_user_id()
        bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()

        if not bookmark:
            return jsonify({'error': 'Bookmark not found'}), 404

        db.session.delete(bookmark)
        db.session.commit()

        return jsonify({'message': 'Bookmark removed successfully'})

    @app.route('/bookmarks')
    def view_bookmarks():
        """Enhanced bookmark management with filtering and organization."""
        user_id = get_user_id()

        # Get bookmarks with related data
        bookmarks = db.session.query(Bookmark) \
            .join(Chapter) \
            .join(Subject) \
            .join(Course) \
            .filter(Bookmark.user_id == user_id) \
            .order_by(Bookmark.created_at.desc()) \
            .all()

        # Group bookmarks by course and subject
        organized_bookmarks = {}
        for bookmark in bookmarks:
            course_name = bookmark.chapter.subject.course.name
            subject_name = bookmark.chapter.subject.name
            subject_domain = bookmark.chapter.subject.subject_domain

            if course_name not in organized_bookmarks:
                organized_bookmarks[course_name] = {}

            if subject_name not in organized_bookmarks[course_name]:
                organized_bookmarks[course_name][subject_name] = {
                    'domain': subject_domain,
                    'bookmarks': []
                }

            organized_bookmarks[course_name][subject_name]['bookmarks'].append(bookmark)

        return render_template('bookmarks.html',
                               organized_bookmarks=organized_bookmarks)

    # =========================================================================
    # --- Analytics and Progress Routes ---
    # =========================================================================

    @app.route('/analytics')
    def view_analytics():
        """Comprehensive learning analytics dashboard."""
        user_id = get_user_id()

        # Get all user's enrollments and progress
        enrollments = CourseEnrollment.query.filter_by(user_id=user_id).all()

        analytics_data = {}
        for enrollment in enrollments:
            course_progress = get_user_course_progress(user_id, enrollment.course_id)
            recommendations = get_adaptive_recommendations(user_id, enrollment.course_id)

            analytics_data[enrollment.course.name] = {
                'course': enrollment.course,
                'progress': course_progress,
                'recommendations': recommendations
            }

        # Get recent study sessions
        recent_sessions = StudySession.query.filter_by(user_id=user_id) \
            .filter(StudySession.session_end.isnot(None)) \
            .order_by(StudySession.session_start.desc()) \
            .limit(10).all()

        # Calculate learning velocity and patterns
        total_study_time = sum(session.duration_minutes or 0 for session in recent_sessions)
        avg_session_length = total_study_time / len(recent_sessions) if recent_sessions else 0

        # Get subject domain performance
        quiz_results = QuizResult.query.filter_by(user_id=user_id).all()
        domain_performance = {}
        for qr in quiz_results:
            domain = qr.subject_domain or 'general'
            if domain not in domain_performance:
                domain_performance[domain] = {'scores': [], 'count': 0}
            domain_performance[domain]['scores'].append(qr.percentage)
            domain_performance[domain]['count'] += 1

        # Calculate average performance by domain
        for domain, data in domain_performance.items():
            data['average'] = sum(data['scores']) / len(data['scores'])

        return render_template('analytics.html',
                               analytics_data=analytics_data,
                               recent_sessions=recent_sessions,
                               total_study_time=total_study_time,
                               avg_session_length=avg_session_length,
                               domain_performance=domain_performance)

    @app.route('/mark-chapter-complete/<int:chapter_id>', methods=['POST'])
    def mark_chapter_complete(chapter_id):
        """Mark a chapter as completed."""
        chapter = db.get_or_404(Chapter, chapter_id)
        user_id = get_user_id()

        progress = UserProgress.query.filter_by(
            user_id=user_id, chapter_id=chapter_id
        ).first()

        if not progress:
            progress = UserProgress(
                user_id=user_id,
                subject_id=chapter.subject_id,
                chapter_id=chapter_id,
                status='completed',
                completion_percentage=100.0,
                completed_at=datetime.utcnow()
            )
            db.session.add(progress)
        else:
            progress.status = 'completed'
            progress.completion_percentage = 100.0
            progress.completed_at = datetime.utcnow()

        db.session.commit()

        flash(f'Chapter "{chapter.title}" marked as completed!', 'success')
        return redirect(url_for('view_chapter',
                                course_id=chapter.subject.course_id,
                                subject_id=chapter.subject_id,
                                chapter_id=chapter_id))

    # =========================================================================
    # --- API Routes for Dynamic Content ---
    # =========================================================================

    @app.route('/api/chapter/<int:chapter_id>/stats')
    def get_chapter_stats(chapter_id):
        """Get chapter statistics for analytics."""
        chapter = db.get_or_404(Chapter, chapter_id)
        user_id = get_user_id()

        progress = UserProgress.query.filter_by(
            user_id=user_id, chapter_id=chapter_id
        ).first()

        quiz_results = QuizResult.query.filter_by(
            user_id=user_id, chapter_id=chapter_id
        ).all()

        return jsonify({
            'chapter': chapter.to_dict(),
            'progress': {
                'status': progress.status if progress else 'not_started',
                'time_spent': progress.time_spent_minutes if progress else 0,
                'questions_asked': progress.questions_asked if progress else 0,
                'quizzes_taken': len(quiz_results),
                'avg_quiz_score': sum(qr.percentage for qr in quiz_results) / len(quiz_results) if quiz_results else 0
            }
        })

    @app.route('/api/course/<int:course_id>/detailed-progress')
    def get_detailed_course_progress(course_id):
        """Get detailed progress analytics for a course."""
        user_id = get_user_id()
        course = db.get_or_404(Course, course_id)

        # Get overall progress
        overall_progress = get_user_course_progress(user_id, course_id)

        # Get subject-level progress
        subject_progress = []
        for subject in course.subjects:
            progress_entries = UserProgress.query.filter_by(
                user_id=user_id, subject_id=subject.id
            ).all()

            completed_chapters = len([p for p in progress_entries if p.status == 'completed' and p.chapter_id])
            total_chapters = len(subject.chapters)
            progress_pct = (completed_chapters / total_chapters * 100) if total_chapters > 0 else 0

            quiz_results = QuizResult.query.join(Chapter).filter(
                QuizResult.user_id == user_id,
                Chapter.subject_id == subject.id
            ).all()

            avg_quiz = sum(qr.percentage for qr in quiz_results) / len(quiz_results) if quiz_results else 0

            # Determine mastery level
            mastery = 'novice'
            if progress_pct >= 90 and avg_quiz >= 85:
                mastery = 'expert'
            elif progress_pct >= 70 and avg_quiz >= 75:
                mastery = 'proficient'
            elif progress_pct >= 50 or avg_quiz >= 60:
                mastery = 'developing'

            subject_progress.append({
                'name': subject.name,
                'progress': int(progress_pct),
                'mastery': mastery,
                'quiz_average': int(avg_quiz),
                'domain': subject.subject_domain
            })

        return jsonify({
            'overall_progress': overall_progress.get('overall_progress', 0),
            'completed_chapters': overall_progress.get('chapters_completed', '0/0').split('/')[0],
            'total_study_hours': overall_progress.get('total_study_time_hours', 0),
            'average_quiz_score': overall_progress.get('average_quiz_score', 0),
            'subject_progress': subject_progress
        })

    @app.route('/api/end-study-session', methods=['POST'])
    def end_study_session():
        """End current study session and calculate engagement metrics."""
        if 'active_study_session' not in session:
            return jsonify({'message': 'No active session'}), 200

        study_session = StudySession.query.get(session['active_study_session'])
        if study_session and not study_session.session_end:
            study_session.session_end = datetime.utcnow()
            study_session.duration_minutes = int(
                (study_session.session_end - study_session.session_start).total_seconds() / 60
            )

            # Calculate engagement metrics based on activities
            activities = json.loads(study_session.activities or '[]')
            study_session.engagement_score = min(100, len(activities) * 10)  # Simple metric

            db.session.commit()

        session.pop('active_study_session', None)
        return jsonify({'message': 'Study session ended successfully'})

    @app.route('/api/bookmark/count')
    def get_bookmark_count():
        """Get total bookmark count for user."""
        user_id = get_user_id()
        count = Bookmark.query.filter_by(user_id=user_id).count()
        return jsonify({'count': count})

    @app.route('/api/ai-service/test')
    def test_ai_service():
        """Test AI service connection."""
        result = ai_service.test_ai_service_connection()
        return jsonify(result)

    @app.route('/api/ai-service/stats')
    def get_ai_service_stats():
        """Get AI service statistics."""
        result = ai_service.get_ai_service_stats()
        return jsonify(result)

    # =========================================================================
    # --- Utility Routes ---
    # =========================================================================

    @app.route('/api/course-intelligence/<course_name>')
    def get_course_intelligence(course_name):
        """Get AI-researched course intelligence."""
        university = request.args.get('university', '')
        course_code = request.args.get('course_code', '')

        intelligence = ai_service.gather_web_course_intelligence(
            course_name, university, course_code
        )

        return jsonify(intelligence)

    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'ai_service': 'configured' if ai_service._is_api_configured() else 'not_configured'
        })

    # =========================================================================
    # --- Error Handlers ---
    # =========================================================================

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def too_large_error(error):
        flash('File too large. Maximum size is 100MB.', 'danger')
        return redirect(request.url)

    # =========================================================================
    # --- Template Filters ---
    # =========================================================================

    @app.template_filter('from_json')
    def from_json_filter(json_str):
        """Template filter to parse JSON strings."""
        if not json_str:
            return {}
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    @app.template_filter('timeago')
    def timeago_filter(datetime_obj):
        """Template filter for human-readable time ago."""
        if not datetime_obj:
            return 'Never'

        now = datetime.utcnow()
        diff = now - datetime_obj

        if diff.days > 0:
            return f'{diff.days} day{"s" if diff.days != 1 else ""} ago'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
        else:
            return 'Just now'

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)