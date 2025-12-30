import { LessonGrid } from "../features/library/LessonGrid"
import { Guitar } from 'lucide-react'

export function Home() {
    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center gap-4 border-b border-neutral-200 pb-6">
                <div className="p-3 bg-orange-100 rounded-lg">
                    <Guitar className="w-8 h-8 text-orange-600" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                        Refret <span className="text-orange-600">Web</span>
                    </h1>
                    <p className="text-neutral-500">Your Modern Guitar Practice Environment</p>
                </div>
            </div>

            {/* Content */}
            <div className="space-y-4">
                <h2 className="text-xl font-semibold text-neutral-800">Your Lessons</h2>
                <LessonGrid />
            </div>
        </div>
    )
}
