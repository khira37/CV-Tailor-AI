# app/services.py
from contextlib import contextmanager

@contextmanager
def temporary_google_doc(drive_service, source_file_id: str, title: str):
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

def extract_text_from_elements(elements):
    text = ""
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for el in elements:
                if 'textRun' in el:
                    text += el.get('textRun').get('content')
        elif 'table' in value:
            table = value.get('table')
            for row in table.get('tableRows'):
                for cell in row.get('tableCells'):
                    text += extract_text_from_elements(cell.get('content'))
    return text

def replace_cv_elements_in_google_doc(document_id: str, data: dict, service):
    requests = []
    
    summary_data = data.get("summary_replacement")
    if summary_data and summary_data.get("old_summary"):
        requests.append({
            'replaceAllText': {
                'containsText': {'text': summary_data['old_summary'], 'matchCase': True},
                'replaceText': summary_data['new_summary']
            }
        })
        
    for item in data.get("replacements", []):
        requests.append({
            'replaceAllText': {
                'containsText': {'text': item['old_text'], 'matchCase': True},
                'replaceText': item['new_text']
            }
        })
        
    if requests:
        service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()