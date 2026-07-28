<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <!-- Upload Section -->
    <div class="mb-8">
      <h3 class="text-xl font-bold text-gray-900 mb-4">Upload Documents</h3>

      <div
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        :class="[
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          isDragging
            ? 'border-purple-600 bg-purple-50'
            : 'border-gray-300 hover:border-purple-400 hover:bg-gray-50'
        ]"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          @change="handleFileSelect"
          class="hidden"
        />

        <div v-if="!isUploading" class="space-y-2">
          <div class="text-5xl">📄</div>
          <p class="text-lg font-medium text-gray-900">
            {{ isDragging ? 'Drop PDF here' : 'Click to upload or drag & drop' }}
          </p>
          <p class="text-sm text-gray-500">PDF files only</p>
        </div>

        <div v-else class="space-y-2">
          <div class="text-5xl animate-pulse">⏳</div>
          <p class="text-lg font-medium text-purple-600">{{ uploadProgress }}</p>
        </div>
      </div>

      <!-- Metadata Form -->
      <div class="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h4 class="font-semibold text-gray-900 mb-3">Document Metadata (Optional)</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Department</label>
            <select v-model="metadata.department" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600">
              <option value="">Select department</option>
              <option value="HR">HR</option>
              <option value="IT">IT</option>
              <option value="Finance">Finance</option>
              <option value="Operations">Operations</option>
              <option value="Sales">Sales</option>
              <option value="Marketing">Marketing</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Grade Level</label>
            <select v-model="metadata.grade" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600">
              <option value="">Select grade</option>
              <option value="K-8">K-8</option>
              <option value="9-12">9-12</option>
              <option value="College">College</option>
              <option value="All">All Grades</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
            <select v-model="metadata.type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600">
              <option value="">Select type</option>
              <option value="policy">Policy</option>
              <option value="handbook">Handbook</option>
              <option value="guide">Guide</option>
              <option value="manual">Manual</option>
              <option value="contract">Contract</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
            <input
              v-model="metadata.tags"
              type="text"
              placeholder="e.g., vacation, benefits, remote"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Documents List -->
    <div>
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-bold text-gray-900">
          Uploaded Documents ({{ documents.length }})
        </h3>
        <button
          @click="loadDocuments"
          :disabled="isLoadingDocuments"
          class="px-3 py-1.5 text-sm text-purple-600 hover:text-purple-700 font-medium disabled:text-gray-400"
        >
          {{ isLoadingDocuments ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>

      <div v-if="documents.length === 0" class="text-center py-12 text-gray-500">
        <div class="text-4xl mb-2">📭</div>
        <p>No documents uploaded yet</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="doc in documents"
          :key="doc.id"
          class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start gap-3">
            <div class="text-3xl flex-shrink-0">📄</div>
            <div class="flex-1 min-w-0">
              <h4 class="font-semibold text-gray-900 truncate" :title="doc.filename">
                {{ doc.filename }}
              </h4>
              <div class="text-sm text-gray-500 mt-1 space-y-0.5">
                <p>{{ doc.chunk_count }} chunks</p>
                <p>{{ formatDate(doc.uploaded_at) }}</p>
              </div>
              <!-- Metadata Badges -->
              <div v-if="doc.doc_metadata && Object.keys(doc.doc_metadata).length > 0" class="mt-2 flex flex-wrap gap-1">
                <span v-for="(value, key) in doc.doc_metadata" :key="key" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                  {{ key }}: {{ value }}
                </span>
              </div>
            </div>
            <button
              @click="confirmDelete(doc)"
              class="text-red-500 hover:text-red-700 text-xl flex-shrink-0"
              title="Delete document"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="documentToDelete"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click.self="documentToDelete = null"
    >
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-bold text-gray-900 mb-2">Delete Document?</h3>
        <p class="text-gray-600 mb-4">
          Are you sure you want to delete "{{ documentToDelete.filename }}"? This action cannot be undone.
        </p>
        <div class="flex gap-3 justify-end">
          <button
            @click="documentToDelete = null"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            @click="deleteDocument"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Document } from '~/composables/useApi'

const api = useApi()
const documents = ref<Document[]>([])
const isLoadingDocuments = ref(false)
const isUploading = ref(false)
const isDragging = ref(false)
const uploadProgress = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const documentToDelete = ref<Document | null>(null)

// Metadata form state
const metadata = ref({
  department: '',
  grade: '',
  type: '',
  tags: ''
})

// Load documents on mount
onMounted(() => {
  loadDocuments()
})

const loadDocuments = async () => {
  isLoadingDocuments.value = true
  try {
    documents.value = await api.listDocuments()
  } catch (error) {
    console.error('Failed to load documents:', error)
  } finally {
    isLoadingDocuments.value = false
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    uploadFile(file)
  }
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please upload a PDF file')
      return
    }
    uploadFile(file)
  }
}

const uploadFile = async (file: File) => {
  isUploading.value = true
  uploadProgress.value = `Uploading ${file.name}...`

  try {
    // Prepare metadata object (only include non-empty values)
    const metadataObj: Record<string, any> = {}
    if (metadata.value.department) metadataObj.department = metadata.value.department
    if (metadata.value.grade) metadataObj.grade = metadata.value.grade
    if (metadata.value.type) metadataObj.type = metadata.value.type
    if (metadata.value.tags) metadataObj.tags = metadata.value.tags.split(',').map(t => t.trim()).filter(t => t)

    await api.uploadDocument(file, Object.keys(metadataObj).length > 0 ? metadataObj : undefined)
    uploadProgress.value = 'Processing document...'
    await loadDocuments()
    uploadProgress.value = 'Upload complete!'

    // Reset form and metadata after delay
    setTimeout(() => {
      uploadProgress.value = ''
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      // Reset metadata form
      metadata.value = {
        department: '',
        grade: '',
        type: '',
        tags: ''
      }
    }, 1500)
  } catch (error: any) {
    console.error('Upload failed:', error)
    alert(`Upload failed: ${error.data?.detail || error.message || 'Unknown error'}`)
    uploadProgress.value = ''
  } finally {
    isUploading.value = false
  }
}

const confirmDelete = (doc: Document) => {
  documentToDelete.value = doc
}

const deleteDocument = async () => {
  if (!documentToDelete.value) return

  try {
    await api.deleteDocument(documentToDelete.value.id)
    await loadDocuments()
    documentToDelete.value = null
  } catch (error) {
    console.error('Failed to delete document:', error)
    alert('Failed to delete document')
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>
