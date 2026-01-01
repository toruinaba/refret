import { Routes, Route, Link } from 'react-router-dom'
import { Guitar, Music, Upload as UploadIcon, Settings as SettingsIcon } from 'lucide-react'
import { Home } from './pages/Home'
import { LessonDetail } from './pages/LessonDetail'
import { LickLibrary } from './pages/LickLibrary'
import { LickDetail } from './pages/LickDetail'
import { Upload } from './pages/Upload'
import { Settings } from './pages/Settings'

function App() {
  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Navigation Header */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-neutral-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-4 flex items-center justify-between gap-4 flex-wrap">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="p-2 bg-orange-100 rounded-lg group-hover:bg-orange-200 transition-colors">
              <Guitar className="w-6 h-6 sm:w-8 sm:h-8 text-orange-600" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-neutral-900">
                Refret <span className="text-orange-600">Web</span>
              </h1>
              <p className="text-neutral-500 text-xs sm:text-sm hidden sm:block">Your Modern Guitar Practice Environment</p>
            </div>
          </Link>

          <div className="flex items-center gap-2 sm:gap-4">
            <Link to="/upload" className="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-600 text-white font-medium hover:bg-orange-700 transition-colors">
              <UploadIcon className="w-4 h-4" />
              <span className="hidden sm:inline">Upload</span>
            </Link>
            <Link to="/licks" className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-neutral-200 hover:bg-neutral-50 text-neutral-700 font-medium transition-colors">
              <Music className="w-4 h-4" />
              <span className="hidden sm:inline">Lick Library</span>
            </Link>
            <Link to="/settings" className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-neutral-200 hover:bg-neutral-50 text-neutral-500 font-medium transition-colors" title="Settings">
              <SettingsIcon className="w-4 h-4" />
              <span className="hidden sm:inline">Settings</span>
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto p-4 sm:p-6 md:p-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lesson/:id" element={<LessonDetail />} />
          <Route path="/licks" element={<LickLibrary />} />
          <Route path="/lick/:id" element={<LickDetail />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
