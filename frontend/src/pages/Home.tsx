import { LessonGrid } from "../features/library/LessonGrid"

export function Home() {
    return (
        <div className="space-y-8">
            <div className="space-y-4">
                <h2 className="text-xl font-semibold text-neutral-800">Your Lessons</h2>
                <LessonGrid />
            </div>
        </div>
    )
}
