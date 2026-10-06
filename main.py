import os
import json
import io
from contextlib import contextmanager

# HTTPException: lets you return clean web error codes 
# (like 400 Bad Request or 500 Internal Server Error) 
# back to a client browser.
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# It ensures data sent to your API matches exact types
from pydantic import BaseModel, Field
from typing import List, Optional

# The lightning-fast local web server that
# physically listens for incoming web traffic and routes it to FastAPI.
import uvicorn


# Google API Libraries
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# connects your local code to a specific Google
# service ecosystem (like Docs, Sheets, or Drive).
from googleapiclient.discovery import build

# Gemini 
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Resume Tailor Backend Pipeline",
    description="API to extract Google Doc content and process job applications",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Gemini client (It automatically looks for an environment variable named GEMINI_API_KEY)
ai_client = genai.Client()


# If modifying these scopes, delete the file token.json.
# 'auth/documents.readonly' allows us to read docs without accidental modifications (read-only)
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]


# This function manages token state. 
# It reads an existing session token, 
# refreshes it if it expired, 
# or boots up a first-time login sequence.
def get_google_auth_credentials():
    """Authenticates the user and returns the Google Docs API service client."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    # It is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request()) # Request: It serves as the underlying HTTP network engine. It provides the secure connection environment
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "Missing 'credentials.json' file. Please download your OAuth 2.0 client config "
                    "from the Google Cloud Console and place it in this directory."
                )
            
            # InstalledAppFlow, opens a tab in your web browser 
            # to perform the formal Google OAuth login screen.
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # build('docs', 'v1', ...) initializes an authorized 
    # client pointing directly at Google Docs API v1.
    return creds

def get_google_docs_service():
    creds = get_google_auth_credentials()
    return build('docs', 'v1', credentials=creds)

def get_drive_service():
    creds = get_google_auth_credentials()
    return build('drive', 'v3', credentials=creds)

def extract_text_from_elements(elements):
    """Recursively extracts raw text from structural elements of a Google Doc."""
    text = ""
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for el in elements:
                if 'textRun' in el:
                    text += el.get('textRun').get('content')
        elif 'table' in value:
            # Handle resume layouts that use tables
            table = value.get('table')
            for row in table.get('tableRows'):
                for cell in row.get('tableCells'):
                    text += extract_text_from_elements(cell.get('content'))
    return text

class DocRequest(BaseModel):
    document_id: str
    job_description: str

class ReplacementItem(BaseModel):
    old_text: str = Field(description="The exact text of the original bullet point from the CV.")
    new_text: str = Field(description="The newly optimized, high-impact bullet point tailored to the job description.")

class SummaryReplacement(BaseModel):
    old_summary: str = Field(description="The exact text of the original professional summary or objective section from the CV.")
    new_summary: str = Field(description="The newly optimized professional summary tailored to the target job description.")

class CVTailorResponse(BaseModel):
    summary_replacement: SummaryReplacement = Field(description="The structural changes for the resume's summary or profile section.")
    tailored_bullets: List[ReplacementItem] = Field(description="The list of changes for individual resume project/work bullet points.")

# Define the payload format your frontend will send
class UpdateDocRequest(BaseModel):
    document_id: str
    summary_replacement: Optional[SummaryReplacement] = None
    tailored_bullets: List[ReplacementItem]

@contextmanager
def temporary_google_doc(drive_service, source_file_id: str, title: str):
    """
    Context manager that duplicates a source Google Doc, yields its temporary ID,
    and guarantees its absolute deletion from Google Drive when exiting the block—
    even if downstream operations or network streaming crashes.
    """
    copy_metadata = {'name': title}
    copied_file = drive_service.files().copy(fileId=source_file_id, body=copy_metadata).execute()
    temp_id = copied_file.get('id')
    try:
        yield temp_id
    finally:
        try:
            drive_service.files().delete(fileId=temp_id).execute()
        except Exception as e:
            print(f"Failed to clean up temporary file {temp_id}: {e}")


@app.post("/api/tailor-cv")
async def tailor_cv(payload: DocRequest):
    try:
        # Step A: Fetch the base CV text using our existing logic
        service = get_google_docs_service()
        document = service.documents().get(documentId=payload.document_id).execute()
        base_cv_text = extract_text_from_elements(document.get('body').get('content'))
        
        # Step B: Design the system prompt with strict rules
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
        
        # Step C: Ask the LLM for a structured JSON response
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                # This forces the model to respond with clean, parseable JSON matching our structure
                response_mime_type="application/json",
                response_schema=CVTailorResponse
            )
        )
        
        # Parse the string response from the AI back into a standard Python dictionary
        structured_data = json.loads(response.text)
        
        return {
            "status": "success",
            "data": structured_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Tailoring failed: {str(e)}")


def replace_cv_elements_in_google_doc(document_id: str, data: dict, service):
    requests = []
    
    # 1. Queue up the Summary Replacement if it exists
    summary_data = data.get("summary_replacement")
    print("\n------------------------")
    print(summary_data)
    print("\n--------------------------")
    if summary_data and summary_data.get("old_summary"):
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': summary_data['old_summary'],
                    'matchCase': True #case-sensitive
                },
                'replaceText': summary_data['new_summary']
            }
        })
        
    # 2. Queue up the Bullet Point Replacements
    bullet_replacements = data.get("replacements", [])
    for item in bullet_replacements:
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': item['old_text'],
                    'matchCase': True
                },
                'replaceText': item['new_text']
            }
        })
        
    # 3. Execute all changes atomically
    if requests:
        service.documents().batchUpdate(
            documentId=document_id, 
            body={'requests': requests}
        ).execute()
        
    return {"status": "success", "message": "Document updated successfully."}


@app.post("/api/update-doc")
async def update_google_document(payload: UpdateDocRequest):
    try:
        docs_service = get_google_docs_service()
        drive_service = get_drive_service()
        
        execution_data = {
            "summary_replacement": payload.summary_replacement.model_dump() if payload.summary_replacement else None,
            "replacements": [item.model_dump() for item in payload.tailored_bullets]
        }
        
        temp_filename = f"Tailored_CV_Working_Copy_{payload.document_id[:6]}"
        
        # Open our safety context manager wrapping the duplication routine
        with temporary_google_doc(drive_service, payload.document_id, temp_filename) as temp_doc_id:
            
            # 1. Modify the temporary clone instead of the user's master file
            replace_cv_elements_in_google_doc(
                document_id=temp_doc_id,
                data=execution_data,
                service=docs_service
            )
            
            # 2. Convert and download the file locally to backend memory as a PDF binary stream
            pdf_bytes = drive_service.files().export_media(
                fileId=temp_doc_id,
                mimeType='application/pdf'
            ).execute()
            
        # 3. Stream the file directly down to the browser.
        # (Once this block closes, the context manager automatically deletes the temporary Google Doc)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Tailored_Resume.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update and export document: {str(e)}")

    

if __name__ == "__main__":
    # Run the server locally on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)