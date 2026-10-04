
Personally this Agent is my favorite prject. 
I built this project and made use of it in real life.

A full-stack application that analyzes your Google Doc resume alongside a target job description, 
optimizes your work experience and skills using Gemini AI, and exports a tailored PDF—all while keeping your original document completely untouched.

How It Works:
Provide Your Inputs: Pass in your Google Doc resume ID and the targeted job description.
Context-Aware AI Optimization: The AI agent analyzes your experience and rewrites project bullet points and skills to align with the job description—without hallucinating false information or fake experience.
Safe Duplicate & Replace Workflow: The system creates a temporary copy of your CV in your Google Drive, performs precise find-and-replace updates via the Google Docs API, exports the result as a PDF, and cleans up after itself. Your original master resume remains intact.
Direct Download: Download your newly optimized, tailored resume directly as a PDF from the UI.

What I learned building this project:
- Google Cloud & OAuth 2.0 Integration
- State Management with Zustand
- Structured AI Outputs

Results
image 1
image 2
image 3
image 4


future work
i'm happy with where this agent is today, but for future work maybe makeing this an acutal app would be a lot easier than running it locally, also maybe add a feature to make the system apply for the job after enhancing the CV.
