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

export const useCVStore = create<CVState>((set, get) => ({
  documentId: '',
  jobDescription: '',
  tailoredBullets: [],
  isLoading: false,
  error: null,

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
}));