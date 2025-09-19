import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from domain_configurations import (
    get_domain_config, get_content_block_templates,
    format_existing_books_context, DIFFICULTY_ADAPTATIONS,
    LEARNING_STYLE_ADAPTATIONS
)

# --- Setup and Configuration ---
PROMPTS_DIR = Path(__file__).resolve().parent / 'prompts'
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
    print("INFO: GEMINI_API_KEY is not configured. AI services will be disabled.")
    genai.configure(api_key="placeholder")
    pro_model = None
    flash_model = None
else:
    genai.configure(api_key=GEMINI_API_KEY)
    PRO_MODEL_NAME = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro-latest")
    FLASH_MODEL_NAME = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash-latest")

    try:
        pro_model = genai.GenerativeModel(PRO_MODEL_NAME)
        flash_model = genai.GenerativeModel(FLASH_MODEL_NAME)
    except AttributeError as e:
        print(f"ERROR: {e}")
        print("This might be due to an outdated google-generativeai package.")
        pro_model = None
        flash_model = None


# --- Helper Functions ---

def _is_api_configured():
    """Checks if the API key is properly configured and models are available."""
    return (GEMINI_API_KEY and
            GEMINI_API_KEY != "YOUR_API_KEY_HERE" and
            pro_model is not None and
            flash_model is not None)


def _load_prompt_template(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    try:
        with open(PROMPTS_DIR / prompt_name, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Prompt file not found: {prompt_name}")
        return ""


def _clean_json_response(response_text: str) -> str:
    """Clean and extract JSON from AI response."""
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned


def _format_prompt_template(template: str, **kwargs) -> str:
    """Format a prompt template with provided parameters."""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        print(f"WARNING: Missing template parameter: {e}")
        return template


# =========================================================================
# --- Subject Analysis and Adaptation ---
# =========================================================================

def analyze_subject_domain(subject_name: str, course_description: str = "") -> Dict[str, Any]:
    """
    Analyze the subject to determine appropriate learning strategies and content types.
    """
    if not _is_api_configured():
        return {"error": "Cannot analyze subject. Gemini API key is not configured."}

    try:
        analysis_prompt = f"""
        Analyze this academic subject to determine the best learning approach and content transformation strategy:

        Subject: {subject_name}
        Description: {course_description}

        Determine and return JSON with:
        {{
            "subject_domain": "economics|computer_science|mathematics|history|literature|psychology|engineering|medicine|law|business|physics|chemistry|biology|other",
            "learning_style": "theoretical|practical|mixed",
            "complexity_level": "undergraduate|masters|phd|professional",
            "key_characteristics": ["analytical thinking", "memorization heavy", "formula-based", "case study driven", "etc."],
            "content_types": ["concepts", "formulas", "case_studies", "historical_examples", "code_examples", "diagrams", "etc."],
            "career_applications": ["industry applications", "job roles", "professional skills"],
            "visualization_types": ["charts", "diagrams", "flowcharts", "timelines", "network_graphs", "etc."],
            "assessment_methods": ["multiple_choice", "case_analysis", "problem_solving", "essay", "practical_exercises"],
            "real_world_connections": ["how concepts apply in practice", "current industry relevance"],
            "difficulty_factors": ["mathematical complexity", "abstract concepts", "memorization load", "etc."],
            "recommended_examples": ["types of examples that work best for this subject"]
        }}

        Focus on understanding what makes this subject unique and how students in this field typically learn best.
        Return only valid JSON.
        """

        response = flash_model.generate_content(analysis_prompt)
        cleaned_json = _clean_json_response(response.text)
        return json.loads(cleaned_json)

    except Exception as e:
        return {"error": f"Failed to analyze subject. Reason: {e}"}


def process_pdf_and_extract_chapters(file_path: str, subject_name: str, course_description: str = "",
                                     existing_books: list = None) -> dict:
    """
    Process a PDF file with adaptive content transformation using modular prompts.
    """
    if not _is_api_configured():
        return {"error": "Cannot process PDF. Gemini API key is not configured or models unavailable."}

    try:
        # First, analyze the subject domain
        subject_analysis = analyze_subject_domain(subject_name, course_description)
        if "error" in subject_analysis:
            # Fallback to generic processing if analysis fails
            subject_analysis = _get_generic_subject_profile()

        # Get domain configuration
        domain_config = get_domain_config(subject_analysis.get("subject_domain", "general"))

        # Upload the file
        uploaded_file = genai.upload_file(path=file_path, display_name=subject_name)

        # Load and format the extraction prompt template
        template = _load_prompt_template('adaptive_pdf_extraction.txt')
        if not template:
            return {"error": "Could not load PDF extraction prompt template"}

        # Prepare template parameters
        prompt_params = {
            'subject_name': subject_name,
            'subject_domain': subject_analysis.get("subject_domain", "general"),
            'subject_domain_upper': subject_analysis.get("subject_domain", "general").upper().replace('_', ' '),
            'course_description': course_description,
            'learning_style': subject_analysis.get("learning_style", "mixed"),
            'complexity_level': subject_analysis.get("complexity_level", "intermediate"),
            'content_types': ', '.join(subject_analysis.get("content_types", ["concepts", "examples"])),
            'career_applications': ', '.join(subject_analysis.get("career_applications", ["professional development"])),
            'visualization_types': ', '.join(subject_analysis.get("visualization_types", ["charts"])),
            'existing_books_context': format_existing_books_context(existing_books or []),
            'domain_specific_instructions': domain_config.get("extraction_instructions",
                                                              "Focus on clear explanations with practical examples"),
            'content_block_templates': get_content_block_templates(
                subject_analysis.get("subject_domain", "general"),
                subject_analysis.get("content_types", ["concepts"])
            ),
            'content_block_guidelines': domain_config.get("extraction_instructions", "")
        }

        # Format the prompt
        formatted_prompt = _format_prompt_template(template, **prompt_params)

        response = pro_model.generate_content([formatted_prompt, uploaded_file])

        if not response.parts:
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                return {"error": f"AI response was blocked. Reason: {response.prompt_feedback.block_reason.name}"}
            return {
                "error": "AI returned an empty response. This may be due to a safety block or an issue with the prompt."}

        cleaned_json = _clean_json_response(response.text)
        result = json.loads(cleaned_json)

        # Add subject analysis metadata
        result["subject_analysis"] = subject_analysis

        return result

    except Exception as e:
        return {"error": f"Failed to process PDF. Reason: {type(e).__name__}: {e}"}


def answer_question_from_context(question: str, context: str, subject_domain: str = "general") -> str:
    """Answer questions using modular Q&A prompt template."""
    if not _is_api_configured():
        return "Error: Cannot answer question. Gemini API key is not configured or models unavailable."

    try:
        # Load Q&A prompt template
        template = _load_prompt_template('adaptive_qa.txt')
        if not template:
            return "Error: Could not load Q&A prompt template."

        # Get domain configuration
        domain_config = get_domain_config(subject_domain)

        # Format the prompt
        formatted_prompt = _format_prompt_template(template,
                                                   subject_domain=subject_domain,
                                                   subject_domain_upper=subject_domain.upper().replace('_', ' '),
                                                   context=context,
                                                   question=question,
                                                   domain_response_guidelines=domain_config.get("qa_guidelines",
                                                                                                "Provide clear, helpful answers")
                                                   )

        response = flash_model.generate_content(formatted_prompt)
        return response.text

    except Exception as e:
        return f"Error: Could not get an answer from the AI. Reason: {e}"


def generate_quiz_from_summary(summary: str, subject_domain: str = "general", difficulty_level: str = "intermediate") -> \
Optional[dict]:
    """Generate domain-appropriate quiz using modular prompt template."""
    if not _is_api_configured():
        return {"error": "Cannot generate quiz. Gemini API key is not configured or models unavailable."}

    try:
        # Load quiz prompt template
        template = _load_prompt_template('adaptive_quiz.txt')
        if not template:
            return {"error": "Could not load quiz generation prompt template."}

        # Get domain configuration
        domain_config = get_domain_config(subject_domain)

        # Format the prompt
        formatted_prompt = _format_prompt_template(template,
                                                   subject_domain=subject_domain,
                                                   subject_domain_upper=subject_domain.upper().replace('_', ' '),
                                                   difficulty_level=difficulty_level,
                                                   content_summary=summary,
                                                   domain_quiz_requirements=domain_config.get("quiz_requirements",
                                                                                              "Create comprehensive questions")
                                                   )

        response = flash_model.generate_content(formatted_prompt)
        cleaned_json = _clean_json_response(response.text)
        return json.loads(cleaned_json)

    except Exception as e:
        return {"error": f"Failed to generate quiz. Reason: {e}"}


def generate_interactive_visualization(description: str, data_context: str, subject_domain: str = "general") -> \
Optional[dict]:
    """Generate appropriate visualizations using modular prompt template."""
    if not _is_api_configured():
        return {"error": "Cannot generate visualization. Gemini API key is not configured or models unavailable."}

    try:
        # Load visualization prompt template
        template = _load_prompt_template('visualization_generation.txt')
        if not template:
            return {"error": "Could not load visualization generation prompt template."}

        # Get domain configuration
        domain_config = get_domain_config(subject_domain)

        # Format the prompt
        formatted_prompt = _format_prompt_template(template,
                                                   subject_domain=subject_domain,
                                                   description=description,
                                                   data_context=data_context,
                                                   domain_visualization_guidelines=domain_config.get(
                                                       "visualization_guidelines",
                                                       "Create clear, informative visualizations"),
                                                   visualization_type_recommendations=f"For {subject_domain}: {', '.join(domain_config.get('visualization_types', ['charts']))}"
                                                   )

        response = flash_model.generate_content(formatted_prompt)
        cleaned_json = _clean_json_response(response.text)
        return json.loads(cleaned_json)

    except Exception as e:
        return {"error": f"Failed to generate visualization. Reason: {e}"}


def simplify_concept(concept_text: str, difficulty_level: str = "beginner", subject_domain: str = "general",
                     learning_style: str = "mixed") -> str:
    """Simplify concepts using modular prompt template."""
    if not _is_api_configured():
        return "Error: Cannot simplify concept. Gemini API key is not configured or models unavailable."

    try:
        # Load simplification prompt template
        template = _load_prompt_template('concept_simplification.txt')
        if not template:
            return "Error: Could not load concept simplification prompt template."

        # Get domain configuration
        domain_config = get_domain_config(subject_domain)

        # Format the prompt
        formatted_prompt = _format_prompt_template(template,
                                                   subject_domain=subject_domain,
                                                   subject_domain_upper=subject_domain.upper().replace('_', ' '),
                                                   difficulty_level=difficulty_level,
                                                   learning_style=learning_style,
                                                   concept_text=concept_text,
                                                   domain_simplification_guidelines=domain_config.get(
                                                       "simplification_guidelines",
                                                       "Use clear, simple language with examples"),
                                                   difficulty_adaptations=DIFFICULTY_ADAPTATIONS.get(difficulty_level,
                                                                                                     "Adapt appropriately for level"),
                                                   learning_style_adaptations=LEARNING_STYLE_ADAPTATIONS.get(
                                                       learning_style, "Balance theory and practice")
                                                   )

        response = flash_model.generate_content(formatted_prompt)
        return response.text

    except Exception as e:
        return f"Error: Could not simplify concept. Reason: {e}"


def _get_generic_subject_profile() -> Dict[str, Any]:
    """Fallback generic subject profile."""
    return {
        "subject_domain": "general",
        "learning_style": "mixed",
        "complexity_level": "intermediate",
        "key_characteristics": ["conceptual understanding", "practical application"],
        "content_types": ["concepts", "examples", "case_studies"],
        "career_applications": ["professional development"],
        "visualization_types": ["charts", "diagrams"],
        "assessment_methods": ["multiple_choice", "case_analysis"],
        "real_world_connections": ["industry applications"],
        "difficulty_factors": ["abstract concepts", "complex relationships"]
    }


# =========================================================================
# --- Prompt Management Functions ---
# =========================================================================

def list_available_prompts() -> list:
    """List all available prompt templates."""
    if not PROMPTS_DIR.exists():
        return []

    return [f.name for f in PROMPTS_DIR.glob('*.txt')]


def validate_prompt_template(prompt_name: str) -> dict:
    """Validate a prompt template for required parameters."""
    template = _load_prompt_template(prompt_name)
    if not template:
        return {"valid": False, "error": f"Template {prompt_name} not found"}

    # Extract template parameters
    import re
    parameters = re.findall(r'{(\w+)}', template)
    unique_params = list(set(parameters))

    return {
        "valid": True,
        "parameters": unique_params,
        "parameter_count": len(unique_params),
        "total_placeholders": len(parameters)
    }


def create_custom_prompt_template(prompt_name: str, template_content: str) -> bool:
    """Create a new custom prompt template."""
    try:
        os.makedirs(PROMPTS_DIR, exist_ok=True)
        with open(PROMPTS_DIR / prompt_name, 'w', encoding='utf-8') as f:
            f.write(template_content)
        return True
    except Exception as e:
        print(f"Error creating prompt template: {e}")
        return False


def update_prompt_template(prompt_name: str, template_content: str) -> bool:
    """Update an existing prompt template."""
    template_path = PROMPTS_DIR / prompt_name
    if not template_path.exists():
        print(f"Template {prompt_name} does not exist. Use create_custom_prompt_template instead.")
        return False

    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        return True
    except Exception as e:
        print(f"Error updating prompt template: {e}")
        return False


def get_prompt_template_preview(prompt_name: str, sample_params: dict = None) -> str:
    """Get a preview of how a prompt template would look with sample parameters."""
    template = _load_prompt_template(prompt_name)
    if not template:
        return f"Template {prompt_name} not found"

    if sample_params:
        try:
            return _format_prompt_template(template, **sample_params)
        except KeyError as e:
            return f"Missing parameter for preview: {e}"

    return template


# =========================================================================
# --- Domain Configuration Management ---
# =========================================================================

def get_supported_domains() -> list:
    """Get list of all supported subject domains."""
    from domain_configurations import DOMAIN_CONFIGURATIONS
    return list(DOMAIN_CONFIGURATIONS.keys())


def add_custom_domain_config(domain_name: str, config: dict) -> bool:
    """Add a custom domain configuration (runtime only)."""
    try:
        from domain_configurations import DOMAIN_CONFIGURATIONS
        DOMAIN_CONFIGURATIONS[domain_name] = config
        return True
    except Exception as e:
        print(f"Error adding custom domain config: {e}")
        return False


def get_domain_info(domain_name: str) -> dict:
    """Get detailed information about a domain configuration."""
    domain_config = get_domain_config(domain_name)
    validation_info = {
        "domain_exists": domain_name in get_supported_domains(),
        "display_name": domain_config.get("display_name", "Unknown"),
        "learning_characteristics": domain_config.get("learning_characteristics", []),
        "content_types": domain_config.get("content_types", []),
        "career_applications": domain_config.get("career_applications", []),
        "has_custom_instructions": bool(domain_config.get("extraction_instructions")),
        "has_qa_guidelines": bool(domain_config.get("qa_guidelines")),
        "has_quiz_requirements": bool(domain_config.get("quiz_requirements")),
        "has_visualization_guidelines": bool(domain_config.get("visualization_guidelines"))
    }

    return {**domain_config, **validation_info}


# =========================================================================
# --- Web Intelligence Integration ---
# =========================================================================

def gather_web_course_intelligence(course_name: str, university: str = "", course_code: str = "") -> dict:
    """
    Gather course intelligence from web sources to enhance PDF processing context.
    This provides the AI with comprehensive course understanding before processing any PDFs.

    Args:
        course_name: Name of the course (e.g., "Advanced Microeconomics")
        university: University name (e.g., "Harvard University")
        course_code: Course code if available (e.g., "ECON 2010")

    Returns:
        Dict with comprehensive course intelligence including:
        - Course description and objectives
        - Typical textbook sequences
        - Prerequisites and follow-up courses
        - Career applications and industry relevance
        - Academic standards and expectations
    """
    if not _is_api_configured():
        return {"error": "Cannot gather course intelligence. Gemini API key not configured."}

    try:
        # Create a comprehensive course research prompt
        intelligence_prompt = f"""
        Research and provide comprehensive intelligence about this academic course:

        Course: {course_name}
        University: {university or "General academic standards"}
        Course Code: {course_code or "Not specified"}

        Based on your knowledge of academic curricula, provide detailed course intelligence:

        {{
            "course_overview": {{
                "official_description": "Comprehensive description of what this course covers",
                "learning_objectives": ["Primary learning goal 1", "Primary learning goal 2", "etc."],
                "academic_level": "undergraduate|masters|phd|professional",
                "typical_duration": "semester length and time commitment",
                "difficulty_rating": "1-10 scale with explanation"
            }},

            "curriculum_structure": {{
                "typical_textbooks": ["Primary textbook authors/titles", "Secondary references"],
                "chapter_sequence": ["Typical chapter progression", "Topic ordering"],
                "prerequisites": ["Required background knowledge", "Prerequisite courses"],
                "follow_up_courses": ["Natural next courses", "Advanced topics"]
            }},

            "subject_domain_analysis": {{
                "primary_domain": "economics|computer_science|mathematics|etc.",
                "subdisciplines": ["Specific areas within the domain"],
                "methodological_approach": "theoretical|practical|mixed",
                "mathematical_intensity": "low|medium|high",
                "memorization_vs_analysis": "ratio and explanation"
            }},

            "career_applications": {{
                "primary_career_paths": ["Most common career destinations"],
                "industry_applications": ["How concepts are used professionally"],
                "salary_impact": "How this knowledge affects earning potential",
                "skill_development": ["Professional skills gained"],
                "certification_relevance": ["Professional certifications this supports"]
            }},

            "academic_context": {{
                "university_approach": "How {university or 'top universities'} typically teach this",
                "research_connections": ["How this connects to current research"],
                "interdisciplinary_links": ["Connections to other fields"],
                "global_variations": ["How this course varies internationally"],
                "current_trends": ["Recent developments in the field"]
            }},

            "learning_optimization": {{
                "effective_study_methods": ["Best approaches for mastering this subject"],
                "common_difficulties": ["Where students typically struggle"],
                "success_strategies": ["What leads to high performance"],
                "resource_recommendations": ["Additional learning resources"],
                "assessment_approaches": ["Typical exam and project formats"]
            }}
        }}

        Provide specific, actionable intelligence that would help an AI tutor create the most effective learning experience for students in this course.
        Return only valid JSON without markdown formatting.
        """

        response = flash_model.generate_content(intelligence_prompt)
        cleaned_json = _clean_json_response(response.text)
        course_intelligence = json.loads(cleaned_json)

        # Enhance with domain-specific configurations
        detected_domain = course_intelligence.get("subject_domain_analysis", {}).get("primary_domain", "general")
        domain_config = get_domain_config(detected_domain)

        course_intelligence["domain_configuration"] = domain_config
        course_intelligence["intelligence_source"] = "ai_research"
        course_intelligence["generated_at"] = datetime.now().isoformat()

        return course_intelligence

    except Exception as e:
        return {"error": f"Failed to gather course intelligence. Reason: {e}"}


def enhance_course_with_web_intelligence(course_name: str, university: str, student_input: dict) -> dict:
    """
    Combine student input with AI-researched course intelligence to create
    comprehensive course context for PDF processing.

    Args:
        course_name: Course name from student
        university: University name from student
        student_input: Student-provided course details and goals

    Returns:
        Enhanced course context combining student input with web intelligence
    """

    # Gather AI-based course intelligence
    web_intelligence = gather_web_course_intelligence(course_name, university,
                                                      student_input.get("course_code", ""))

    if "error" in web_intelligence:
        # Fallback to basic course context if web intelligence fails
        web_intelligence = _create_fallback_course_context(course_name, university)

    # Combine student input with web intelligence
    enhanced_context = {
        "student_provided": student_input,
        "web_intelligence": web_intelligence,
        "synthesis": _synthesize_course_context(student_input, web_intelligence)
    }

    return enhanced_context


def _create_fallback_course_context(course_name: str, university: str) -> dict:
    """Create basic course context when web intelligence fails."""

    # Basic domain detection from course name
    domain_keywords = {
        "economics": ["economics", "econometrics", "macro", "micro", "finance"],
        "computer_science": ["computer", "programming", "algorithms", "data", "software"],
        "mathematics": ["mathematics", "calculus", "algebra", "statistics", "math"],
        "psychology": ["psychology", "behavioral", "cognitive", "social"],
        "business": ["business", "management", "marketing", "strategy", "mba"],
        "engineering": ["engineering", "mechanical", "electrical", "civil"],
        "medicine": ["medicine", "medical", "anatomy", "physiology", "clinical"]
    }

    detected_domain = "general"
    course_lower = course_name.lower()

    for domain, keywords in domain_keywords.items():
        if any(keyword in course_lower for keyword in keywords):
            detected_domain = domain
            break

    domain_config = get_domain_config(detected_domain)

    return {
        "course_overview": {
            "official_description": f"Academic course in {course_name}",
            "learning_objectives": domain_config.get("career_applications", ["Professional development"]),
            "academic_level": "masters",
            "difficulty_rating": "7 - Graduate level course"
        },
        "subject_domain_analysis": {
            "primary_domain": detected_domain,
            "methodological_approach": domain_config.get("learning_style", "mixed")
        },
        "career_applications": {
            "primary_career_paths": domain_config.get("career_applications", []),
            "industry_applications": domain_config.get("career_applications", [])
        },
        "fallback": True
    }


def _synthesize_course_context(student_input: dict, web_intelligence: dict) -> dict:
    """
    Synthesize student input with web intelligence to create optimal course context.
    """

    synthesis = {
        "course_name": student_input.get("course_name", ""),
        "university": student_input.get("university", ""),
        "academic_level": student_input.get("academic_level",
                                            web_intelligence.get("course_overview", {}).get("academic_level",
                                                                                            "masters")),

        # Merge learning objectives
        "learning_objectives": list(set(
            student_input.get("learning_objectives", []) +
            web_intelligence.get("course_overview", {}).get("learning_objectives", [])
        )),

        # Career focus
        "career_focus": student_input.get("career_goals",
                                          web_intelligence.get("career_applications", {}).get("primary_career_paths",
                                                                                              [])),

        # Subject domain
        "subject_domain": web_intelligence.get("subject_domain_analysis", {}).get("primary_domain", "general"),

        # Prerequisites and context
        "prerequisites": web_intelligence.get("curriculum_structure", {}).get("prerequisites", []),
        "follow_up_courses": web_intelligence.get("curriculum_structure", {}).get("follow_up_courses", []),

        # Learning approach
        "methodological_approach": web_intelligence.get("subject_domain_analysis", {}).get("methodological_approach",
                                                                                           "mixed"),
        "difficulty_level": web_intelligence.get("course_overview", {}).get("difficulty_rating", "intermediate")
    }

    return synthesis


# =========================================================================
# --- Enhanced PDF Processing with Course Intelligence ---
# =========================================================================

def process_pdf_with_course_intelligence(file_path: str, subject_name: str, enhanced_course_context: dict) -> dict:
    """
    Enhanced PDF processing that uses comprehensive course intelligence
    to create contextually aware, curriculum-integrated content.

    Args:
        file_path: Path to PDF file
        subject_name: Name of the subject/book
        enhanced_course_context: Result from enhance_course_with_web_intelligence()

    Returns:
        Processed content with full course context integration
    """
    if not _is_api_configured():
        return {"error": "Cannot process PDF. Gemini API key is not configured or models unavailable."}

    try:
        # Extract course intelligence
        course_synthesis = enhanced_course_context.get("synthesis", {})
        web_intelligence = enhanced_course_context.get("web_intelligence", {})
        student_input = enhanced_course_context.get("student_provided", {})

        # Upload the file
        uploaded_file = genai.upload_file(path=file_path, display_name=subject_name)

        # Load and format the extraction prompt template with full context
        template = _load_prompt_template('adaptive_pdf_extraction.txt')
        if not template:
            return {"error": "Could not load PDF extraction prompt template"}

        # Get domain configuration
        subject_domain = course_synthesis.get("subject_domain", "general")
        domain_config = get_domain_config(subject_domain)

        # Build comprehensive course context for the prompt
        course_context_prompt = _build_course_context_prompt(enhanced_course_context)

        # Prepare template parameters with enhanced context
        prompt_params = {
            'subject_name': subject_name,
            'subject_domain': subject_domain,
            'subject_domain_upper': subject_domain.upper().replace('_', ' '),
            'course_description': course_synthesis.get("course_name", "") + " - " +
                                  str(web_intelligence.get("course_overview", {}).get("official_description", "")),
            'learning_style': course_synthesis.get("methodological_approach", "mixed"),
            'complexity_level': course_synthesis.get("academic_level", "intermediate"),
            'content_types': ', '.join(domain_config.get("content_types", ["concepts", "examples"])),
            'career_applications': ', '.join(course_synthesis.get("career_focus", [])),
            'visualization_types': ', '.join(domain_config.get("visualization_types", ["charts"])),
            'existing_books_context': course_context_prompt,
            'domain_specific_instructions': domain_config.get("extraction_instructions", "Focus on clear explanations"),
            'content_block_templates': get_content_block_templates(subject_domain,
                                                                   domain_config.get("content_types", [])),
            'content_block_guidelines': _build_content_guidelines(domain_config, course_synthesis)
        }

        # Format the prompt with comprehensive context
        formatted_prompt = _format_prompt_template(template, **prompt_params)

        response = pro_model.generate_content([formatted_prompt, uploaded_file])

        if not response.parts:
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                return {"error": f"AI response was blocked. Reason: {response.prompt_feedback.block_reason.name}"}
            return {
                "error": "AI returned an empty response. This may be due to a safety block or an issue with the prompt."}

        cleaned_json = _clean_json_response(response.text)
        result = json.loads(cleaned_json)

        # Add enhanced metadata
        result["course_intelligence"] = enhanced_course_context
        result["processing_metadata"] = {
            "subject_domain_detected": subject_domain,
            "course_context_used": True,
            "web_intelligence_available": "web_intelligence" in enhanced_course_context,
            "processing_timestamp": datetime.now().isoformat()
        }

        return result

    except Exception as e:
        return {"error": f"Failed to process PDF with course intelligence. Reason: {type(e).__name__}: {e}"}


def _build_course_context_prompt(enhanced_course_context: dict) -> str:
    """Build detailed course context for AI prompt."""

    synthesis = enhanced_course_context.get("synthesis", {})
    web_intelligence = enhanced_course_context.get("web_intelligence", {})

    context_parts = []

    # Course overview
    if web_intelligence.get("course_overview"):
        overview = web_intelligence["course_overview"]
        context_parts.append(f"""
COURSE OVERVIEW:
- {synthesis.get('course_name', 'Unknown Course')} at {synthesis.get('university', 'Institution')}
- Description: {overview.get('official_description', 'No description available')}
- Academic Level: {synthesis.get('academic_level', 'masters').title()}
- Learning Objectives: {', '.join(synthesis.get('learning_objectives', []))}
""")

    # Curriculum context
    if web_intelligence.get("curriculum_structure"):
        curriculum = web_intelligence["curriculum_structure"]
        context_parts.append(f"""
CURRICULUM CONTEXT:
- Prerequisites: {', '.join(curriculum.get('prerequisites', ['None specified']))}
- Follow-up Courses: {', '.join(curriculum.get('follow_up_courses', ['None specified']))}
- Typical Textbooks: {', '.join(curriculum.get('typical_textbooks', ['Various']))}
""")

    # Career context
    if synthesis.get("career_focus"):
        context_parts.append(f"""
CAREER FOCUS:
- Target Career Paths: {', '.join(synthesis.get('career_focus', []))}
- Industry Applications: Focus on practical applications for these career goals
""")

    # Learning approach
    context_parts.append(f"""
LEARNING APPROACH:
- Methodological Style: {synthesis.get('methodological_approach', 'mixed')}
- Subject Domain: {synthesis.get('subject_domain', 'general')}
- Difficulty Expectation: {synthesis.get('difficulty_level', 'intermediate')}
""")

    return "\n".join(context_parts) if context_parts else "This is the first book in a new course."


def _build_content_guidelines(domain_config: dict, course_synthesis: dict) -> str:
    """Build specific content guidelines based on domain and course context."""

    guidelines = []

    # Domain-specific guidelines
    if domain_config.get("extraction_instructions"):
        guidelines.append(f"DOMAIN GUIDELINES: {domain_config['extraction_instructions']}")

    # Career-focused guidelines
    if course_synthesis.get("career_focus"):
        career_focus = ", ".join(course_synthesis["career_focus"])
        guidelines.append(f"CAREER FOCUS: Emphasize applications relevant to {career_focus}")

    # Academic level guidelines
    academic_level = course_synthesis.get("academic_level", "masters")
    if academic_level == "undergraduate":
        guidelines.append("COMPLEXITY: Use foundational examples, avoid advanced mathematics")
    elif academic_level == "masters":
        guidelines.append("COMPLEXITY: Include sophisticated analysis, professional applications")
    elif academic_level == "phd":
        guidelines.append("COMPLEXITY: Emphasize research applications, theoretical depth")

    return " | ".join(guidelines) if guidelines else "Use appropriate academic standards"


# =========================================================================
# --- Utility Functions ---
# =========================================================================

def test_ai_service_connection() -> dict:
    """Test the AI service connection and return status."""

    if not _is_api_configured():
        return {
            "status": "error",
            "message": "Gemini API key not configured",
            "configured": False
        }

    try:
        # Test basic AI functionality
        test_response = flash_model.generate_content("Respond with 'AI service working' if you can read this.")

        return {
            "status": "success",
            "message": "AI service connected successfully",
            "configured": True,
            "test_response": test_response.text[:50] + "..." if len(test_response.text) > 50 else test_response.text,
            "available_functions": [
                "PDF processing",
                "Question answering",
                "Quiz generation",
                "Concept simplification",
                "Visualization generation",
                "Course intelligence gathering"
            ]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"AI service connection failed: {str(e)}",
            "configured": True,
            "connection_error": True
        }


def get_ai_service_stats() -> dict:
    """Get statistics about AI service usage and capabilities."""

    return {
        "service_info": {
            "configured": _is_api_configured(),
            "supported_domains": len(get_supported_domains()),
            "available_prompts": len(list_available_prompts()),
            "models_available": {
                "pro_model": pro_model is not None,
                "flash_model": flash_model is not None
            }
        },
        "capabilities": {
            "pdf_processing": True,
            "web_intelligence": True,
            "adaptive_content": True,
            "multi_domain": True,
            "course_context": True,
            "interactive_visualizations": True
        },
        "supported_domains": get_supported_domains(),
        "prompt_templates": list_available_prompts()
    }