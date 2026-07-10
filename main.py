import os
import json

# HTTPException: lets you return clean web error codes 
# (like 400 Bad Request or 500 Internal Server Error) 
# back to a client browser.
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# It ensures data sent to your API matches exact types
from pydantic import BaseModel
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
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']


# This function manages token state. 
# It reads an existing session token, 
# refreshes it if it expired, 
# or boots up a first-time login sequence.
def get_google_docs_service():
    """Authenticates the user and returns the Google Docs API service client."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    # It is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
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
    return build('docs', 'v1', credentials=creds)

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

# Defines a explicit blueprint for incoming API calls. 
# It mandates that any frontend request sent to this path 
# must provide a JSON payload containing a string parameter key 
# explicitly named "document_id".
class DocRequest(BaseModel):
    document_id: str
    job_description: str

# # Registers a web-accessible POST route.
# @app.post("/api/fetch-cv")
# async def fetch_cv(payload: DocRequest):
#     """
#     Accepts a Google Doc ID, authenticates, extracts the body text, 
#     and returns it.
#     """
#     try:
#         # Initialize the Docs service
#         service = get_google_docs_service()
        
#         # Retrieve the document structure from Google API
#         document = service.documents().get(documentId=payload.document_id).execute()
#         doc_title = document.get('title')
#         doc_body = document.get('body').get('content')
        
#         # Parse the JSON structural elements into raw text string
#         raw_text = extract_text_from_elements(doc_body)
        
#         return {
#             "status": "success",
#             "document_title": doc_title,
#             "text_content": raw_text
#         }
        
#     except FileNotFoundError as fnf_error:
#         raise HTTPException(status_code=500, detail=str(fnf_error))
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Failed to fetch document: {str(e)}")

@app.post("/api/tailor-cv")
async def tailor_cv(payload: DocRequest):
    try:
        # Step A: Fetch the base CV text using our existing logic
        service = get_google_docs_service()
        document = service.documents().get(documentId=payload.document_id).execute()
        base_cv_text = extract_text_from_elements(document.get('body').get('content'))
        
        # Step B: Design the system prompt with strict rules
        system_instruction = (
            "You are an expert technical resume writer. Your job is to adapt the user's base CV "
            "to better match the provided job description. "
            "CRITICAL RULES:\n"
            "1. Do NOT invent fake experience, fake companies, or alter dates.\n"
            "2. Rephrase existing bullet points to naturally highlight skills, tools, and keywords requested in the job description.\n"
            "3. You must return your response strictly as a JSON object containing an array of strings named 'tailored_bullets'."
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
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "tailored_bullets": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING)
                        )
                    },
                    required=["tailored_bullets"]
                )
            )
        )
        
        # Parse the string response from the AI back into a standard Python dictionary
        tailored_data = json.loads(response.text)
        
        return {
            "status": "success",
            "data": tailored_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Tailoring failed: {str(e)}")
    
if __name__ == "__main__":
    # Run the server locally on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)