import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import type { Lesson } from "../../types"
import { api } from "../../lib/api"
import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui/card"
import { Calendar, Tag } from "lucide-react"

export function LessonGrid() {
    const [lessons, setLessons] = useState<Lesson[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const fetchLessons = async () => {
            try {
                const data = await api.getLessons()
                setLessons(data)
            } catch (err) {
                console.error(err)
                setError("Failed to fetch lessons. Is the backend running?")
            } finally {
                setLoading(false)
            }
        }
        fetchLessons()
    }, [])

    if (loading) return <div className="text-center p-8">Loading lessons...</div>

    if (error) return (
        <div className="text-center p-8 text-red-500 bg-red-50 rounded-lg">
            <p>{error}</p>
            <p className="text-sm mt-2">Ensure `start_backend.sh` is running.</p>
        </div>
    )

    if (lessons.length === 0) return (
        <div className="text-center p-8 text-neutral-500">
            No lessons found. Upload one via the original app first!
        </div>
    )

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {lessons.map((lesson) => (
                <Link key={lesson.id} to={`/lesson/${lesson.id}`}>
                    <Card className="h-full cursor-pointer hover:border-orange-200 transition-colors">
                        <CardHeader>
                            <CardTitle className="truncate" title={lesson.title}>
                                {lesson.title}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-col gap-2 text-sm text-neutral-500">
                                <div className="flex items-center gap-2">
                                    <Calendar className="w-4 h-4" />
                                    <span>{lesson.created_at || "Unknown Date"}</span>
                                </div>
                                <div className="flex items-center gap-2 flex-wrap">
                                    <Tag className="w-4 h-4" />
                                    {lesson.tags && lesson.tags.length > 0 ? (
                                        <div className="flex gap-1 flex-wrap">
                                            {lesson.tags.slice(0, 3).map(tag => (
                                                <span key={tag} className="bg-neutral-100 px-2 py-0.5 rounded-full text-xs">
                                                    {tag}
                                                </span>
                                            ))}
                                            {lesson.tags.length > 3 && <span>+{lesson.tags.length - 3}</span>}
                                        </div>
                                    ) : (
                                        <span>No tags</span>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </Link>
            ))}
        </div>
    )
}
