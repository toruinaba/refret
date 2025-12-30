import { Routes, Route } from 'react-router-dom'
import { Home } from './pages/Home'
import { LessonDetail } from './pages/LessonDetail'

function App() {
  return (
    <div className="min-h-screen bg-neutral-50 p-8">
      <div className="max-w-6xl mx-auto">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lesson/:id" element={<LessonDetail />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
