/**
 * API composable for AskDocs backend
 * Provides typed API calls to FastAPI backend
 */

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: string
}

export interface Source {
  document_name: string
  page_number: number
  relevance_score?: number
}

export interface Session {
  id: string
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  filename: string
  upload_date: string
  chunk_count: number
}

export interface AskResponse {
  answer: string
  sources: Source[]
  session_id: string
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  /**
   * Upload a PDF document
   */
  const uploadDocument = async (file: File): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await $fetch<Document>('/documents', {
      baseURL: apiBase,
      method: 'POST',
      body: formData,
    })

    return response
  }

  /**
   * Get list of all documents
   */
  const listDocuments = async (): Promise<Document[]> => {
    const response = await $fetch<Document[]>('/documents', {
      baseURL: apiBase,
      method: 'GET',
    })

    return response
  }

  /**
   * Delete a document by ID
   */
  const deleteDocument = async (documentId: string): Promise<void> => {
    await $fetch(`/documents/${documentId}`, {
      baseURL: apiBase,
      method: 'DELETE',
    })
  }

  /**
   * Create a new chat session
   */
  const createSession = async (): Promise<Session> => {
    const response = await $fetch<Session>('/sessions/', {
      baseURL: apiBase,
      method: 'POST',
      body: {},
    })

    return response
  }

  /**
   * Get a specific session with messages
   */
  const getSession = async (sessionId: string): Promise<any> => {
    const response = await $fetch(`/sessions/${sessionId}`, {
      baseURL: apiBase,
      method: 'GET',
    })

    return response
  }

  /**
   * Get chat history for a session
   */
  const getSessionHistory = async (sessionId: string): Promise<Message[]> => {
    const response = await $fetch<Message[]>(`/sessions/${sessionId}/history`, {
      baseURL: apiBase,
      method: 'GET',
    })

    return response
  }

  /**
   * Delete a session
   */
  const deleteSession = async (sessionId: string): Promise<void> => {
    await $fetch(`/sessions/${sessionId}`, {
      baseURL: apiBase,
      method: 'DELETE',
    })
  }

  /**
   * Ask a question
   */
  const askQuestion = async (
    question: string,
    sessionId?: string
  ): Promise<AskResponse> => {
    const response = await $fetch<AskResponse>('/ask', {
      baseURL: apiBase,
      method: 'POST',
      body: {
        question,
        session_id: sessionId,
      },
    })

    return response
  }

  /**
   * Health check
   */
  const healthCheck = async () => {
    const response = await $fetch('/health', {
      baseURL: apiBase,
      method: 'GET',
    })

    return response
  }

  return {
    uploadDocument,
    listDocuments,
    deleteDocument,
    createSession,
    getSession,
    getSessionHistory,
    deleteSession,
    askQuestion,
    healthCheck,
  }
}
