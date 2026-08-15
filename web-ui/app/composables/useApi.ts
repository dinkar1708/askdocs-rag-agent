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
  uploaded_at: string
  chunk_count: number
  page_count: number
  doc_metadata?: Record<string, any>
}

export interface JobResponse {
  job_id: string
  filename: string
  status: string
  message: string
}

export interface JobStatus {
  job_id: string
  filename: string
  status: 'queued' | 'extracting' | 'chunking' | 'embedding' | 'storing' | 'complete' | 'failed'
  progress: number
  current_stage?: string
  error_message?: string
  result_document_id?: number
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface AskResponse {
  answer: string
  sources: Source[]
  session_id: string
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase
  const apiKey = config.public.apiKey

  // Default headers with API authentication
  const getHeaders = () => ({
    'X-API-Key': apiKey
  })

  /**
   * Upload a PDF document (returns job_id for async processing)
   */
  const uploadDocument = async (file: File, metadata?: Record<string, any>): Promise<JobResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    if (metadata && Object.keys(metadata).length > 0) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    const response = await $fetch<JobResponse>('/documents', {
      baseURL: apiBase,
      method: 'POST',
      body: formData,
      headers: getHeaders()
    })

    return response
  }

  /**
   * Get job status for document processing
   */
  const getJobStatus = async (jobId: string): Promise<JobStatus> => {
    const response = await $fetch<JobStatus>(`/documents/jobs/${jobId}`, {
      baseURL: apiBase,
      method: 'GET',
      headers: getHeaders()
    })

    return response
  }

  /**
   * Poll job status until complete or failed
   */
  const pollJobStatus = async (
    jobId: string,
    onProgress?: (status: JobStatus) => void,
    pollInterval: number = 1000
  ): Promise<JobStatus> => {
    while (true) {
      const status = await getJobStatus(jobId)

      if (onProgress) {
        onProgress(status)
      }

      if (status.status === 'complete' || status.status === 'failed') {
        return status
      }

      // Wait before polling again
      await new Promise(resolve => setTimeout(resolve, pollInterval))
    }
  }

  /**
   * Get list of all documents
   */
  const listDocuments = async (): Promise<Document[]> => {
    const response = await $fetch<{documents: Document[], total: number}>('/documents', {
      baseURL: apiBase,
      method: 'GET',
      headers: getHeaders()
    })

    return response.documents
  }

  /**
   * Delete a document by ID
   */
  const deleteDocument = async (documentId: string): Promise<void> => {
    await $fetch(`/documents/${documentId}`, {
      baseURL: apiBase,
      method: 'DELETE',
      headers: getHeaders()
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
      headers: getHeaders()
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
      headers: getHeaders()
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
      headers: getHeaders()
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
      headers: getHeaders()
    })
  }

  /**
   * Ask a question
   */
  const askQuestion = async (
    question: string,
    sessionId?: string,
    metadataFilters?: Record<string, any>
  ): Promise<AskResponse> => {
    const response = await $fetch<AskResponse>('/ask', {
      baseURL: apiBase,
      method: 'POST',
      body: {
        question,
        session_id: sessionId,
        metadata_filters: metadataFilters,
      },
      headers: getHeaders()
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
      headers: getHeaders()
    })

    return response
  }

  return {
    uploadDocument,
    getJobStatus,
    pollJobStatus,
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
