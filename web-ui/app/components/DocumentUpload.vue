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
                <p>{{ formatDate(doc.upload_date) }}</p>
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
    await api.uploadDocument(file)
    uploadProgress.value = 'Processing document...'
    await loadDocuments()
    uploadProgress.value = 'Upload complete!'

    // Reset after delay
    setTimeout(() => {
      uploadProgress.value = ''
      if (fileInput.value) {
        fileInput.value.value = ''
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
