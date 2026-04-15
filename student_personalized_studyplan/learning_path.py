from typing import Dict

from .models import StudentProfile
from .planning import allocate_weekly_hours, ordered_subjects, recommend_focus


def build_study_path(student: StudentProfile) -> Dict[str, object]:
    subjects = ordered_subjects(student)
    hours = student.weekly_study_hours

    low_subjects = [(subject, score) for subject, score in subjects if score < 60]
    medium_subjects = [(subject, score) for subject, score in subjects if 60 <= score < 80]
    strong_subjects = [(subject, score) for subject, score in subjects if score >= 80]

    return {
        "student": student.name,
        "goal": student.target_goal,
        "weekly_plan": allocate_weekly_hours(hours),
        "phases": [
            {
                "phase": "Phase 1: Diagnose and rebuild fundamentals",
                "duration": "Weeks 1-2",
                "actions": [
                    f"Start with the lowest-scoring subjects, especially {', '.join(subject for subject, _ in low_subjects) or 'none'}, and spend the first two weeks identifying which chapters, concepts, or question types are causing the biggest score drop.",
                    "Review core concepts, formulas, definitions, and solved examples before attempting full-length exercises so understanding becomes stronger than guesswork.",
                    "Create a mistake notebook with one page per subject, recording wrong answers, the reason for each error, and the correct method to use next time.",
                ],
            },
            {
                "phase": "Phase 2: Guided practice and confidence building",
                "duration": "Weeks 3-5",
                "actions": [
                    "Practice topic-wise question sets from easy to moderate level so the student first builds accuracy and then grows comfortable handling mixed difficulty.",
                    "Use one weekly mini-test for each priority subject and review it the same day to convert mistakes into immediate action items instead of repeating them later.",
                    f"Keep steady revision for mid-range subjects such as {', '.join(subject for subject, _ in medium_subjects) or 'none'} so they remain stable while weaker subjects improve.",
                ],
            },
            {
                "phase": "Phase 3: Exam-focused improvement",
                "duration": "Weeks 6-8",
                "actions": [
                    "Attempt timed mixed-subject papers and review errors on the same day so the student improves exam speed, stamina, and answer planning under realistic conditions.",
                    "Convert repeated mistakes into revision flashcards, formula sheets, or summary notes so weak areas become easier to revise quickly before tests.",
                    f"Maintain high-performing subjects such as {', '.join(subject for subject, _ in strong_subjects) or 'none'} with light but regular revision so strengths do not slip while focus stays on weaker areas.",
                ],
            },
        ],
        "subject_actions": [
            {
                "subject": subject,
                "score": score,
                "recommended_actions": recommend_focus(subject, score),
            }
            for subject, score in subjects
        ],
    }
