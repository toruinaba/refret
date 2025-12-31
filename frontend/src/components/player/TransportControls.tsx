import type { HTMLAttributes } from "react"
import { Play, Pause, ZoomIn, Repeat, X } from "lucide-react"
import { cn } from "../../lib/utils"

interface TransportControlsProps extends HTMLAttributes<HTMLDivElement> {
    isPlaying: boolean;
    onPlayPause: () => void;
    playbackRate: number;
    onPlaybackRateChange: (rate: number) => void;
    zoom: number;
    onZoomChange: (zoom: number) => void;
    vocalsMuted: boolean;
    onVocalsMuteChange: (muted: boolean) => void;
    guitarMuted: boolean;
    onGuitarMuteChange: (muted: boolean) => void;
    currentTime: number;
    totalTime: number;
    loop: boolean;
    onLoopChange: (loop: boolean) => void;
    hasSelection: boolean;
    onClearSelection: () => void;
}

export function TransportControls({
    className,
    isPlaying,
    onPlayPause,
    playbackRate,
    onPlaybackRateChange,
    zoom,
    onZoomChange,
    vocalsMuted,
    onVocalsMuteChange,
    guitarMuted,
    onGuitarMuteChange,
    currentTime,
    totalTime,
    loop,
    onLoopChange,
    hasSelection,
    onClearSelection,
    ...props
}: TransportControlsProps) {

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className={cn("bg-neutral-900 text-white p-3 rounded-lg flex items-center flex-wrap gap-3 sm:gap-4", className)} {...props}>
            {/* Play Toggle */}
            <button
                onClick={onPlayPause}
                className="w-10 h-10 rounded-full bg-orange-600 hover:bg-orange-500 flex items-center justify-center transition-colors shrink-0"
            >
                {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
            </button>

            {/* Loop Toggle */}
            <button
                onClick={() => onLoopChange(!loop)}
                className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center transition-colors shrink-0",
                    loop ? "bg-blue-600 hover:bg-blue-500 text-white" : "bg-neutral-800 hover:bg-neutral-700 text-neutral-400"
                )}
                title={loop ? "Loop: ON" : "Loop: OFF"}
            >
                <Repeat className="w-5 h-5" />
            </button>

            {/* Clear Selection */}
            {hasSelection && (
                <button
                    onClick={onClearSelection}
                    className="w-10 h-10 rounded-full bg-neutral-800 hover:bg-red-900/50 text-neutral-400 hover:text-red-400 flex items-center justify-center transition-colors shrink-0"
                    title="Clear Selection"
                >
                    <X className="w-5 h-5" />
                </button>
            )}

            {/* Speed */}
            <div className="flex flex-col gap-1 flex-1 sm:flex-none sm:min-w-[100px]">
                <label className="text-[10px] text-neutral-400 font-medium uppercase tracking-wider whitespace-nowrap">
                    Speed: <span className="text-white">{playbackRate.toFixed(1)}x</span>
                </label>
                <input
                    type="range"
                    min="0.25" max="1.5" step="0.05"
                    value={playbackRate}
                    onChange={(e) => onPlaybackRateChange(parseFloat(e.target.value))}
                    className="accent-orange-500 h-1.5 bg-neutral-700 rounded-lg appearance-none cursor-pointer w-full"
                />
            </div>

            {/* Zoom */}
            <div className="flex flex-col gap-1 flex-1 sm:flex-none sm:min-w-[100px]">
                <label className="text-[10px] text-neutral-400 font-medium uppercase tracking-wider flex items-center gap-1 whitespace-nowrap">
                    <ZoomIn className="w-3 h-3" /> Zoom
                </label>
                <input
                    type="range"
                    min="10" max="200" step="10"
                    value={zoom}
                    onChange={(e) => onZoomChange(parseInt(e.target.value))}
                    className="accent-neutral-500 h-1.5 bg-neutral-700 rounded-lg appearance-none cursor-pointer w-full"
                />
            </div>

            {/* Tracks */}
            <div className="flex items-center gap-4 border-t sm:border-t-0 sm:border-l border-neutral-700 pt-3 sm:pt-0 sm:pl-4 w-full sm:w-auto mt-1 sm:mt-0 justify-between sm:justify-start">
                <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer text-xs">
                        <input
                            type="checkbox"
                            checked={!vocalsMuted}
                            onChange={(e) => onVocalsMuteChange(!e.target.checked)}
                            className="accent-purple-500"
                        />
                        Vocals
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer text-xs">
                        <input
                            type="checkbox"
                            checked={!guitarMuted}
                            onChange={(e) => onGuitarMuteChange(!e.target.checked)}
                            className="accent-orange-500"
                        />
                        Guitar
                    </label>
                </div>

                {/* Time (Moved inside flex row for mobile alignment or kept separate?) */}
                {/* On mobile, let's keep time next to tracks or stack it. */}
                {/* Original layout had time at ml-auto. On mobile this breaks if wrapped. */}
                <div className="sm:ml-auto font-mono text-sm text-neutral-300">
                    {formatTime(currentTime)} / {formatTime(totalTime)}
                </div>
            </div>
        </div>
    )
}
