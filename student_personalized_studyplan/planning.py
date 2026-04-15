from typing import Dict, List, Tuple

from .models import StudentProfile


def allocate_weekly_hours(total_hours: int) -> Dict[str, int]:
    weak_hours = round(total_hours * 0.5)
    medium_hours = round(total_hours * 0.3)

    if total_hours >= 3:
        weak_hours = max(1, weak_hours)
        medium_hours = max(1, medium_hours)
    else:
        weak_hours = max(1, weak_hours)
        medium_hours = 0

    strong_hours = total_hours - weak_hours - medium_hours

    if strong_hours < 0:
        reduction = min(medium_hours, abs(strong_hours))
        medium_hours -= reduction
        strong_hours += reduction

    if strong_hours < 0:
        weak_hours = max(1, weak_hours + strong_hours)
        strong_hours = 0

    return {
        "weak_subjects_hours": weak_hours,
        "medium_subjects_hours": medium_hours,
        "strong_subjects_hours": strong_hours,
    }


def performance_band(score: int) -> str:
    if score >= 85:
        return "strong"
    if score >= 70:
        return "stable"
    if score >= 50:
        return "needs improvement"
    return "high priority"


def recommend_focus(subject: str, score: int) -> List[str]:
    normalized = subject.lower()

    subject_map = {
        "math": [
            "Revise one concept at a time, beginning with the topics that cause the most errors, and solve 15 to 20 graded problems daily so confidence builds from basic questions to exam-level ones.",
            "Maintain an error log for formulas, careless mistakes, and time-loss patterns, and review that notebook before every new practice session so the same mistakes are not repeated.",
            "End each week with one mixed problem set under timed conditions to improve speed, question selection, and exam temperament.",
        ],
        "mathematics": [
            "Revise one concept at a time, beginning with the topics that cause the most errors, and solve 15 to 20 graded problems daily so confidence builds from basic questions to exam-level ones.",
            "Maintain an error log for formulas, careless mistakes, and time-loss patterns, and review that notebook before every new practice session so the same mistakes are not repeated.",
            "End each week with one mixed problem set under timed conditions to improve speed, question selection, and exam temperament.",
        ],
        "science": [
            "Break each chapter into concept maps, key definitions, and real-life examples, then explain the topic aloud in simple language to confirm actual understanding instead of recognition-only memory.",
            "Alternate theory review with diagrams, labelled illustrations, and short quiz-based recall sessions so visual memory and conceptual clarity improve together.",
            "Use past-paper style questions after every chapter to connect textbook learning with application-based answers and improve written expression.",
        ],
        "physics": [
            "Separate formulas, definitions, and derivations into different revision blocks so each type of knowledge is revised with the right level of focus.",
            "Practice numerical questions immediately after concept review to strengthen the link between theory, formula selection, and calculation accuracy.",
            "Use visual summaries for laws, units, and common misconceptions, then revisit them before tests for faster recall.",
        ],
        "chemistry": [
            "Split study time between reactions, conceptual understanding, and numericals so memorization does not replace actual topic mastery.",
            "Use flashcards for equations, valency, symbols, and periodic trends, and review them in short daily bursts to improve retention.",
            "Practice chapter-end questions with short written explanations so the student learns to present chemical reasoning clearly and accurately.",
        ],
        "biology": [
            "Use labelled diagrams and active recall for terminology-heavy chapters so the student can connect structure, function, and vocabulary with less confusion.",
            "Summarize each topic in five key bullet points from memory to check whether the chapter has been understood well enough to explain independently.",
            "Practice descriptive answers with keyword-based marking so exam answers become more complete and scoring improves.",
        ],
        "english": [
            "Build comprehension through daily reading and short written summaries so vocabulary, understanding, and answer quality improve together over time.",
            "Practice grammar in small focused sets and review mistakes immediately, because grammar accuracy improves faster through quick correction than through bulk worksheets.",
            "Prepare model answers for common writing formats and literature themes, then rewrite them in the student's own words to improve structure and confidence.",
        ],
    }

    default_plan = [
        "Review fundamentals first before attempting advanced questions so the student is not building on shaky understanding.",
        "Use active recall, short quizzes, and self-explanation instead of passive rereading to improve long-term retention.",
        "Track mistakes weekly and revisit them before starting new topics so weak foundations are repaired consistently.",
    ]

    plan = subject_map.get(normalized, default_plan)

    if score < 50:
        plan = [
            "Start with foundation-level revision before moving to exam-level questions, because the current score suggests the basics need to be rebuilt carefully.",
            "Use shorter daily study sessions with immediate feedback after each practice block so the student stays engaged without feeling overloaded.",
            "Revisit the same topic within 48 hours through a quick recap or quiz to improve retention and reduce forgetting.",
        ] + plan[:1]

    return plan


def ordered_subjects(student: StudentProfile) -> List[Tuple[str, int]]:
    return sorted(student.marks.items(), key=lambda item: item[1])
