<template>
  <div class="flex flex-col h-full bg-white rounded-lg shadow-md">
    <!-- Chat Header -->
    <div class="flex justify-between items-center p-4 border-b border-gray-200">
      <h2 class="text-xl font-bold text-gray-900">Ask Your Documents</h2>
      <button
        @click="newChat"
        class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
      >
        New Chat
      </button>
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
              <li v-for="(source, idx) in message.sources" :key="idx" class="flex items-start gap-2">
                <span class="text-purple-200">📄</span>
                <span>
                  {{ source.document_name }}, page {{ source.page_number }}
                  <span v-if="source.relevance_score" class="text-purple-300 ml-1">
                    ({{ (source.relevance_score * 100).toFixed(1) }}%)
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

// Create session on mount
onMounted(async () => {
  try {
    const session = await api.createSession()
    sessionId.value = session.id
  } catch (error) {
    console.error('Failed to create session:', error)
  }
})

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
    const response = await api.askQuestion(question, sessionId.value || undefined)

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
    sessionId.value = session.id
    messages.value = []
    inputMessage.value = ''
  } catch (error) {
    console.error('Failed to create new session:', error)
  }
}
</script>
