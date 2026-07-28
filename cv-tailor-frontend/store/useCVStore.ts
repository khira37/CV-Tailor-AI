import { create } from 'zustand';

// why did we name it store? 
// a store in zustand is where we store the state 
// and any function that update that state

interface ReplacementItem {
  old_text: string;
  new_text: string;
}

interface SummaryReplacement {
  old_summary: string;
  new_summary: string;
}

// This defines the structure of the data. 
// It tells TypeScript exactly what variables exist and thier types.
interface CVState {
  documentId: string;
  jobDescription: string;
  tailoredBullets: ReplacementItem[];
  summaryReplacement: SummaryReplacement | null;
  isLoading: boolean;
  error: string | null;
  isSaving: boolean;
  updateGoogleDoc: () => Promise<void>;
  setDocumentId: (id: string) => void;
  setJobDescription: (text: string) => void;
  processCV: () => Promise<void>;
  resetStore: () => void;
  

  
}

export const useCVStore = create<CVState>((set, get) => ({
  documentId: '',
  jobDescription: '',
  tailoredBullets: [],
  summaryReplacement: null,
  isLoading: false,
  error: null,
  isSaving : false,

  setDocumentId: (id) => set({ documentId: id }),
  setJobDescription: (text) => set({ jobDescription: text }),

  processCV: async () => {
    const { documentId, jobDescription } = get();
    if (!documentId || !jobDescription) {
      set({ error: 'Please provide both a Document ID and a Job Description.' });
      return;
    }

    set({ isLoading: true, error: null, tailoredBullets: [] });

    try {
      const response = await fetch('http://127.0.0.1:8000/api/tailor-cv', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentId,
          job_description: jobDescription,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to process application data.');
      }

      const result = await response.json();
      if (result.status === 'success') {
        set({ tailoredBullets: result.data.tailored_bullets });
      } else {
        throw new Error('An unexpected status error occurred.');
      }
    } catch (err: any) {
      set({ error: err.message || 'Something went wrong.' });
    } finally {
      set({ isLoading: false });
    }
  },

  resetStore: () => set({ tailoredBullets: [], error: null }),

  updateGoogleDoc: async () => {
    const { documentId, tailoredBullets, summaryReplacement } = get();
    
    if (!documentId) {
      alert("No document ID found!");
      return;
    }

    set({ isSaving: true });
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/update-doc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: documentId,
          summary_replacement: summaryReplacement, // Make sure you track this in your store state
          tailored_bullets: tailoredBullets
        })
      });

      if (!response.ok) throw new Error("Network response failed");

      const pdfBlob = await response.blob();
      // 2. Create a hidden download link
    const downloadUrl = window.URL.createObjectURL(pdfBlob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = "Tailored_Resume.pdf"; // Modern property syntax

    // 3. Append, click, and cleanly detach
    document.body.appendChild(link);
    link.click();
    
    //  FIX: Use .remove() directly instead of link.parentNode.removeChild()
    link.remove();
    
    // 4. Revoke the object URL to prevent memory leaks
    window.URL.revokeObjectURL(downloadUrl);
    
    } catch (error) {
      console.error(error);
      alert("Error updating document. Check backend console.");
    } finally {
      alert("Done.");
      set({ isSaving: false });
    }
  }

}));