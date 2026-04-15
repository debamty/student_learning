from typing import Dict

from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    name: str = Field(..., description="Student name")
    grade: str = Field(..., description="Class or grade level")
    target_goal: str = Field(..., description="Exam or academic goal")
    weekly_study_hours: int = Field(..., ge=1, description="Hours available each week")
    preferred_style: str = Field(..., description="Learning preference such as visual or practice-heavy")
    marks: Dict[str, int] = Field(..., description="Subject marks from 0 to 100")
