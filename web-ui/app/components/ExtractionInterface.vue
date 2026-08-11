<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">📊 Structured Data Extraction</h2>
      <p class="text-gray-600">Extract structured information from your documents using custom schemas</p>
    </div>

    <!-- Step 1: Schema Definition -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 class="text-xl font-semibold text-gray-900 mb-4">1. Define Extraction Schema</h3>

      <div class="space-y-3 mb-4">
        <div v-for="(field, index) in schema" :key="index" class="flex gap-2">
          <input
            v-model="field.name"
            type="text"
            placeholder="Field name (e.g., title)"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <select
            v-model="field.type"
            class="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="string">Text</option>
            <option value="number">Number</option>
            <option value="array">List</option>
          </select>
          <button
            @click="removeField(index)"
            class="px-3 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      <button
        @click="addField"
        class="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors mb-4"
      >
        + Add Field
      </button>

      <!-- Schema Templates -->
      <div class="pt-4 border-t border-gray-200">
        <p class="text-sm text-gray-600 mb-2">Quick Templates:</p>
        <div class="flex gap-2">
          <button
            @click="loadTemplate('job')"
            class="px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors text-sm"
          >
            Job Posting
          </button>
          <button
            @click="loadTemplate('invoice')"
            class="px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors text-sm"
          >
            Invoice
          </button>
          <button
            @click="loadTemplate('resume')"
            class="px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors text-sm"
          >
            Resume
          </button>
        </div>
      </div>
    </div>

    <!-- Step 2: Document Selection -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 class="text-xl font-semibold text-gray-900 mb-4">2. Select Documents</h3>

      <div v-if="loadingDocuments" class="text-center py-8 text-gray-600">
        Loading documents...
      </div>

      <div v-else-if="documents.length === 0" class="text-center py-8 text-gray-400">
        No documents available. Please upload documents first.
      </div>

      <div v-else class="max-h-80 overflow-y-auto space-y-2">
        <div
          v-for="doc in documents"
          :key="doc.id"
          @click="toggleDocument(doc.id)"
          :class="[
            'flex items-center gap-3 p-3 border rounded-md cursor-pointer transition-all',
            selectedDocuments.includes(doc.id)
              ? 'bg-blue-50 border-blue-400'
              : 'border-gray-300 hover:bg-gray-50'
          ]"
        >
          <input
            type="checkbox"
            :checked="selectedDocuments.includes(doc.id)"
            @change="toggleDocument(doc.id)"
            class="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
          />
          <span class="flex-1 font-medium text-gray-900">{{ doc.filename }}</span>
          <span class="text-sm text-gray-500">{{ doc.page_count }} pages</span>
        </div>
      </div>
    </div>

    <!-- Step 3: Extract -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 class="text-xl font-semibold text-gray-900 mb-4">3. Extract Data</h3>
      <button
        @click="extractData"
        :disabled="!canExtract || extracting"
        :class="[
          'px-6 py-3 rounded-md font-semibold transition-colors',
          canExtract && !extracting
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        ]"
      >
        <span v-if="extracting">⏳ Extracting...</span>
        <span v-else>🚀 Extract Data</span>
      </button>
    </div>

    <!-- Results -->
    <div v-if="results.length > 0" class="bg-gray-50 rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold text-gray-900">📄 Extraction Results</h3>
        <div class="flex gap-2">
          <button
            @click="exportResults('json')"
            class="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors text-sm"
          >
            Export JSON
          </button>
          <button
            @click="exportResults('csv')"
            class="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors text-sm"
          >
            Export CSV
          </button>
        </div>
      </div>

      <div class="space-y-4">
        <div
          v-for="result in results"
          :key="result.document_id"
          class="bg-white p-4 rounded-lg border border-gray-200"
        >
          <h4 class="font-semibold text-gray-900 mb-3">{{ result.filename }}</h4>

          <!-- Confidence Bar -->
          <div class="relative h-6 bg-gray-200 rounded-md mb-4 overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-300"
              :style="{ width: (result.confidence * 100) + '%' }"
            ></div>
            <span class="absolute inset-0 flex items-center justify-center text-xs font-semibold text-gray-800">
              {{ (result.confidence * 100).toFixed(0) }}% confidence
            </span>
          </div>

          <!-- Extracted Data -->
          <div class="space-y-2">
            <div
              v-for="(value, key) in result.extracted_data"
              :key="key"
              class="p-2 bg-gray-50 rounded text-sm"
            >
              <strong class="text-gray-700">{{ key }}:</strong>
              <span class="ml-2 text-gray-900">
                <span v-if="Array.isArray(value)">{{ value.join(', ') }}</span>
                <span v-else>{{ value || 'N/A' }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
      ⚠️ {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// State
const schema = ref([
  { name: '', type: 'string' }
])
const documents = ref([])
const selectedDocuments = ref([])
const results = ref([])
const extracting = ref(false)
const loadingDocuments = ref(false)
const error = ref('')

// API base URL and config
const config = useRuntimeConfig()
const API_URL = config.public.apiBase
const API_KEY = config.public.apiKey

// Computed
const canExtract = computed(() => {
  return schema.value.length > 0 &&
         schema.value.some(f => f.name.trim() !== '') &&
         selectedDocuments.value.length > 0
})

// Methods
const addField = () => {
  schema.value.push({ name: '', type: 'string' })
}

const removeField = (index) => {
  if (schema.value.length > 1) {
    schema.value.splice(index, 1)
  }
}

const loadTemplate = (type) => {
  if (type === 'job') {
    schema.value = [
      { name: 'title', type: 'string' },
      { name: 'experience_years', type: 'number' },
      { name: 'required_skills', type: 'array' },
      { name: 'location', type: 'string' },
      { name: 'salary_range', type: 'string' }
    ]
  } else if (type === 'invoice') {
    schema.value = [
      { name: 'invoice_number', type: 'string' },
      { name: 'date', type: 'string' },
      { name: 'total_amount', type: 'number' },
      { name: 'vendor_name', type: 'string' },
      { name: 'items', type: 'array' }
    ]
  } else if (type === 'resume') {
    schema.value = [
      { name: 'name', type: 'string' },
      { name: 'email', type: 'string' },
      { name: 'phone', type: 'string' },
      { name: 'skills', type: 'array' },
      { name: 'experience_years', type: 'number' }
    ]
  }
}

const toggleDocument = (docId) => {
  const index = selectedDocuments.value.indexOf(docId)
  if (index > -1) {
    selectedDocuments.value.splice(index, 1)
  } else {
    selectedDocuments.value.push(docId)
  }
}

const loadDocuments = async () => {
  loadingDocuments.value = true
  error.value = ''
  try {
    const response = await fetch(`${API_URL}/documents/`, {
      headers: {
        'X-API-Key': API_KEY
      }
    })
    if (!response.ok) throw new Error('Failed to load documents')
    const data = await response.json()
    documents.value = data.documents || []
  } catch (e) {
    error.value = e.message
  } finally {
    loadingDocuments.value = false
  }
}

const extractData = async () => {
  extracting.value = true
  error.value = ''
  results.value = []

  try {
    // Build schema object
    const schemaObj = {}
    schema.value.forEach(field => {
      if (field.name.trim()) {
        schemaObj[field.name.trim()] = field.type
      }
    })

    // Extract from each selected document
    const extractionPromises = selectedDocuments.value.map(async (docId) => {
      const response = await fetch(`${API_URL}/extract/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        },
        body: JSON.stringify({
          document_id: docId,
          schema: schemaObj
        })
      })

      if (!response.ok) throw new Error(`Failed to extract from document ${docId}`)

      const result = await response.json()
      return {
        document_id: docId,
        filename: documents.value.find(d => d.id === docId)?.filename || `Document ${docId}`,
        ...result
      }
    })

    results.value = await Promise.all(extractionPromises)
  } catch (e) {
    error.value = e.message
  } finally {
    extracting.value = false
  }
}

const exportResults = async (format) => {
  if (results.value.length === 0) return

  try {
    // Create export locally for all cases
    if (format === 'json') {
        const dataStr = JSON.stringify(results.value, null, 2)
        const blob = new Blob([dataStr], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'extraction_results.json'
        a.click()
        window.URL.revokeObjectURL(url)
      } else if (format === 'csv') {
        // Create CSV from results
        const headers = Object.keys(results.value[0].extracted_data || {})
        const csvRows = [['document_id', 'filename', ...headers].join(',')]

        results.value.forEach(result => {
          const row = [
            result.document_id,
            `"${result.filename}"`,
            ...headers.map(h => {
              const val = result.extracted_data[h]
              if (Array.isArray(val)) return `"${val.join('; ')}"`
              return `"${val || ''}"`
            })
          ]
          csvRows.push(row.join(','))
        })

        const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'extraction_results.csv'
        a.click()
        window.URL.revokeObjectURL(url)
      }
  } catch (e) {
    error.value = `Export failed: ${e.message}`
  }
}

// Load documents on mount
onMounted(() => {
  loadDocuments()
})
</script>
