import { useState } from 'react'
import { Guitar } from 'lucide-react'

function App() {
  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="p-4 bg-orange-100 rounded-full">
            <Guitar className="w-12 h-12 text-orange-600" />
          </div>
        </div>

        <h1 className="text-4xl font-bold tracking-tight text-neutral-900">
          Refret <span className="text-orange-600">Web</span>
        </h1>

        <p className="text-lg text-neutral-600">
          The modern Frontend for your Guitar Lesson Review tool is successfully initialized.
        </p>

        <div className="p-4 bg-white rounded-lg border border-neutral-200 shadow-sm text-left">
          <h3 className="font-semibold mb-2">Next Steps (Phase 3):</h3>
          <ul className="list-disc pl-5 space-y-1 text-sm text-neutral-600">
            <li>Connect to FastAPI Backend</li>
            <li>Implement Lesson Library Grid</li>
            <li>Port Wavesurfer Player Logic</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default App
