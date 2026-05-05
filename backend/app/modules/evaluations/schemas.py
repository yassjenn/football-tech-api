from pydantic import BaseModel, Field


class EvaluationCreateRequest(BaseModel):
    """Schema para evaluar a un jugador tras la sesión."""

    technique_score: int = Field(ge=1, le=10)
    physical_score: int = Field(ge=1, le=10)
    attitude_score: int = Field(ge=1, le=10)
    feedback: str | None = None


class EvaluationResponse(BaseModel):
    """Schema de respuesta de evaluación."""

    attendance_id: int
    player_id: int
    convocation_id: int
    technique_score: int | None
    physical_score: int | None
    attitude_score: int | None
    feedback: str | None
    feedback_generated_by_ai: bool

    model_config = {"from_attributes": True}
