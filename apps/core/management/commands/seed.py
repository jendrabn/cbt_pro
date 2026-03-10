from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import UserProfile
from apps.notifications.models import SystemSetting
from apps.questions.models import (
    Question,
    QuestionAnswer,
    QuestionBlankAnswer,
    QuestionCategory,
    QuestionMatchingPair,
    QuestionOption,
    QuestionOrderingItem,
    QuestionTag,
    QuestionTagRelation,
)
from apps.subjects.models import Subject

User = get_user_model()

OPTION_LETTERS = [choice.value for choice in QuestionOption.OptionLetter]

ADMIN_ACCOUNT = {
    "username": "admin",
    "email": "admin@mail.com",
    "password": "admin123",
    "first_name": "System",
    "last_name": "Administrator",
    "role": User.Role.ADMIN,
}

TEACHER_ACCOUNTS = [
    {
        "username": "olivia.carter",
        "email": "olivia.carter@mail.com",
        "password": "teacher123",
        "first_name": "Olivia",
        "last_name": "Carter",
        "teacher_id": "TCH-1001",
        "subject_specialization": "Mathematics",
    },
    {
        "username": "michael.reed",
        "email": "michael.reed@mail.com",
        "password": "teacher123",
        "first_name": "Michael",
        "last_name": "Reed",
        "teacher_id": "TCH-1002",
        "subject_specialization": "Science",
    },
    {
        "username": "sophia.bennett",
        "email": "sophia.bennett@mail.com",
        "password": "teacher123",
        "first_name": "Sophia",
        "last_name": "Bennett",
        "teacher_id": "TCH-1003",
        "subject_specialization": "Humanities and Technology",
    },
]

STUDENT_ACCOUNTS = [
    {
        "username": "ethan.walker",
        "email": "ethan.walker@mail.com",
        "password": "student123",
        "first_name": "Ethan",
        "last_name": "Walker",
        "student_id": "STU-2001",
        "class_grade": "11th Grade - A",
    },
    {
        "username": "ava.thompson",
        "email": "ava.thompson@mail.com",
        "password": "student123",
        "first_name": "Ava",
        "last_name": "Thompson",
        "student_id": "STU-2002",
        "class_grade": "11th Grade - B",
    },
    {
        "username": "noah.parker",
        "email": "noah.parker@mail.com",
        "password": "student123",
        "first_name": "Noah",
        "last_name": "Parker",
        "student_id": "STU-2003",
        "class_grade": "12th Grade - A",
    },
]

SUBJECTS = [
    {
        "code": "ALG2",
        "name": "Algebra II",
        "description": "Functions, equations, and polynomial operations for U.S. high school math.",
    },
    {
        "code": "GEOM",
        "name": "Geometry",
        "description": "Core geometry concepts, proofs, and measurement.",
    },
    {
        "code": "BIO",
        "name": "Biology",
        "description": "Cells, genetics, ecosystems, and scientific reasoning.",
    },
    {
        "code": "CHEM",
        "name": "Chemistry",
        "description": "Matter, atoms, reactions, and stoichiometry.",
    },
    {
        "code": "PHYS",
        "name": "Physics",
        "description": "Motion, forces, energy, and waves.",
    },
    {
        "code": "ENG-LIT",
        "name": "English Literature",
        "description": "Reading analysis, literary devices, and theme.",
    },
    {
        "code": "USHIST",
        "name": "U.S. History",
        "description": "Foundations of the United States and major historical events.",
    },
    {
        "code": "CS",
        "name": "Computer Science",
        "description": "Programming fundamentals, algorithms, and digital logic.",
    },
]

QUESTION_BANK = [
    {
        "subject_code": "ALG2",
        "teacher_username": "olivia.carter",
        "category": "Linear Equations",
        "question_text": "Solve for x: 2x + 5 = 17",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "Subtract 5 from both sides to get 2x = 12, then divide by 2.",
        "tags": ["algebra", "linear-equations"],
        "options": [
            {"text": "4", "is_correct": False},
            {"text": "5", "is_correct": False},
            {"text": "6", "is_correct": True},
            {"text": "7", "is_correct": False},
        ],
    },
    {
        "subject_code": "ALG2",
        "teacher_username": "olivia.carter",
        "category": "Quadratic Expressions",
        "question_text": "Which expression is equivalent to x^2 - 5x + 6?",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 5,
        "explanation": "Look for two numbers that multiply to 6 and add to -5.",
        "tags": ["algebra", "factoring", "quadratics"],
        "options": [
            {"text": "(x - 2)(x - 3)", "is_correct": True},
            {"text": "(x + 2)(x + 3)", "is_correct": False},
            {"text": "(x - 1)(x - 6)", "is_correct": False},
            {"text": "(x + 1)(x + 6)", "is_correct": False},
        ],
    },
    {
        "subject_code": "GEOM",
        "teacher_username": "olivia.carter",
        "category": "Angle Relationships",
        "question_text": "What is the sum of the interior angles of any triangle?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "All triangles have interior angles that add up to 180 degrees.",
        "tags": ["geometry", "angles"],
        "options": [
            {"text": "90 degrees", "is_correct": False},
            {"text": "180 degrees", "is_correct": True},
            {"text": "270 degrees", "is_correct": False},
            {"text": "360 degrees", "is_correct": False},
        ],
    },
    {
        "subject_code": "BIO",
        "teacher_username": "michael.reed",
        "category": "Cell Biology",
        "question_text": "Which organelle is known as the powerhouse of the cell?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "Mitochondria produce ATP, which cells use for energy.",
        "tags": ["biology", "cells"],
        "options": [
            {"text": "Nucleus", "is_correct": False},
            {"text": "Mitochondrion", "is_correct": True},
            {"text": "Ribosome", "is_correct": False},
            {"text": "Golgi apparatus", "is_correct": False},
        ],
    },
    {
        "subject_code": "CHEM",
        "teacher_username": "michael.reed",
        "category": "Atomic Structure",
        "question_text": "What is the atomic number of oxygen?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "Atomic number tells you how many protons are in the nucleus. Oxygen has 8.",
        "tags": ["chemistry", "atoms"],
        "options": [
            {"text": "6", "is_correct": False},
            {"text": "7", "is_correct": False},
            {"text": "8", "is_correct": True},
            {"text": "9", "is_correct": False},
        ],
    },
    {
        "subject_code": "PHYS",
        "teacher_username": "michael.reed",
        "category": "Forces and Motion",
        "question_text": "A net force of 20 N acts on a 4 kg object. What is the acceleration?",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 5,
        "explanation": "Use Newton's second law: a = F / m = 20 / 4 = 5.",
        "tags": ["physics", "newton-laws", "motion"],
        "options": [
            {"text": "4 m/s^2", "is_correct": False},
            {"text": "5 m/s^2", "is_correct": True},
            {"text": "8 m/s^2", "is_correct": False},
            {"text": "16 m/s^2", "is_correct": False},
        ],
    },
    {
        "subject_code": "ENG-LIT",
        "teacher_username": "sophia.bennett",
        "category": "Literary Devices",
        "question_text": "What is a metaphor?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "A metaphor compares two unlike things without using 'like' or 'as'.",
        "tags": ["english", "literary-devices"],
        "options": [
            {"text": "A comparison using 'like' or 'as'", "is_correct": False},
            {"text": "A direct comparison without using 'like' or 'as'", "is_correct": True},
            {"text": "An exaggeration used for emphasis", "is_correct": False},
            {"text": "A repeated consonant sound", "is_correct": False},
        ],
    },
    {
        "subject_code": "ENG-LIT",
        "teacher_username": "sophia.bennett",
        "category": "Reading Analysis",
        "question_text": "Which statement best describes the theme of a story?",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 5,
        "explanation": "Theme is the central message or insight a reader can take from the story.",
        "tags": ["english", "theme", "reading-analysis"],
        "options": [
            {"text": "The list of characters in the story", "is_correct": False},
            {"text": "The lesson or central message explored by the story", "is_correct": True},
            {"text": "The place where the story happens", "is_correct": False},
            {"text": "The order of events in the plot", "is_correct": False},
        ],
    },
    {
        "subject_code": "USHIST",
        "teacher_username": "sophia.bennett",
        "category": "Founding Documents",
        "question_text": "What is the name of the first ten amendments to the U.S. Constitution?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "The first ten amendments are collectively called the Bill of Rights.",
        "tags": ["history", "constitution", "government"],
        "options": [
            {"text": "The Federalist Papers", "is_correct": False},
            {"text": "The Articles of Confederation", "is_correct": False},
            {"text": "The Bill of Rights", "is_correct": True},
            {"text": "The Emancipation Proclamation", "is_correct": False},
        ],
    },
    {
        "subject_code": "CS",
        "teacher_username": "sophia.bennett",
        "category": "Programming Fundamentals",
        "question_text": "In Python, what does len([3, 4, 5]) return?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "The len function returns the number of items in a list. This list has 3 items.",
        "tags": ["computer-science", "python", "lists"],
        "options": [
            {"text": "2", "is_correct": False},
            {"text": "3", "is_correct": True},
            {"text": "4", "is_correct": False},
            {"text": "12", "is_correct": False},
        ],
    },
    {
        "subject_code": "ALG2",
        "teacher_username": "olivia.carter",
        "category": "Algebra Review",
        "question_type": Question.QuestionType.CHECKBOX,
        "question_text": "Select all expressions equivalent to 2(x + 3).",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 6,
        "checkbox_scoring": Question.CheckboxScoring.PARTIAL_NO_PENALTY,
        "explanation": "Distribute the 2 to both terms inside the parentheses.",
        "tags": ["algebra", "distribution", "checkbox"],
        "options": [
            {"text": "2x + 6", "is_correct": True},
            {"text": "6 + 2x", "is_correct": True},
            {"text": "2x + 3", "is_correct": False},
            {"text": "x + 6", "is_correct": False},
        ],
    },
    {
        "subject_code": "BIO",
        "teacher_username": "michael.reed",
        "category": "Characteristics of Life",
        "question_type": Question.QuestionType.CHECKBOX,
        "question_text": "Select all characteristics shared by living organisms.",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 6,
        "checkbox_scoring": Question.CheckboxScoring.PARTIAL,
        "explanation": "Living things are made of cells, use energy, grow, and respond to stimuli.",
        "tags": ["biology", "life-science", "checkbox"],
        "options": [
            {"text": "Made of one or more cells", "is_correct": True},
            {"text": "Can maintain internal balance", "is_correct": True},
            {"text": "Always move from place to place", "is_correct": False},
            {"text": "Use energy", "is_correct": True},
        ],
    },
    {
        "subject_code": "CS",
        "teacher_username": "sophia.bennett",
        "category": "Python Basics",
        "question_type": Question.QuestionType.CHECKBOX,
        "question_text": "Which of the following are valid built-in Python collection types?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 6,
        "checkbox_scoring": Question.CheckboxScoring.ALL_OR_NOTHING,
        "explanation": "List, tuple, and dictionary are built-in collection types in Python.",
        "tags": ["computer-science", "python", "checkbox"],
        "options": [
            {"text": "list", "is_correct": True},
            {"text": "tuple", "is_correct": True},
            {"text": "dictionary", "is_correct": True},
            {"text": "spreadsheet", "is_correct": False},
        ],
    },
    {
        "subject_code": "BIO",
        "teacher_username": "michael.reed",
        "category": "Organization in Biology",
        "question_type": Question.QuestionType.ORDERING,
        "question_text": "Order the levels of biological organization from smallest to largest.",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 6,
        "explanation": "Cells form tissues, tissues form organs, and organs form organ systems.",
        "tags": ["biology", "organization", "ordering"],
        "ordering_items": [
            "Cell",
            "Tissue",
            "Organ",
            "Organ system",
        ],
    },
    {
        "subject_code": "USHIST",
        "teacher_username": "sophia.bennett",
        "category": "Civics Process",
        "question_type": Question.QuestionType.ORDERING,
        "question_text": "Order the general steps for how a bill becomes a law in the United States.",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 6,
        "explanation": "A bill is introduced, debated and approved by Congress, then sent to the president.",
        "tags": ["history", "government", "ordering"],
        "ordering_items": [
            "A bill is introduced",
            "The bill is debated and voted on in Congress",
            "Both houses approve the bill",
            "The president signs the bill",
        ],
    },
    {
        "subject_code": "CHEM",
        "teacher_username": "michael.reed",
        "category": "Scientific Method",
        "question_type": Question.QuestionType.ORDERING,
        "question_text": "Order these steps of a basic lab investigation.",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 6,
        "explanation": "A solid investigation starts with a question and ends with analysis.",
        "tags": ["chemistry", "lab", "ordering"],
        "ordering_items": [
            "Ask a question",
            "Form a hypothesis",
            "Test the hypothesis",
            "Analyze the results",
        ],
    },
    {
        "subject_code": "GEOM",
        "teacher_username": "olivia.carter",
        "category": "Geometry Vocabulary",
        "question_type": Question.QuestionType.MATCHING,
        "question_text": "Match each geometry term with its correct definition.",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 8,
        "explanation": "Each term has a standard geometry definition used in proofs and measurement.",
        "tags": ["geometry", "vocabulary", "matching"],
        "matching_pairs": [
            {"prompt_text": "Radius", "answer_text": "A segment from the center of a circle to a point on the circle"},
            {"prompt_text": "Diameter", "answer_text": "A segment passing through the center of a circle with endpoints on the circle"},
            {"prompt_text": "Chord", "answer_text": "A segment with both endpoints on a circle"},
        ],
    },
    {
        "subject_code": "PHYS",
        "teacher_username": "michael.reed",
        "category": "Units and Quantities",
        "question_type": Question.QuestionType.MATCHING,
        "question_text": "Match each physical quantity with its SI unit.",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 8,
        "explanation": "The SI system pairs each base quantity with a standard unit.",
        "tags": ["physics", "units", "matching"],
        "matching_pairs": [
            {"prompt_text": "Length", "answer_text": "meter"},
            {"prompt_text": "Mass", "answer_text": "kilogram"},
            {"prompt_text": "Time", "answer_text": "second"},
        ],
    },
    {
        "subject_code": "ENG-LIT",
        "teacher_username": "sophia.bennett",
        "category": "Literary Devices",
        "question_type": Question.QuestionType.MATCHING,
        "question_text": "Match each literary device with the best description.",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 8,
        "explanation": "Literary devices help authors create style, tone, and meaning.",
        "tags": ["english", "literary-devices", "matching"],
        "matching_pairs": [
            {"prompt_text": "Simile", "answer_text": "A comparison using like or as"},
            {"prompt_text": "Hyperbole", "answer_text": "An intentional exaggeration for emphasis"},
            {"prompt_text": "Alliteration", "answer_text": "The repetition of initial consonant sounds"},
        ],
    },
    {
        "subject_code": "CHEM",
        "teacher_username": "michael.reed",
        "category": "Chemical Basics",
        "question_type": Question.QuestionType.FILL_IN_BLANK,
        "question_text": "The chemical formula for water is {{1}}, and its freezing point in Celsius is {{2}}.",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 8,
        "explanation": "Water is written as H2O and freezes at 0°C under standard conditions.",
        "tags": ["chemistry", "compounds", "fill-in-blank"],
        "blank_answers": [
            {"blank_number": 1, "accepted_answers": ["H2O", "h2o"], "blank_points": 4},
            {"blank_number": 2, "accepted_answers": ["0", "zero"], "blank_points": 4},
        ],
    },
    {
        "subject_code": "USHIST",
        "teacher_username": "sophia.bennett",
        "category": "Founding Era",
        "question_type": Question.QuestionType.FILL_IN_BLANK,
        "question_text": "The Declaration of Independence was adopted in {{1}}.",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "The Continental Congress adopted the Declaration in 1776.",
        "tags": ["history", "founding-documents", "fill-in-blank"],
        "blank_answers": [
            {"blank_number": 1, "accepted_answers": ["1776"], "blank_points": 5},
        ],
    },
    {
        "subject_code": "CS",
        "teacher_username": "sophia.bennett",
        "category": "Programming Fundamentals",
        "question_type": Question.QuestionType.FILL_IN_BLANK,
        "question_text": "In Python, a loop that continues while a condition is true is called a {{1}} loop.",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "A while loop repeats as long as its condition evaluates to true.",
        "tags": ["computer-science", "python", "fill-in-blank"],
        "blank_answers": [
            {"blank_number": 1, "accepted_answers": ["while"], "blank_points": 5, "is_case_sensitive": False},
        ],
    },
    {
        "subject_code": "ENG-LIT",
        "teacher_username": "sophia.bennett",
        "category": "Essay Writing",
        "question_type": Question.QuestionType.ESSAY,
        "question_text": "Explain how setting can influence the mood of a story. Use one example in your response.",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 10,
        "explanation": "Strong responses connect details about place and time to the reader's emotional experience.",
        "tags": ["english", "essay", "analysis"],
        "answer_text": "A strong answer explains that setting shapes mood through details about time, place, weather, and atmosphere, then supports the claim with an example.",
        "max_word_count": 180,
    },
    {
        "subject_code": "BIO",
        "teacher_username": "michael.reed",
        "category": "Cell Processes",
        "question_type": Question.QuestionType.ESSAY,
        "question_text": "Describe the process of photosynthesis and explain why it is important to ecosystems.",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 10,
        "explanation": "Seed answer highlights light energy, glucose production, oxygen release, and food webs.",
        "tags": ["biology", "essay", "photosynthesis"],
        "answer_text": "Photosynthesis uses light energy, water, and carbon dioxide to produce glucose and oxygen, providing energy for plants and supporting ecosystems through food chains and oxygen production.",
        "max_word_count": 200,
    },
    {
        "subject_code": "USHIST",
        "teacher_username": "sophia.bennett",
        "category": "American Revolution",
        "question_type": Question.QuestionType.ESSAY,
        "question_text": "Explain one major cause of the American Revolution and how it increased tension between Britain and the colonies.",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 10,
        "explanation": "Responses may discuss taxation, representation, trade restrictions, or military presence.",
        "tags": ["history", "essay", "american-revolution"],
        "answer_text": "A strong answer identifies one major cause such as taxation without representation and explains how colonists viewed British policies as unfair and controlling.",
        "max_word_count": 180,
    },
    {
        "subject_code": "ALG2",
        "teacher_username": "olivia.carter",
        "category": "Slope",
        "question_type": Question.QuestionType.SHORT_ANSWER,
        "question_text": "What is the slope of the line y = 3x + 1?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 4,
        "explanation": "In slope-intercept form y = mx + b, the slope is the coefficient of x.",
        "tags": ["algebra", "short-answer", "slope"],
        "answer_text": "3",
        "keywords": ["3"],
        "is_case_sensitive": False,
        "max_word_count": 2,
    },
    {
        "subject_code": "CHEM",
        "teacher_username": "michael.reed",
        "category": "Atomic Structure",
        "question_type": Question.QuestionType.SHORT_ANSWER,
        "question_text": "Which subatomic particle has a negative charge?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 4,
        "explanation": "Electrons carry a negative charge.",
        "tags": ["chemistry", "short-answer", "atoms"],
        "answer_text": "electron",
        "keywords": ["electron"],
        "is_case_sensitive": False,
        "max_word_count": 3,
    },
    {
        "subject_code": "CS",
        "teacher_username": "sophia.bennett",
        "category": "Python Basics",
        "question_type": Question.QuestionType.SHORT_ANSWER,
        "question_text": "What keyword is used to define a function in Python?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 4,
        "explanation": "Python functions begin with the def keyword.",
        "tags": ["computer-science", "python", "short-answer"],
        "answer_text": "def",
        "keywords": ["def"],
        "is_case_sensitive": False,
        "max_word_count": 2,
    },
]

SYSTEM_SETTINGS = [
    {
        "setting_key": "institution_name",
        "setting_value": "Riverside High School",
        "setting_type": "string",
        "category": "branding",
        "description": "Nama sekolah/lembaga",
        "is_public": True,
    },
    {
        "setting_key": "institution_type",
        "setting_value": "High School",
        "setting_type": "string",
        "category": "branding",
        "description": "Jenis lembaga (SMA/SMK/MA/Universitas)",
        "is_public": True,
    },
    {
        "setting_key": "institution_address",
        "setting_value": "1250 Lincoln Ave, Portland, OR 97205",
        "setting_type": "string",
        "category": "branding",
        "description": "Alamat lembaga",
        "is_public": False,
    },
    {
        "setting_key": "institution_phone",
        "setting_value": "+1 503-555-0117",
        "setting_type": "string",
        "category": "branding",
        "description": "Nomor telepon/WA lembaga",
        "is_public": False,
    },
    {
        "setting_key": "institution_email",
        "setting_value": "hello@riversidehigh.edu",
        "setting_type": "string",
        "category": "branding",
        "description": "Email resmi lembaga",
        "is_public": False,
    },
    {
        "setting_key": "institution_website",
        "setting_value": "https://www.riversidehigh.edu",
        "setting_type": "string",
        "category": "branding",
        "description": "Website resmi lembaga",
        "is_public": True,
    },
    {
        "setting_key": "institution_logo_url",
        "setting_value": "",
        "setting_type": "string",
        "category": "branding",
        "description": "Path logo utama",
        "is_public": True,
    },
    {
        "setting_key": "institution_logo_dark_url",
        "setting_value": "",
        "setting_type": "string",
        "category": "branding",
        "description": "Path logo dark",
        "is_public": True,
    },
    {
        "setting_key": "institution_favicon_url",
        "setting_value": "",
        "setting_type": "string",
        "category": "branding",
        "description": "Path favicon",
        "is_public": True,
    },
    {
        "setting_key": "login_page_headline",
        "setting_value": "Welcome Back",
        "setting_type": "string",
        "category": "branding",
        "description": "Headline login page",
        "is_public": True,
    },
    {
        "setting_key": "login_page_subheadline",
        "setting_value": "Sign in to manage exams, question banks, and student sessions.",
        "setting_type": "string",
        "category": "branding",
        "description": "Subheadline login page",
        "is_public": True,
    },
    {
        "setting_key": "login_page_background_url",
        "setting_value": "",
        "setting_type": "string",
        "category": "branding",
        "description": "Path background login",
        "is_public": True,
    },
    {
        "setting_key": "primary_color",
        "setting_value": "#0d6efd",
        "setting_type": "string",
        "category": "branding",
        "description": "Warna utama UI",
        "is_public": True,
    },
    {
        "setting_key": "landing_page_enabled",
        "setting_value": "true",
        "setting_type": "boolean",
        "category": "general",
        "description": "Aktifkan landing page di URL root",
        "is_public": True,
    },
    {
        "setting_key": "default_exam_duration",
        "setting_value": "120",
        "setting_type": "number",
        "category": "exam_defaults",
        "description": "Default exam duration in minutes",
        "is_public": False,
    },
    {
        "setting_key": "default_passing_score",
        "setting_value": "60",
        "setting_type": "number",
        "category": "exam_defaults",
        "description": "Default passing score percentage",
        "is_public": False,
    },
    {
        "setting_key": "max_login_attempts",
        "setting_value": "5",
        "setting_type": "number",
        "category": "security",
        "description": "Maximum login attempts before lockout",
        "is_public": False,
    },
    {
        "setting_key": "session_timeout_minutes",
        "setting_value": "120",
        "setting_type": "number",
        "category": "security",
        "description": "User session timeout in minutes",
        "is_public": False,
    },
    {
        "setting_key": "certificates_enabled",
        "setting_value": "true",
        "setting_type": "boolean",
        "category": "certificates",
        "description": "Master switch fitur sertifikat",
        "is_public": False,
    },
    {
        "setting_key": "certificate_number_prefix",
        "setting_value": "CERT",
        "setting_type": "string",
        "category": "certificates",
        "description": "Prefix nomor sertifikat",
        "is_public": False,
    },
    {
        "setting_key": "certificate_pdf_dpi",
        "setting_value": "150",
        "setting_type": "number",
        "category": "certificates",
        "description": "Resolusi render PDF sertifikat",
        "is_public": False,
    },
    {
        "setting_key": "certificate_storage_path",
        "setting_value": "certificates/",
        "setting_type": "string",
        "category": "certificates",
        "description": "Direktori penyimpanan sertifikat",
        "is_public": False,
    },
    {
        "setting_key": "certificate_email_enabled",
        "setting_value": "false",
        "setting_type": "boolean",
        "category": "certificates",
        "description": "Kirim email saat sertifikat siap",
        "is_public": False,
    },
    {
        "setting_key": "certificate_verify_public",
        "setting_value": "true",
        "setting_type": "boolean",
        "category": "certificates",
        "description": "Verifikasi sertifikat publik",
        "is_public": True,
    },
]


class Command(BaseCommand):
    help = "Seed demo data with sample users, U.S. high school subjects, and example questions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting database seeding..."))

        self.create_admin_user()
        teachers = self.create_teacher_users()
        self.create_student_users()
        subjects = self.create_subjects()
        self.create_question_bank(teachers, subjects)
        self.create_system_settings()

        self.stdout.write(self.style.SUCCESS("Database seeding completed."))

    def _upsert_user(self, account_data, role, is_superuser=False):
        defaults = {
            "email": account_data["email"],
            "first_name": account_data["first_name"],
            "last_name": account_data["last_name"],
            "role": role,
            "is_active": True,
            "is_deleted": False,
        }
        if is_superuser:
            defaults["is_staff"] = True
            defaults["is_superuser"] = True
        else:
            defaults["is_staff"] = False
            defaults["is_superuser"] = False

        user, created = User.objects.get_or_create(
            username=account_data["username"],
            defaults=defaults,
        )

        changed_fields = []
        for field, value in defaults.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)

        if created or not user.check_password(account_data["password"]):
            user.set_password(account_data["password"])
            changed_fields.append("password")

        if changed_fields:
            user.save()

        action = "Created" if created else "Updated" if changed_fields else "Unchanged"
        self.stdout.write(self.style.SUCCESS(f"{action} {role} user: {user.username}"))
        return user

    def create_admin_user(self):
        self._upsert_user(ADMIN_ACCOUNT, User.Role.ADMIN, is_superuser=True)

    def create_teacher_users(self):
        teachers = {}
        for teacher_data in TEACHER_ACCOUNTS:
            user = self._upsert_user(teacher_data, User.Role.TEACHER)
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "teacher_id": teacher_data["teacher_id"],
                    "subject_specialization": teacher_data["subject_specialization"],
                },
            )
            teachers[user.username] = user
        return teachers

    def create_student_users(self):
        students = {}
        for student_data in STUDENT_ACCOUNTS:
            user = self._upsert_user(student_data, User.Role.STUDENT)
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "student_id": student_data["student_id"],
                    "class_grade": student_data["class_grade"],
                },
            )
            students[user.username] = user
        return students

    def create_subjects(self):
        subject_map = {}
        for subject_data in SUBJECTS:
            subject = Subject.objects.filter(code=subject_data["code"]).first()
            if subject is None:
                subject = Subject.objects.filter(name=subject_data["name"]).first()

            created = subject is None
            if created:
                subject = Subject.objects.create(
                    code=subject_data["code"],
                    name=subject_data["name"],
                    description=subject_data["description"],
                    is_active=True,
                )
            else:
                changed = False
                for field, value in {
                    "code": subject_data["code"],
                    "name": subject_data["name"],
                    "description": subject_data["description"],
                    "is_active": True,
                }.items():
                    if getattr(subject, field) != value:
                        setattr(subject, field, value)
                        changed = True
                if changed:
                    subject.save()

            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} subject: {subject.name}"))
            subject_map[subject_data["code"]] = subject
        return subject_map

    def _get_or_create_category(self, name):
        category, created = QuestionCategory.objects.get_or_create(
            name=name,
            parent=None,
            defaults={
                "description": f"Sample category for {name}.",
                "is_active": True,
            },
        )
        if not created and not category.is_active:
            category.is_active = True
            category.save(update_fields=["is_active", "updated_at"])
        return category

    def _sync_question_options(self, question, options_data):
        if len(options_data) > len(OPTION_LETTERS):
            raise ValueError(f"Question '{question.question_text[:40]}' has too many options.")

        if question.question_type not in {
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.CHECKBOX,
        }:
            QuestionOption.objects.filter(question=question).delete()
            return

        QuestionOption.objects.filter(question=question).delete()
        options = []
        for index, option_data in enumerate(options_data):
            options.append(
                QuestionOption(
                    question=question,
                    option_letter=OPTION_LETTERS[index],
                    option_text=option_data["text"],
                    option_image_url=option_data.get("image_url", ""),
                    is_correct=option_data["is_correct"],
                    display_order=index + 1,
                )
            )
        QuestionOption.objects.bulk_create(options)

    def _sync_question_answer(self, question, question_data):
        if question.question_type in {
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.CHECKBOX,
            Question.QuestionType.ORDERING,
            Question.QuestionType.MATCHING,
            Question.QuestionType.FILL_IN_BLANK,
        }:
            QuestionAnswer.objects.filter(question=question).delete()
            return

        QuestionAnswer.objects.update_or_create(
            question=question,
            defaults={
                "answer_text": question_data.get("answer_text", ""),
                "keywords": question_data.get("keywords", []),
                "is_case_sensitive": bool(question_data.get("is_case_sensitive", False))
                if question.question_type == Question.QuestionType.SHORT_ANSWER
                else False,
                "max_word_count": question_data.get("max_word_count"),
            },
        )

    def _sync_question_ordering_items(self, question, ordering_items):
        if question.question_type != Question.QuestionType.ORDERING:
            QuestionOrderingItem.objects.filter(question=question).delete()
            return

        QuestionOrderingItem.objects.filter(question=question).delete()
        QuestionOrderingItem.objects.bulk_create(
            [
                QuestionOrderingItem(
                    question=question,
                    item_text=item_text,
                    correct_order=index,
                )
                for index, item_text in enumerate(ordering_items, start=1)
            ]
        )

    def _sync_question_matching_pairs(self, question, matching_pairs):
        if question.question_type != Question.QuestionType.MATCHING:
            QuestionMatchingPair.objects.filter(question=question).delete()
            return

        QuestionMatchingPair.objects.filter(question=question).delete()
        QuestionMatchingPair.objects.bulk_create(
            [
                QuestionMatchingPair(
                    question=question,
                    prompt_text=pair_data["prompt_text"],
                    answer_text=pair_data["answer_text"],
                    pair_order=index,
                )
                for index, pair_data in enumerate(matching_pairs, start=1)
            ]
        )

    def _sync_question_blank_answers(self, question, blank_answers):
        if question.question_type != Question.QuestionType.FILL_IN_BLANK:
            QuestionBlankAnswer.objects.filter(question=question).delete()
            return

        QuestionBlankAnswer.objects.filter(question=question).delete()
        QuestionBlankAnswer.objects.bulk_create(
            [
                QuestionBlankAnswer(
                    question=question,
                    blank_number=int(blank_data["blank_number"]),
                    accepted_answers=list(blank_data.get("accepted_answers") or []),
                    is_case_sensitive=bool(blank_data.get("is_case_sensitive", False)),
                    blank_points=blank_data.get("blank_points"),
                )
                for blank_data in blank_answers
            ]
        )

    def _sync_question_tags(self, question, tag_names):
        QuestionTagRelation.objects.filter(question=question).delete()
        for tag_name in dict.fromkeys(tag_names):
            tag, _ = QuestionTag.objects.get_or_create(name=tag_name)
            QuestionTagRelation.objects.create(question=question, tag=tag)

    def create_question_bank(self, teachers, subjects):
        for question_data in QUESTION_BANK:
            teacher = teachers[question_data["teacher_username"]]
            subject = subjects[question_data["subject_code"]]
            category = self._get_or_create_category(question_data["category"])
            question_type = question_data.get("question_type", Question.QuestionType.MULTIPLE_CHOICE)

            question, created = Question.objects.update_or_create(
                created_by=teacher,
                subject=subject,
                question_text=question_data["question_text"],
                defaults={
                    "category": category,
                    "question_type": question_type,
                    "points": question_data["points"],
                    "difficulty_level": question_data["difficulty_level"],
                    "explanation": question_data["explanation"],
                    "question_image_url": question_data.get("question_image_url", ""),
                    "audio_play_limit": question_data.get("audio_play_limit"),
                    "video_play_limit": question_data.get("video_play_limit"),
                    "checkbox_scoring": question_data.get(
                        "checkbox_scoring",
                        Question.CheckboxScoring.ALL_OR_NOTHING,
                    ),
                    "allow_previous": True,
                    "allow_next": True,
                    "force_sequential": bool(question_data.get("force_sequential", False)),
                    "time_limit_seconds": question_data.get("time_limit_seconds"),
                    "is_active": True,
                    "is_deleted": False,
                },
            )

            self._sync_question_options(question, question_data.get("options", []))
            self._sync_question_ordering_items(question, question_data.get("ordering_items", []))
            self._sync_question_matching_pairs(question, question_data.get("matching_pairs", []))
            self._sync_question_blank_answers(question, question_data.get("blank_answers", []))
            self._sync_question_answer(question, question_data)
            self._sync_question_tags(question, question_data["tags"])

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} sample question: {subject.code} [{question.question_type}] - {question.question_text[:60]}"
                )
            )

    def create_system_settings(self):
        for setting_data in SYSTEM_SETTINGS:
            setting, created = SystemSetting.objects.get_or_create(
                setting_key=setting_data["setting_key"],
                defaults=setting_data,
            )
            action = "Created" if created else "Unchanged"
            self.stdout.write(self.style.SUCCESS(f"{action} setting: {setting.setting_key}"))
