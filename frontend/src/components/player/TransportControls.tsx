import type { HTMLAttributes } from "react"
import { Play, Pause, ZoomIn, Repeat, X, SkipBack, SkipForward } from "lucide-react"
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
    onSkipStart: () => void;
    onSkipEnd: () => void;
    showMixer?: boolean;
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
    onSkipStart,
    onSkipEnd,
    showMixer = true,
    ...props
}: TransportControlsProps) {

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className={cn("bg-neutral-900 text-white p-3 rounded-lg flex flex-col sm:flex-row sm:items-center sm:flex-wrap gap-4", className)} {...props}>

            {/* Group 1: Transport Buttons */}
            <div className="flex items-center justify-between sm:justify-start gap-2 sm:gap-4 w-full sm:w-auto">
                <div className="flex items-center gap-2">
                    {/* Skip Start */}
                    <button
                        onClick={onSkipStart}
                        className="w-8 h-8 rounded-full bg-neutral-800 hover:bg-neutral-700 flex items-center justify-center transition-colors text-neutral-400 hover:text-white shrink-0"
                    >
                        <SkipBack className="w-4 h-4 fill-current" />
                    </button>

                    {/* Play Toggle */}
                    <button
                        onClick={onPlayPause}
                        className="w-10 h-10 rounded-full bg-orange-600 hover:bg-orange-500 flex items-center justify-center transition-colors shrink-0"
                    >
                        {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
                    </button>

                    {/* Skip End */}
                    <button
                        onClick={onSkipEnd}
                        className="w-8 h-8 rounded-full bg-neutral-800 hover:bg-neutral-700 flex items-center justify-center transition-colors text-neutral-400 hover:text-white shrink-0"
                    >
                        <SkipForward className="w-4 h-4 fill-current" />
                    </button>
                </div>

                <div className="flex items-center gap-2">
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
                </div>
            </div>

            {/* Group 2: Sliders */}
            <div className="grid grid-cols-2 gap-4 w-full sm:w-auto sm:flex sm:gap-4">
                {/* Speed */}
                <div className="flex flex-col gap-1 w-full sm:w-[100px]">
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
                <div className="flex flex-col gap-1 w-full sm:w-[100px]">
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
            </div>

            {/* Group 3: Tracks & Time */}
            <div className="flex items-center justify-between sm:justify-start gap-4 w-full sm:w-auto border-t border-neutral-800 pt-3 sm:border-0 sm:pt-0 sm:ml-auto">
                {showMixer && (
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
                )}

                <div className="font-mono text-sm text-neutral-400 sm:hidden lg:block">
                    {formatTime(currentTime)} / {formatTime(totalTime)}
                </div>
            </div>

            {/* Desktop Time (hidden on mobile to avoid crowding Group 3, shown in Group 3 on mobile) */}
            <div className="hidden sm:block lg:hidden font-mono text-sm text-neutral-400 ml-auto">
                {formatTime(currentTime)} / {formatTime(totalTime)}
            </div>
        </div>
    )
}
