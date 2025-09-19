"""
Domain-specific configurations for adaptive learning system.
This file contains all the domain-specific guidelines, instructions, and templates
that are used to customize the AI prompts for different subject areas.
"""

DOMAIN_CONFIGURATIONS = {
    "economics": {
        "display_name": "Economics",
        "learning_characteristics": ["quantitative analysis", "policy implications", "market dynamics"],
        "content_types": ["concepts", "models", "case studies", "calculations", "charts"],
        "career_applications": ["consulting", "finance", "policy analysis", "business strategy"],
        "visualization_types": ["line charts", "bar charts", "scatter plots", "economic models"],
        "assessment_methods": ["multiple_choice", "case_analysis", "problem_solving", "policy evaluation"],

        "extraction_instructions": """
        - Focus on market applications, policy implications, and business strategy
        - Include quantitative analysis and data interpretation
        - Use current economic events and business cases
        - Emphasize career paths: consulting, finance, policy analysis, business analysis
        - Include interactive economic models and calculations
        - Connect macroeconomic and microeconomic principles
        - Show real-world market examples and company case studies
        """,

        "qa_guidelines": """
        - Provide quantitative examples with real economic data
        - Connect concepts to current market conditions and policy debates
        - Include career applications in consulting, finance, and business
        - Use business case studies and company examples
        - Explain mathematical relationships and economic models
        - Reference current economic research and trends
        """,

        "quiz_requirements": """
        - Include scenario-based questions using real companies and markets
        - Test quantitative reasoning with economic calculations
        - Ask about policy implications and business applications
        - Include questions about economic model interpretation
        - Test understanding of cause-and-effect relationships in markets
        """,

        "simplification_guidelines": """
        - Use business analogies and market examples
        - Break down mathematical models into logical steps
        - Connect abstract concepts to everyday economic decisions
        - Use current events and recognizable company examples
        - Explain the "why" behind economic relationships
        """,

        "visualization_guidelines": """
        - Create interactive supply/demand curves and market models
        - Use professional business color schemes (blues, greens)
        - Include economic indicators and trend analysis charts
        - Show cause-and-effect relationships with flow diagrams
        - Make charts suitable for business presentations
        """
    },

    "computer_science": {
        "display_name": "Computer Science",
        "learning_characteristics": ["hands-on coding", "algorithm thinking", "system design"],
        "content_types": ["concepts", "algorithms", "code examples", "system designs", "case studies"],
        "career_applications": ["software development", "data science", "system architecture", "cybersecurity"],
        "visualization_types": ["flowcharts", "system diagrams", "algorithm visualizations", "network diagrams"],
        "assessment_methods": ["coding problems", "system design", "algorithm analysis", "debugging"],

        "extraction_instructions": """
        - Include code examples and algorithm visualizations
        - Focus on practical implementation and system design
        - Use current technology trends and industry practices
        - Emphasize career paths: software development, data science, system architecture
        - Include interactive coding exercises and technical diagrams
        - Connect theoretical concepts to real-world software systems
        - Show examples from major tech companies and open source projects
        """,

        "qa_guidelines": """
        - Provide code examples in popular programming languages
        - Explain algorithms with step-by-step breakdowns
        - Include system design considerations and trade-offs
        - Reference current technology stacks and industry practices
        - Connect concepts to real software engineering challenges
        - Suggest hands-on projects and coding exercises
        """,

        "quiz_requirements": """
        - Include algorithm analysis and complexity questions
        - Test system design and architecture understanding
        - Ask about debugging and problem-solving approaches
        - Include code reading and interpretation questions
        - Test knowledge of current technologies and frameworks
        """,

        "simplification_guidelines": """
        - Use coding analogies and programming metaphors
        - Break down algorithms into pseudo-code steps
        - Connect abstract concepts to familiar software applications
        - Use examples from popular apps and websites
        - Explain the practical benefits of different approaches
        """,

        "visualization_guidelines": """
        - Create interactive algorithm step-through animations
        - Use technical color schemes suitable for developers
        - Include system architecture and data flow diagrams
        - Show code structure and class relationship diagrams
        - Make visualizations that developers would use professionally
        """
    },

    "mathematics": {
        "display_name": "Mathematics",
        "learning_characteristics": ["logical reasoning", "problem solving", "proof construction"],
        "content_types": ["theorems", "proofs", "problem sets", "geometric interpretations", "applications"],
        "career_applications": ["data analysis", "engineering", "finance", "research", "teaching"],
        "visualization_types": ["graphs", "geometric diagrams", "function plots", "statistical charts"],
        "assessment_methods": ["problem_solving", "proof_writing", "application_problems", "concept_explanation"],

        "extraction_instructions": """
        - Provide step-by-step problem solving approaches
        - Include visual proofs and geometric interpretations
        - Focus on applications in science, engineering, and finance
        - Emphasize logical reasoning and mathematical thinking
        - Include interactive formula calculators and geometric visualizations
        - Connect pure mathematics to practical applications
        - Show historical context and mathematical discoveries
        """,

        "qa_guidelines": """
        - Break down complex problems into manageable steps
        - Provide multiple solution approaches when possible
        - Include geometric or visual interpretations
        - Connect mathematical concepts to real-world applications
        - Explain the intuition behind mathematical relationships
        - Suggest practice problems and further exploration
        """,

        "quiz_requirements": """
        - Include multi-step problem-solving questions
        - Test conceptual understanding, not just computation
        - Ask about applications in various fields
        - Include proof-based and reasoning questions
        - Test ability to connect different mathematical concepts
        """,

        "simplification_guidelines": """
        - Use visual and geometric analogies
        - Break complex proofs into logical building blocks
        - Connect abstract concepts to concrete examples
        - Use real-world applications to motivate concepts
        - Explain the "why" behind mathematical procedures
        """,

        "visualization_guidelines": """
        - Create interactive function plotters and geometric tools
        - Use mathematical color conventions and clear labeling
        - Include step-by-step proof visualizations
        - Show geometric interpretations of algebraic concepts
        - Make tools suitable for mathematical exploration
        """
    },

    "psychology": {
        "display_name": "Psychology",
        "learning_characteristics": ["case study analysis", "research methodology", "behavioral observation"],
        "content_types": ["theories", "case studies", "research findings", "assessments", "applications"],
        "career_applications": ["clinical psychology", "research", "organizational psychology", "counseling"],
        "visualization_types": ["behavioral charts", "research diagrams", "brain maps", "statistical plots"],
        "assessment_methods": ["case_analysis", "research_design", "theory_application", "ethical_scenarios"],

        "extraction_instructions": """
        - Include case studies and behavioral examples
        - Focus on research methodology and data interpretation
        - Use contemporary psychological research and applications
        - Emphasize career paths: clinical, research, organizational psychology
        - Include interactive assessments and behavioral visualizations
        - Connect theories to everyday human behavior
        - Show examples from clinical and applied settings
        """,

        "qa_guidelines": """
        - Provide case study examples and behavioral scenarios
        - Explain research methodology and statistical concepts
        - Include ethical considerations and professional applications
        - Reference current psychological research and findings
        - Connect theories to practical therapeutic and organizational contexts
        - Suggest ways to observe and apply concepts in daily life
        """,

        "quiz_requirements": """
        - Include case study analysis questions
        - Test understanding of research design and methodology
        - Ask about ethical considerations in psychological practice
        - Include questions about theory application to real situations
        - Test knowledge of assessment tools and interventions
        """,

        "simplification_guidelines": """
        - Use relatable human behavior examples
        - Connect theories to everyday psychological experiences
        - Break down research concepts into practical terms
        - Use case studies from diverse populations
        - Explain the practical implications of psychological findings
        """,

        "visualization_guidelines": """
        - Create behavioral pattern charts and assessment tools
        - Use professional clinical color schemes
        - Include research data visualization and statistical charts
        - Show psychological process diagrams and flow charts
        - Make visualizations suitable for clinical and research contexts
        """
    },

    "business": {
        "display_name": "Business",
        "learning_characteristics": ["strategic thinking", "case analysis", "decision making"],
        "content_types": ["case studies", "frameworks", "financial models", "strategy tools", "market analysis"],
        "career_applications": ["management", "consulting", "entrepreneurship", "finance", "marketing"],
        "visualization_types": ["business models", "financial charts", "strategy diagrams", "process flows"],
        "assessment_methods": ["case_analysis", "strategic_planning", "financial_modeling", "presentation"],

        "extraction_instructions": """
        - Include business cases and strategic scenarios
        - Focus on decision-making frameworks and analysis
        - Use current market examples and company studies
        - Emphasize leadership, strategy, and operational excellence
        - Include interactive business models and financial calculators
        - Connect theories to real business challenges and opportunities
        - Show examples from various industries and company sizes
        """,

        "qa_guidelines": """
        - Provide business case examples and strategic scenarios
        - Explain frameworks with practical application steps
        - Include financial analysis and market considerations
        - Reference current business trends and company examples
        - Connect concepts to leadership and management challenges
        - Suggest ways to apply learning in professional settings
        """,

        "quiz_requirements": """
        - Include business case analysis questions
        - Test strategic thinking and decision-making skills
        - Ask about financial analysis and market evaluation
        - Include questions about leadership and management scenarios
        - Test understanding of business frameworks and tools
        """,

        "simplification_guidelines": """
        - Use recognizable company examples and business scenarios
        - Connect frameworks to everyday business decisions
        - Break down complex strategies into actionable steps
        - Use current market events and business news
        - Explain the practical benefits of business tools and concepts
        """,

        "visualization_guidelines": """
        - Create interactive business model canvases and strategy tools
        - Use professional business color schemes and formatting
        - Include financial dashboards and performance metrics
        - Show organizational charts and process flow diagrams
        - Make visualizations suitable for business presentations
        """
    }
}

# Content block templates for different domains
CONTENT_BLOCK_TEMPLATES = {
    "concept_explanation": '''
    {
      "type": "concept_explanation",
      "title": "Concept name",
      "difficulty_level": "beginner|intermediate|advanced",
      "content": "Clear, engaging explanation adapted to domain",
      "key_points": ["main ideas broken down"],
      "examples": ["domain-specific examples"],
      "applications": ["how this concept is used professionally"],
      "common_misconceptions": ["what students often get wrong"],
      "study_tips": ["how to master this concept"]
    }''',

    "interactive_visualization": '''
    {
      "type": "interactive_visualization",
      "title": "Visualization title",
      "visualization_type": "chart|diagram|flowchart|timeline|network",
      "description": "What this visualization shows",
      "purpose": "Why this visualization helps learning",
      "data_structure": "structure of data to visualize",
      "interactive_features": ["features that enhance understanding"],
      "interpretation_guide": "how to read and understand the visualization"
    }''',

    "case_study": '''
    {
      "type": "case_study",
      "title": "Case study title",
      "scenario": "realistic situation from the field",
      "background": "context and setting",
      "key_issues": ["main problems or questions"],
      "analysis_framework": "how to approach this type of case",
      "discussion_questions": ["questions for deeper thinking"],
      "lessons_learned": ["key insights and applications"]
    }''',

    "problem_solving": '''
    {
      "type": "problem_solving",
      "title": "Problem or exercise title",
      "problem_statement": "Clear problem description",
      "solution_approach": "step-by-step solving strategy",
      "worked_example": "detailed solution example",
      "practice_problems": ["similar problems for practice"],
      "common_errors": ["mistakes to avoid"]
    }'''
}

# Difficulty level adaptations
DIFFICULTY_ADAPTATIONS = {
    "beginner": "Focus on basic understanding with lots of examples and simple language",
    "intermediate": "Balance conceptual depth with practical applications and some technical detail",
    "advanced": "Include nuanced explanations, complex scenarios, and professional-level detail"
}

# Learning style adaptations
LEARNING_STYLE_ADAPTATIONS = {
    "theoretical": "Emphasize concepts, principles, and abstract understanding",
    "practical": "Focus on hands-on applications, real-world examples, and actionable skills",
    "mixed": "Balance theoretical understanding with practical applications and examples"
}


def get_domain_config(domain: str) -> dict:
    """Get configuration for a specific domain, with fallback to general."""
    return DOMAIN_CONFIGURATIONS.get(domain, {
        "display_name": domain.replace('_', ' ').title(),
        "learning_characteristics": ["conceptual understanding", "practical application"],
        "content_types": ["concepts", "examples", "case studies"],
        "career_applications": ["professional development"],
        "visualization_types": ["charts", "diagrams"],
        "assessment_methods": ["multiple_choice", "case_analysis"],
        "extraction_instructions": "Focus on clear explanations with practical examples",
        "qa_guidelines": "Provide clear answers with real-world context",
        "quiz_requirements": "Create questions that test both understanding and application",
        "simplification_guidelines": "Use simple language with relevant examples",
        "visualization_guidelines": "Create clear, informative visualizations"
    })


def get_content_block_templates(domain: str, content_types: list) -> str:
    """Generate content block templates based on domain and content types."""
    templates = []

    # Always include concept explanation
    templates.append(CONTENT_BLOCK_TEMPLATES["concept_explanation"])

    # Add visualization if appropriate
    if any(viz_type in content_types for viz_type in ["charts", "diagrams", "visualizations"]):
        templates.append(CONTENT_BLOCK_TEMPLATES["interactive_visualization"])

    # Add case studies for applied domains
    if domain in ["business", "psychology", "medicine", "history", "law"] or "case studies" in content_types:
        templates.append(CONTENT_BLOCK_TEMPLATES["case_study"])

    # Add problem-solving for quantitative domains
    if domain in ["mathematics", "engineering", "economics", "computer_science"] or "calculations" in content_types:
        templates.append(CONTENT_BLOCK_TEMPLATES["problem_solving"])

    return ",\n        ".join(templates)


def format_existing_books_context(existing_books: list) -> str:
    """Format existing books context for prompt inclusion."""
    if not existing_books:
        return "This is the first book in the course."

    context = "EXISTING BOOKS IN THIS COURSE:\n"
    for i, book in enumerate(existing_books, 1):
        context += f"{i}. {book.get('name', 'Unknown')} ({book.get('domain', 'general')}) - {book.get('summary', 'No summary')}\n"
    context += "\nConsider how this new book fits with and complements the existing materials."
    return context