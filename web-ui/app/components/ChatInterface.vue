<template>
  <div class="flex flex-col h-full bg-white rounded-lg shadow-md">
    <!-- Chat Header -->
    <div class="p-4 border-b border-gray-200">
      <div class="flex justify-between items-center mb-3">
        <h2 class="text-xl font-bold text-gray-900">Ask Your Documents</h2>
        <button
          @click="newChat"
          class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
        >
          New Chat
        </button>
      </div>

      <!-- Filter Controls -->
      <div class="flex flex-wrap gap-2 items-center">
        <span class="text-sm font-medium text-gray-700">Filters:</span>
        <select v-model="filters.department" class="text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600">
          <option value="">All Departments</option>
          <option value="HR">HR</option>
          <option value="IT">IT</option>
          <option value="Finance">Finance</option>
          <option value="Operations">Operations</option>
          <option value="Sales">Sales</option>
          <option value="Marketing">Marketing</option>
        </select>

        <select v-model="filters.grade" class="text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600">
          <option value="">All Grades</option>
          <option value="K-8">K-8</option>
          <option value="9-12">9-12</option>
          <option value="College">College</option>
          <option value="All">All Grades</option>
        </select>

        <select v-model="filters.type" class="text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600">
          <option value="">All Types</option>
          <option value="policy">Policy</option>
          <option value="handbook">Handbook</option>
          <option value="guide">Guide</option>
          <option value="manual">Manual</option>
          <option value="contract">Contract</option>
        </select>

        <button
          v-if="hasActiveFilters"
          @click="clearFilters"
          class="text-sm px-3 py-1.5 text-purple-600 hover:text-purple-700 font-medium"
        >
          Clear Filters
        </button>

        <span v-if="hasActiveFilters" class="text-xs text-purple-600 font-medium">
          (Filtering active)
        </span>
      </div>
    </div>

    <!-- Messages Container -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-4">
      <!-- Welcome Message -->
      <div v-if="messages.length === 0" class="text-center py-12">
        <div class="text-6xl mb-4">💬</div>
        <h3 class="text-2xl font-bold text-gray-900 mb-2">Welcome to AskDocs!</h3>
        <p class="text-gray-600 mb-1">Upload documents and ask questions to get grounded, cited answers.</p>
        <p class="text-sm text-gray-500 italic">Try asking questions about your uploaded documents.</p>
      </div>

      <!-- Messages -->
      <div
        v-for="message in messages"
        :key="message.id"
        :class="[
          'flex',
          message.role === 'user' ? 'justify-end' : 'justify-start'
        ]"
      >
        <div
          :class="[
            'max-w-[70%] rounded-lg px-4 py-3',
            message.role === 'user'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-100 text-gray-900'
          ]"
        >
          <div class="whitespace-pre-wrap break-words">{{ message.content }}</div>

          <!-- Sources -->
          <div v-if="message.sources && message.sources.length > 0" class="mt-3 pt-3 border-t border-purple-500/20">
            <div class="text-sm font-semibold mb-2">Sources:</div>
            <ul class="text-sm space-y-1">
              <li v-for="(source, idx) in getUniqueSources(message.sources)" :key="idx" class="flex items-start gap-2">
                <span class="text-purple-200">📄</span>
                <span>
                  {{ source.filename }}, page {{ source.page_number }}
                  <span v-if="source.chunk_count > 1" class="text-purple-300 ml-1">
                    ({{ source.chunk_count }} chunks)
                  </span>
                  <span v-if="source.reranking_score" class="text-purple-200 ml-1">
                    - {{ (source.reranking_score * 100).toFixed(1) }}% relevance
                  </span>
                  <span v-else-if="source.similarity_score" class="text-purple-300 ml-1">
                    - {{ (source.similarity_score * 100).toFixed(1) }}% match
                  </span>
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Loading Indicator -->
      <div v-if="isLoading" class="flex justify-start">
        <div class="max-w-[70%] bg-gray-100 rounded-lg px-4 py-3">
          <div class="flex items-center gap-2">
            <div class="flex gap-1">
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
            </div>
            <span class="text-sm text-gray-600">Thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Form -->
    <div class="border-t border-gray-200 p-4 bg-gray-50">
      <form @submit.prevent="sendMessage" class="flex gap-3">
        <input
          v-model="inputMessage"
          type="text"
          placeholder="Ask a question about your documents..."
          :disabled="isLoading"
          class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          :disabled="isLoading || !inputMessage.trim()"
          class="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '~/composables/useApi'

const api = useApi()
const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const sessionId = ref<string | null>(null)
const messagesContainer = ref<HTMLDivElement | null>(null)

// Filter state
const filters = ref({
  department: '',
  grade: '',
  type: ''
})

// Check if any filters are active
const hasActiveFilters = computed(() => {
  return filters.value.department || filters.value.grade || filters.value.type
})

// Clear all filters
const clearFilters = () => {
  filters.value = {
    department: '',
    grade: '',
    type: ''
  }
}

// Restore or create session on mount
onMounted(async () => {
  // Check localStorage for existing session
  const storedSessionId = localStorage.getItem('askdocs_session_id')

  if (storedSessionId) {
    // Try to verify session exists
    try {
      const session = await api.getSession(storedSessionId)
      sessionId.value = storedSessionId

      // Load message history
      if (session.messages && session.messages.length > 0) {
        messages.value = session.messages.map((msg: any) => ({
          id: msg.id.toString(),
          role: msg.role,
          content: msg.content,
          sources: msg.sources,
          timestamp: msg.created_at
        }))
      }
    } catch (error) {
      console.warn('Stored session not found, creating new session')
      await createNewSession()
    }
  } else {
    // No stored session, create new one
    await createNewSession()
  }
})

// Helper to create new session
const createNewSession = async () => {
  try {
    const session = await api.createSession()
    sessionId.value = session.id.toString()
    localStorage.setItem('askdocs_session_id', sessionId.value)
  } catch (error) {
    console.error('Failed to create session:', error)
  }
}

// Auto-scroll to bottom when new messages arrive
watch(messages, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}, { deep: true })

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date().toISOString(),
  }

  messages.value.push(userMessage)
  const question = inputMessage.value
  inputMessage.value = ''
  isLoading.value = true

  try {
    // Prepare metadata filters (only include non-empty values)
    const metadataFilters: Record<string, any> = {}
    if (filters.value.department) metadataFilters.department = filters.value.department
    if (filters.value.grade) metadataFilters.grade = filters.value.grade
    if (filters.value.type) metadataFilters.type = filters.value.type

    const response = await api.askQuestion(
      question,
      sessionId.value || undefined,
      Object.keys(metadataFilters).length > 0 ? metadataFilters : undefined
    )

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.answer,
      sources: response.sources,
      timestamp: new Date().toISOString(),
    }

    messages.value.push(assistantMessage)

    if (response.session_id && !sessionId.value) {
      sessionId.value = response.session_id
    }
  } catch (error: any) {
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: `Error: ${error.data?.detail || error.message || 'Failed to get response'}`,
      timestamp: new Date().toISOString(),
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
  }
}

const newChat = async () => {
  try {
    const session = await api.createSession()
    sessionId.value = session.id.toString()
    localStorage.setItem('askdocs_session_id', sessionId.value)
    messages.value = []
    inputMessage.value = ''
  } catch (error) {
    console.error('Failed to create new session:', error)
  }
}

// Deduplicate sources by document and page
const getUniqueSources = (sources: any[] | undefined) => {
  if (!sources || sources.length === 0) return []

  const sourceMap = new Map()

  sources.forEach(source => {
    const key = `${source.filename || source.document_name}_page_${source.page_number}`

    if (!sourceMap.has(key)) {
      sourceMap.set(key, {
        filename: source.filename || source.document_name,
        page_number: source.page_number,
        similarity_score: source.similarity_score || source.relevance_score,
        chunk_count: 1
      })
    } else {
      // Increment chunk count and average the similarity score
      const existing = sourceMap.get(key)
      existing.chunk_count += 1
      existing.similarity_score = Math.max(existing.similarity_score, source.similarity_score || source.relevance_score || 0)
    }
  })

  return Array.from(sourceMap.values()).sort((a, b) => b.similarity_score - a.similarity_score)
}
</script>
