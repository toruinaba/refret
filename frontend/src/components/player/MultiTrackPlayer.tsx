import { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from "react"
import WaveSurfer from "wavesurfer.js"
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.js"
import { TransportControls } from "./TransportControls"
import { api } from "../../lib/api"
import { cn } from "../../lib/utils"

interface MultiTrackPlayerProps {
    lessonId: string;
    initialRegion?: { start: number, end: number };
    onSelectionChange?: (region: { start: number, end: number } | null) => void;
    className?: string;
    autoPlay?: boolean;
}

export interface MultiTrackPlayerRef {
    seekTo: (time: number) => void;
}

export const MultiTrackPlayer = forwardRef<MultiTrackPlayerRef, MultiTrackPlayerProps>(({ lessonId, initialRegion, onSelectionChange, className, autoPlay = false }, ref) => {
    // Container Refs
    const containerV = useRef<HTMLDivElement>(null)
    const containerG = useRef<HTMLDivElement>(null)

    // Instances
    const wsV = useRef<WaveSurfer | null>(null)
    const wsG = useRef<WaveSurfer | null>(null)
    const regionsG = useRef<RegionsPlugin | null>(null)

    // State
    const [isReady, setIsReady] = useState(false)
    const [isPlaying, setIsPlaying] = useState(false)
    const [playbackRate, setPlaybackRate] = useState(1.0)
    const [zoom, setZoom] = useState(20)
    const [vocalsMuted, setVocalsMuted] = useState(false)
    const [guitarMuted, setGuitarMuted] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)
    const [totalTime, setTotalTime] = useState(0)
    const [selection, setSelection] = useState<{ start: number, end: number } | null>(null)
    const [loop, setLoop] = useState(true)
    const loopRef = useRef(loop)

    useEffect(() => {
        loopRef.current = loop;
    }, [loop]);

    // Expose seekTo
    useImperativeHandle(ref, () => ({
        seekTo: (time: number) => {
            const duration = wsG.current?.getDuration() || 0;
            console.log(`[MultiTrackPlayer] seekTo: ${time}s (Duration: ${duration}s, Ready: ${isReady})`);

            if (isReady && duration > 0) {
                const progress = time / duration;
                // Clamp progress
                const p = Math.max(0, Math.min(1, progress));

                wsG.current?.seekTo(p);
                wsV.current?.seekTo(p);

                // Auto-play
                wsG.current?.play();
                wsV.current?.play();
                setIsPlaying(true);
            }
        }
    }));

    // --- Initialization ---
    useEffect(() => {
        if (!containerV.current || !containerG.current) return;

        // 1. Create Vocals
        wsV.current = WaveSurfer.create({
            container: containerV.current,
            waveColor: '#A855F7',
            progressColor: '#7E22CE',
            cursorColor: '#7E22CE',
            barWidth: 2,
            barGap: 1,
            barRadius: 2,
            height: 70,
            normalize: true,
            minPxPerSec: zoom,
            interact: false, // Slave track interacts via Master
        });
        if (wsV.current.getMediaElement()) {
            wsV.current.getMediaElement().autoplay = false;
        }

        // 2. Create Guitar (Master)
        const regions = RegionsPlugin.create()
        regionsG.current = regions

        wsG.current = WaveSurfer.create({
            container: containerG.current,
            waveColor: '#F97316',
            progressColor: '#C2410C',
            cursorColor: '#C2410C',
            barWidth: 2,
            barGap: 1,
            barRadius: 2,
            height: 70,
            normalize: true,
            minPxPerSec: zoom,
            plugins: [regions]
        });
        if (wsG.current.getMediaElement()) {
            wsG.current.getMediaElement().autoplay = false;
        }


        // Load Audio
        const vUrl = api.getAudioUrl(lessonId, "vocals");
        const gUrl = api.getAudioUrl(lessonId, "guitar");

        wsV.current.load(vUrl);
        wsG.current.load(gUrl);

        // --- Event Bindings ---

        // Time Update (Only need one source usually)
        wsG.current.on('timeupdate', (currentTime) => {
            setCurrentTime(currentTime);
        });

        wsG.current.on('ready', () => {
            setIsReady(true);
            setTotalTime(wsG.current?.getDuration() || 0);

            // Handle Initial Region
            if (initialRegion) {
                regions.clearRegions();
                regions.addRegion({
                    start: initialRegion.start,
                    end: initialRegion.end,
                    color: 'rgba(255, 0, 0, 0.3)',
                    drag: true,
                    resize: true
                });
                setSelection(initialRegion);
                onSelectionChange?.(initialRegion);
                wsG.current?.setTime(initialRegion.start);
                wsV.current?.setTime(initialRegion.start);
            }

            if (autoPlay) {
                wsG.current?.play();
                wsV.current?.play();
                setIsPlaying(true);
            } else {
                wsG.current?.pause();
                wsV.current?.pause();
                setIsPlaying(false);
            }
        });

        wsG.current.on('finish', () => {
            setIsPlaying(false);
        });

        // --- Synchronization Logic ---
        // If user clicks on Guitar track (Master)
        wsG.current.on('seeking', (currentTime) => {
            wsV.current?.setTime(currentTime);
        });

        wsG.current.on('interaction', () => {
            wsV.current?.setTime(wsG.current?.getCurrentTime() || 0);
        });

        // Region Events (Draggable)
        // Enable Drag Selection
        regionsG.current.enableDragSelection({
            color: 'rgba(255, 0, 0, 0.3)',
        });

        regionsG.current.on('region-created', (region) => {
            // Enforce Single Region: Clear others
            regionsG.current?.getRegions().forEach(r => {
                if (r !== region) r.remove();
            });
            const s = { start: region.start, end: region.end };
            setSelection(s);
            onSelectionChange?.(s);
        });

        regionsG.current.on('region-updated', (region) => {
            const s = { start: region.start, end: region.end };
            setSelection(s);
            onSelectionChange?.(s);
        });

        // Manual Loop Sync (Ported from Streamlit app.py)
        regionsG.current.on('region-out', (region) => {
            // Check if we are actually playing, otherwise this might be a seek/init event
            if (!wsG.current?.isPlaying()) return;

            if (loopRef.current) {
                // Loop back
                const start = region.start;
                wsG.current?.setTime(start);
                wsV.current?.setTime(start);
                wsG.current?.play();
                wsV.current?.play();
            } else {
                // Pause
                wsG.current?.pause();
                wsV.current?.pause();
                setIsPlaying(false);
            }
        });

        regionsG.current.on('region-clicked', (region, e) => {
            e.stopPropagation(); // Avoid seeking parent
            const start = region.start;
            wsG.current?.setTime(start);
            wsV.current?.setTime(start);
            wsG.current?.play();
            wsV.current?.play();
            setIsPlaying(true);
        });

        // Cleanup
        // Cleanup
        return () => {
            try {
                wsV.current?.destroy();
            } catch (e) {
                // Ignore AbortError during cleanup
            }
            try {
                wsG.current?.destroy();
            } catch (e) {
                // Ignore AbortError during cleanup
            }
        }
    }, [lessonId]); // Re-init on lesson change

    // --- Handlers ---

    // Zoom
    useEffect(() => {
        if (!isReady) return;
        wsV.current?.zoom(zoom);
        wsG.current?.zoom(zoom);
    }, [zoom, isReady]);

    // Speed
    useEffect(() => {
        if (!isReady) return;
        wsV.current?.setPlaybackRate(playbackRate);
        wsG.current?.setPlaybackRate(playbackRate);
    }, [playbackRate, isReady]);

    // Play/Pause
    const togglePlay = useCallback(() => {
        if (wsG.current?.isPlaying()) {
            wsV.current?.pause();
            wsG.current?.pause();
            setIsPlaying(false);
        } else {
            wsV.current?.play();
            wsG.current?.play();
            setIsPlaying(true);
        }
    }, []);

    // Mute
    useEffect(() => {
        wsV.current?.setMuted(vocalsMuted);
    }, [vocalsMuted]);

    useEffect(() => {
        wsG.current?.setMuted(guitarMuted);
    }, [guitarMuted]);

    const handleClearSelection = useCallback(() => {
        regionsG.current?.clearRegions();
        setSelection(null);
        onSelectionChange?.(null);
    }, [onSelectionChange]);

    const handleSkipStart = useCallback(() => {
        const time = selection ? selection.start : 0;
        wsG.current?.setTime(time);
        wsV.current?.setTime(time);
    }, [selection]);

    const handleSkipEnd = useCallback(() => {
        const time = selection ? selection.end : (wsG.current?.getDuration() || 0);
        wsG.current?.setTime(time);
        wsV.current?.setTime(time);
    }, [selection]);


    return (
        <div className={cn("bg-white rounded-xl border border-neutral-200 shadow-sm p-2 sm:p-4 w-full min-w-0", className)}>
            <TransportControls
                className="mb-4"
                isPlaying={isPlaying}
                onPlayPause={togglePlay}
                playbackRate={playbackRate}
                onPlaybackRateChange={setPlaybackRate}
                zoom={zoom}
                onZoomChange={setZoom}
                vocalsMuted={vocalsMuted}
                onVocalsMuteChange={setVocalsMuted}
                guitarMuted={guitarMuted}
                onGuitarMuteChange={setGuitarMuted}
                currentTime={currentTime}
                totalTime={totalTime}
                loop={loop}
                onLoopChange={setLoop}
                hasSelection={!!selection}
                onClearSelection={handleClearSelection}
                onSkipStart={handleSkipStart}
                onSkipEnd={handleSkipEnd}
            />

            {/* Waveforms */}
            <div className="space-y-4 w-full">
                <div className="relative bg-neutral-50 rounded-lg p-2 border border-neutral-100 overflow-x-auto w-full">
                    <span className="absolute top-2 left-2 text-[10px] font-bold bg-white/80 px-1.5 py-0.5 rounded pointer-events-none z-10">
                        🗣️ Vocals
                    </span>
                    <div ref={containerV} className="w-full" />
                </div>

                <div className="relative bg-neutral-50 rounded-lg p-2 border border-neutral-100 overflow-x-auto w-full">
                    <span className="absolute top-2 left-2 text-[10px] font-bold bg-white/80 px-1.5 py-0.5 rounded pointer-events-none z-10">
                        🎸 Guitar
                    </span>
                    <div ref={containerG} className="w-full" />
                </div>
            </div>

            {/* Selection Info */}
            <div className="mt-2 text-xs text-neutral-400 font-mono text-right">
                Selection: {selection ? `${selection.start.toFixed(2)}s - ${selection.end.toFixed(2)}s` : "--"}
            </div>
        </div>
    )
})

MultiTrackPlayer.displayName = "MultiTrackPlayer"
