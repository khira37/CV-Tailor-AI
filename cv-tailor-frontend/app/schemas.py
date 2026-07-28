# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class DocRequest(BaseModel):
    document_id: str
    job_description: str

class ReplacementItem(BaseModel):
    old_text: str = Field(description="The exact text of the original bullet point from the CV.")
    new_text: str = Field(description="The newly optimized, high-impact bullet point tailored to the job description.")

class SummaryReplacement(BaseModel):
    old_summary: str = Field(description="The exact text of the original professional summary section.")
    new_summary: str = Field(description="The newly optimized professional summary.")

class CVTailorResponse(BaseModel):
    summary_replacement: SummaryReplacement = Field(description="The structural changes for the resume's summary section.")
    tailored_bullets: List[ReplacementItem] = Field(description="The list of changes for individual resume project/work bullet points.")

class UpdateDocRequest(BaseModel):
    document_id: str
    summary_replacement: Optional[SummaryReplacement] = None
    tailored_bullets: List[ReplacementItem]