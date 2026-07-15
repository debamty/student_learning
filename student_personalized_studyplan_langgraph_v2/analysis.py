from typing import Dict

from .models import StudentProfile
from .planning import ordered_subjects, performance_band


def build_marks_analysis(student: StudentProfile) -> Dict[str, object]:
    sorted_subjects = ordered_subjects(student)

    return {
        "student": student.name,
        "grade": student.grade,
        "target_goal": student.target_goal,
        "weekly_study_hours": student.weekly_study_hours,
        "preferred_style": student.preferred_style,
        "average_score": round(sum(student.marks.values()) / len(student.marks), 1),
        "subjects": [
            {
                "subject": subject,
                "score": score,
                "performance_band": performance_band(score),
                "focus_level": "primary" if score < 60 else "secondary" if score < 75 else "maintenance",
            }
            for subject, score in sorted_subjects
        ],
        "top_strengths": [subject for subject, score in sorted_subjects[::-1] if score >= 75][:2],
        "priority_subjects": [subject for subject, score in sorted_subjects if score < 60][:3],
    }
