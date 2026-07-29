# app/router.py
import io
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from google.genai import types

from schemas import DocRequest, UpdateDocRequest, CVTailorResponse
from utils import get_google_docs_service, get_drive_service, get_gemini_client
from services import extract_text_from_elements, temporary_google_doc, replace_cv_elements_in_google_doc

router = APIRouter(prefix="/api", tags=["CV Operations"])
ai_client = get_gemini_client()

@router.post("/tailor-cv")
async def tailor_cv(payload: DocRequest):
    try:
        docs_service = get_google_docs_service()
        document = docs_service.documents().get(documentId=payload.document_id).execute()
        base_cv_text = extract_text_from_elements(document.get('body').get('content'))
        
        system_instruction = (
            "You are an expert technical resume writer. Your job is to take the original resume bullet points "
            "and rewrite them to perfectly match the target job description.\n"
            "CRITICAL RULES:\n"
            "1. Do NOT invent fake experience, fake companies, or alter dates.\n"
            "2. Rephrase existing bullet points to naturally highlight skills, tools, and keywords requested in the job description.\n"
            "3. You must return your response strictly as a JSON object matching the requested schema layout.\n"
            "4. Find the professional summary paragraph or profile statement at the top of the resume, and rewrite it to strongly align with the trajectory requested in the job description."
        )
            
        prompt = f"""
            Base CV Text:
            {base_cv_text}
            
            Target Job Description:
            {payload.job_description}
        """
        
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CVTailorResponse
            )
        )
        
        return {"status": "success", "data": json.loads(response.text)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Tailoring failed: {str(e)}")

@router.post("/update-doc")
async def update_google_document(payload: UpdateDocRequest):
    try:
        docs_service = get_google_docs_service()
        drive_service = get_drive_service()
        
        execution_data = {
            "summary_replacement": payload.summary_replacement.model_dump() if payload.summary_replacement else None,
            "replacements": [item.model_dump() for item in payload.tailored_bullets]
        }
        
        temp_filename = f"Tailored_CV_Working_Copy_{payload.document_id[:6]}"
        
        with temporary_google_doc(drive_service, payload.document_id, temp_filename) as temp_doc_id:
            replace_cv_elements_in_google_doc(
                document_id=temp_doc_id,
                data=execution_data,
                service=docs_service
            )
            
            pdf_bytes = drive_service.files().export_media(
                fileId=temp_doc_id,
                mimeType='application/pdf'
            ).execute()
            
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Tailored_Resume.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update and export document: {str(e)}")