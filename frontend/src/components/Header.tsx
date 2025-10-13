export default function Header() {
  return (
    <header className="text-center mb-12">
      <h1 className="text-5xl font-bold text-gray-800 mb-4">
        Speech Analysis
      </h1>
      <p className="text-xl text-gray-600 mb-2">
        RAG-based Information Retrieval System
      </p>
      <p className="text-sm text-gray-500">
        Semantic search powered by ChromaDB and Sentence Transformers
      </p>
    </header>
  )
}
