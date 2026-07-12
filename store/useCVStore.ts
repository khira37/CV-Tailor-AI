import { create } from 'zustand';

interface CVState {
  documentId: string;
  jobDescription: string;
  tailoredBullets: string[];
  isLoading: boolean;
  error: string | null;
  setDocumentId: (id: string) => void;
  setJobDescription: (text: string) => void;
  processCV: () => Promise<void>;
  resetStore: () => void;
}

// set is used to update the state, 
// and get is used to read the current state.
export const useCVStore = create<CVState>((set, get) => ({
  documentId: '',
  jobDescription: '',
  tailoredBullets: [],
  isLoading: false,
  error: null,

  // simple helper functions to update the documentId & jobDescription
  // in the global state whenever the user types in the input field.
  // These two functions are called in the page.tsx
  setDocumentId: (id) => set({ documentId: id }),
  setJobDescription: (text) => set({ jobDescription: text }),

  processCV: async () => {

    // grabs the current user inputs from the store.
    const { documentId, jobDescription } = get();

    if (!documentId || !jobDescription) {
      set({ error: 'Please provide both a Document ID and a Job Description.' });
      return;
    }

    // It resets the UI state
    // يعني تمسح المعلومات القديمة لما نطلب ريكويست جديد
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
      set({ isLoading: false }); // turns off the loading spinner
    }
  },

  // A cleanup function to clear the results and errors when 
  // the user wants to start over.
  resetStore: () => set({ tailoredBullets: [], error: null }),
}));