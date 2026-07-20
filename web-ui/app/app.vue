<template>
  <div class="min-h-screen bg-gray-50">
    <NuxtRouteAnnouncer />

    <!-- Header -->
    <header class="bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <h1 class="text-3xl font-bold">AskDocs RAG Agent</h1>
        <p class="text-purple-100 mt-2">Ask questions to your documents with grounded, cited answers</p>
      </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="bg-white border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex space-x-8">
          <button
            @click="activeTab = 'chat'"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'chat'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            Chat
          </button>
          <button
            @click="activeTab = 'documents'"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'documents'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            Documents
          </button>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div v-if="activeTab === 'chat'" class="bg-white rounded-lg shadow-md p-8">
        <div class="text-center py-12">
          <div class="text-6xl mb-4">💬</div>
          <h2 class="text-2xl font-bold text-gray-900 mb-2">Chat Interface</h2>
          <p class="text-gray-600">Ask questions and get grounded answers with citations</p>
          <p class="text-sm text-gray-500 mt-4">Coming soon...</p>
        </div>
      </div>

      <div v-if="activeTab === 'documents'" class="bg-white rounded-lg shadow-md p-8">
        <div class="text-center py-12">
          <div class="text-6xl mb-4">📄</div>
          <h2 class="text-2xl font-bold text-gray-900 mb-2">Document Management</h2>
          <p class="text-gray-600">Upload and manage your PDF documents</p>
          <p class="text-sm text-gray-500 mt-4">Coming soon...</p>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <p class="text-center text-gray-500 text-sm">
          Built with FastAPI, LangGraph, Nuxt, and Tailwind CSS
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const activeTab = ref<'chat' | 'documents'>('chat')
</script>
