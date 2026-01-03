import { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from "react"
import WaveSurfer from "wavesurfer.js"
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.js"
import { TransportControls } from "./TransportControls"
import { api } from "../../lib/api"
import { cn } from "../../lib/utils"

interface MultiTrackPlayerProps {
    lessonId?: string; // Optional now
    audioUrl?: string; // For single mode
    mode?: 'lesson' | 'single';
    analysisData?: { bpm: number; key: string };

    initialRegion?: { start: number, end: number };
    onSelectionChange?: (region: { start: number, end: number } | null) => void;
    className?: string;
    autoPlay?: boolean;
    initialVocalsMuted?: boolean;
}

export interface MultiTrackPlayerRef {
    seekTo: (time: number) => void;
}

export const MultiTrackPlayer = forwardRef<MultiTrackPlayerRef, MultiTrackPlayerProps>(({
    lessonId,
    audioUrl,
    mode = 'lesson',
    analysisData,
    initialRegion,
    onSelectionChange,
    className,
    autoPlay = false,
    initialVocalsMuted = false
}, ref) => {
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
    const [vocalsMuted, setVocalsMuted] = useState(initialVocalsMuted)
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
            // console.log(`[MultiTrackPlayer] seekTo: ${time}s (Duration: ${duration}s, Ready: ${isReady})`);

            if (isReady && duration > 0) {
                const progress = time / duration;
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
        // Validation
        if (mode === 'lesson' && !lessonId) return;
        if (mode === 'single' && !audioUrl) return;
        if (!containerG.current) return;
        if (mode === 'lesson' && !containerV.current) return;

        // Cleanup previous
        if (wsG.current) wsG.current.destroy();
        if (wsV.current) wsV.current.destroy();
        setIsReady(false);

        // 1. Fetch Peaks Data
        const loadWaveSurfer = async () => {
            // Helper to fetch peaks
            const fetchPeaks = async (trackType: string) => {
                if (mode !== 'lesson' || !lessonId) return undefined;
                try {
                    // Try to fetch peaks JSON
                    // We assume API client can do this or fetch directly. 
                    // Since api.client isn't fully exposed here, using fetch for now or adding to api.ts?
                    // Let's assume we use the endpoint we just made: /api/lessons/{id}/audio/{track}/peaks
                    const response = await fetch(`/api/lessons/${lessonId}/audio/${trackType}/peaks`);
                    if (!response.ok) return undefined;
                    const json = await response.json();
                    return json.data; // Server returns { data: [...], points_per_second: 100 }
                } catch (e) {
                    // console.warn("Failed to load peaks", e);
                    return undefined;
                }
            };

            const [vocalsPeaks, guitarPeaks] = await Promise.all([
                mode === 'lesson' ? fetchPeaks("vocals") : Promise.resolve(undefined),
                mode === 'lesson' ? fetchPeaks("guitar") : Promise.resolve(undefined),
            ]);

            // console.log("Peaks loaded:", { vocals: vocalsPeaks?.length, guitar: guitarPeaks?.length });

            // 1. Create Vocals (Only for Lesson Mode)
            if (mode === 'lesson' && containerV.current) {
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
                    interact: false, // Slave track
                    backend: 'MediaElement', // Key for streaming!
                    peaks: vocalsPeaks // Pass peaks to avoid decoding
                });
                if (wsV.current.getMediaElement()) {
                    wsV.current.getMediaElement().autoplay = false;
                }
            }

            // 2. Create Master Track (Guitar or Single Log)
            const regions = RegionsPlugin.create()
            regionsG.current = regions

            // Color theme based on mode
            const waveColor = mode === 'lesson' ? '#F97316' : '#14b8a6'; // Orange / Teal
            const progressColor = mode === 'lesson' ? '#C2410C' : '#0d9488';

            wsG.current = WaveSurfer.create({
                container: containerG.current,
                waveColor: waveColor,
                progressColor: progressColor,
                cursorColor: progressColor,
                barWidth: 2,
                barGap: 1,
                barRadius: 2,
                height: mode === 'single' ? 120 : 70, // Taller for single
                normalize: true,
                minPxPerSec: zoom,
                plugins: [regions],
                backend: 'MediaElement', // Key for streaming!
                peaks: guitarPeaks // Pass peaks to avoid decoding
            });
            if (wsG.current.getMediaElement()) {
                wsG.current.getMediaElement().autoplay = false;
            }


            // Load Audio with Peaks support
            // WaveSurfer with MediaElement backend loads audio via HTML5 Audio tag
            // but renders waveform using peaks provided in create().
            const gUrl = mode === 'lesson' && lessonId ? api.getAudioUrl(lessonId, "guitar") : audioUrl!;

            wsG.current.load(gUrl); // Peaks already set in create

            if (mode === 'lesson' && lessonId && wsV.current) {
                const vUrl = api.getAudioUrl(lessonId, "vocals");
                wsV.current.load(vUrl);
            }

            // --- Event Bindings ---
            // (Re-bind events here because we are inside async init)
            bindEvents();
        };

        const bindEvents = () => {
            if (!wsG.current) return;

            wsG.current.on('timeupdate', (currentTime) => {
                setCurrentTime(currentTime);
            });

            wsG.current.on('ready', () => {
                setIsReady(true);
                setTotalTime(wsG.current?.getDuration() || 0);

                // Handle Initial Region
                if (initialRegion && regionsG.current) {
                    regionsG.current.clearRegions();
                    regionsG.current.addRegion({
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
                }
            });

            wsG.current.on('finish', () => {
                setIsPlaying(false);
            });

            // --- Synchronization Logic (Lesson Mode Only) ---
            if (mode === 'lesson' && wsV.current) {
                wsG.current.on('seeking', (currentTime) => {
                    wsV.current?.setTime(currentTime);
                });
                wsG.current.on('interaction', () => {
                    wsV.current?.setTime(wsG.current?.getCurrentTime() || 0);
                });
            }

            // Region Events
            if (regionsG.current) {
                regionsG.current.enableDragSelection({
                    color: 'rgba(255, 0, 0, 0.3)',
                });

                regionsG.current.on('region-created', (region) => {
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

                regionsG.current.on('region-out', (region) => {
                    if (!wsG.current?.isPlaying()) return;

                    if (loopRef.current) {
                        const start = region.start;
                        wsG.current?.setTime(start);
                        wsV.current?.setTime(start);
                        wsG.current?.play();
                        wsV.current?.play();
                    } else {
                        wsG.current?.pause();
                        wsV.current?.pause();
                        setIsPlaying(false);
                    }
                });

                regionsG.current.on('region-clicked', (region, e) => {
                    e.stopPropagation();
                    const start = region.start;
                    wsG.current?.setTime(start);
                    wsV.current?.setTime(start);
                    wsG.current?.play();
                    wsV.current?.play();
                    setIsPlaying(true);
                });
            }
        };

        // Start initialization
        loadWaveSurfer();


        // Cleanup
        return () => {
            try { wsV.current?.destroy(); } catch (e) { }
            try { wsG.current?.destroy(); } catch (e) { }
        }
    }, [lessonId, audioUrl, mode]);

    // --- Handlers ---
    useEffect(() => {
        if (!isReady) return;
        wsV.current?.zoom(zoom);
        wsG.current?.zoom(zoom);
    }, [zoom, isReady]);

    useEffect(() => {
        if (!isReady) return;
        wsV.current?.setPlaybackRate(playbackRate);
        wsG.current?.setPlaybackRate(playbackRate);
    }, [playbackRate, isReady]);

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
            {/* Analysis Badge (Single Mode) */}
            {mode === 'single' && analysisData && (
                <div className="flex gap-2 mb-4">
                    <div className="bg-teal-50 text-teal-700 px-3 py-1 rounded-full text-xs font-bold border border-teal-200">
                        BPM: {Math.round(analysisData.bpm)}
                    </div>
                    <div className="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-xs font-bold border border-indigo-200">
                        Key: {analysisData.key}
                    </div>
                </div>
            )}

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
                showMixer={mode === 'lesson'}
            />

            {/* Waveforms */}
            <div className="space-y-4 w-full">
                {mode === 'lesson' && (
                    <div className="relative bg-neutral-50 rounded-lg p-2 border border-neutral-100 overflow-x-auto w-full">
                        <span className="absolute top-2 left-2 text-[10px] font-bold bg-white/80 px-1.5 py-0.5 rounded pointer-events-none z-10">
                            🗣️ Vocals
                        </span>
                        <div ref={containerV} className="w-full" />
                    </div>
                )}

                <div className="relative bg-neutral-50 rounded-lg p-2 border border-neutral-100 overflow-x-auto w-full">
                    {mode === 'lesson' && (
                        <span className="absolute top-2 left-2 text-[10px] font-bold bg-white/80 px-1.5 py-0.5 rounded pointer-events-none z-10">
                            🎸 Guitar
                        </span>
                    )}
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
