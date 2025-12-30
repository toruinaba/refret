import { useParams, Link } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { MultiTrackPlayer } from "../components/player/MultiTrackPlayer"

export function LessonDetail() {
    const { id } = useParams<{ id: string }>()

    if (!id) return <div>Invalid Lesson ID</div>

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Link to="/" className="p-2 hover:bg-neutral-100 rounded-full transition-colors">
                    <ArrowLeft className="w-5 h-5 text-neutral-600" />
                </Link>
                <h1 className="text-2xl font-bold">{id}</h1>
            </div>

            <div className="max-w-4xl mx-auto">
                <MultiTrackPlayer lessonId={id} />
            </div>
        </div>
    )
}
