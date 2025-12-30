import { Routes, Route, Link } from 'react-router-dom'
import { Guitar, Music } from 'lucide-react'
import { Home } from './pages/Home'
import { LessonDetail } from './pages/LessonDetail'
import { LickLibrary } from './pages/LickLibrary'
import { LickDetail } from './pages/LickDetail'

function App() {
  return (
    <div className="min-h-screen bg-neutral-50 p-8">
      <div className="max-w-6xl mx-auto">

        {/* Navigation Header */}
        <div className="flex items-center justify-between border-b border-neutral-200 pb-6 mb-8">
          <Link to="/" className="flex items-center gap-4 group">
            <div className="p-3 bg-orange-100 rounded-lg group-hover:bg-orange-200 transition-colors">
              <Guitar className="w-8 h-8 text-orange-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                Refret <span className="text-orange-600">Web</span>
              </h1>
              <p className="text-neutral-500 text-sm">Your Modern Guitar Practice Environment</p>
            </div>
          </Link>

          <div className="flex gap-4">
            <Link to="/licks" className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-neutral-200 hover:bg-neutral-50 text-neutral-700 font-medium transition-colors">
              <Music className="w-4 h-4" />
              Lick Library
            </Link>
          </div>
        </div>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lesson/:id" element={<LessonDetail />} />
          <Route path="/licks" element={<LickLibrary />} />
          <Route path="/lick/:id" element={<LickDetail />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
