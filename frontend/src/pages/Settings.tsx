import { useState, useEffect } from "react"
import { api } from "../lib/api"
import { Save, Lock, AlertCircle, Mic, Music, Layers, Brain } from "lucide-react"

export function Settings() {
    const [settings, setSettings] = useState({
        llm_provider: "openai",
        openai_api_key: "",
        llm_model: "gpt-3.5-turbo",
        system_prompt: "",
        // Audio defaults
        demucs_model: "htdemucs",
        demucs_shifts: 1,
        demucs_overlap: 0.25,
        whisper_model: "base",
        whisper_beam_size: 5,
        bp_onset_threshold: 0.6,
        bp_min_frequency: 80.0,
        bp_quantize_grid: 4
    })
    const [originalApiKeyMasked, setOriginalApiKeyMasked] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

    useEffect(() => {
        api.getSettings().then(data => {
            setSettings(prev => ({
                ...prev,
                llm_provider: data.llm_provider,
                openai_api_key: "",
                llm_model: data.llm_model,
                system_prompt: data.system_prompt,
                // Load Audio settings if present (fallback to defaults if undefined)
                demucs_model: data.demucs_model ?? "htdemucs",
                demucs_shifts: data.demucs_shifts ?? 1,
                demucs_overlap: data.demucs_overlap ?? 0.25,
                whisper_model: data.whisper_model ?? "base",
                whisper_beam_size: data.whisper_beam_size ?? 5,
                bp_onset_threshold: data.bp_onset_threshold ?? 0.6,
                bp_min_frequency: data.bp_min_frequency ?? 80.0,
                bp_quantize_grid: data.bp_quantize_grid ?? 4
            }))
            setOriginalApiKeyMasked(data.openai_api_key_masked)
            setLoading(false)
        }).catch(err => {
            console.error(err)
            setLoading(false)
        })
    }, [])

    const handleSave = async () => {
        setSaving(true)
        setMessage(null)
        try {
            await api.saveSettings(settings)
            setMessage({ type: 'success', text: "Settings saved successfully!" })
            const data = await api.getSettings();
            setOriginalApiKeyMasked(data.openai_api_key_masked)
            setSettings(prev => ({ ...prev, openai_api_key: "" }))
        } catch (e) {
            setMessage({ type: 'error', text: "Failed to save settings." })
        } finally {
            setSaving(false)
        }
    }

    if (loading) return <div className="p-8">Loading settings...</div>

    return (
        <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in duration-500 pb-20">
            <div className="flex items-center justify-between border-b border-neutral-200 pb-4">
                <h1 className="text-2xl font-bold">App Settings</h1>
            </div>

            {message && (
                <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {message.type === 'success' ? <Save className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    {message.text}
                </div>
            )}

            <div className="space-y-8">

                {/* Section 1: LLM */}
                <section className="space-y-4 bg-white p-6 rounded-xl border border-neutral-200 shadow-sm">
                    <div className="flex items-center gap-2 pb-4 border-b border-neutral-100 mb-4">
                        <Brain className="w-5 h-5 text-indigo-600" />
                        <h2 className="text-lg font-semibold text-neutral-800">LLM & Summarization</h2>
                    </div>

                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">Provider</label>
                                <select
                                    value={settings.llm_provider}
                                    onChange={e => setSettings({ ...settings, llm_provider: e.target.value })}
                                    className="w-full border border-neutral-300 rounded-lg px-3 py-2 bg-neutral-50"
                                >
                                    <option value="openai">OpenAI</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">Model</label>
                                <input
                                    type="text"
                                    value={settings.llm_model}
                                    onChange={e => setSettings({ ...settings, llm_model: e.target.value })}
                                    className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1 flex justify-between">
                                <span>API Key</span>
                                {originalApiKeyMasked && <span className="text-xs text-green-600 flex items-center gap-1"><Lock className="w-3 h-3" /> Configured ({originalApiKeyMasked})</span>}
                            </label>
                            <input
                                type="password"
                                value={settings.openai_api_key}
                                onChange={e => setSettings({ ...settings, openai_api_key: e.target.value })}
                                placeholder={originalApiKeyMasked ? "Has configured key (Leave empty to keep)" : "sk-..."}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">System Prompt</label>
                            <textarea
                                value={settings.system_prompt}
                                onChange={e => setSettings({ ...settings, system_prompt: e.target.value })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2 h-24 font-mono text-sm leading-relaxed"
                            />
                        </div>
                    </div>
                </section>

                {/* Section 2: Separation */}
                <section className="space-y-4 bg-white p-6 rounded-xl border border-neutral-200 shadow-sm">
                    <div className="flex items-center gap-2 pb-4 border-b border-neutral-100 mb-4">
                        <Layers className="w-5 h-5 text-blue-600" />
                        <h2 className="text-lg font-semibold text-neutral-800">Audio Separation (Demucs)</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Model Architecture</label>
                            <select
                                value={settings.demucs_model}
                                onChange={e => setSettings({ ...settings, demucs_model: e.target.value })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2 bg-neutral-50"
                            >
                                <option value="htdemucs">htdemucs (Latest, Best)</option>
                                <option value="hdemucs_mmi">hdemucs_mmi</option>
                                <option value="mdx_extra_q">mdx_extra_q</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Shifts (Quality vs Speed)</label>
                            <input
                                type="number"
                                min={1} max={10}
                                value={settings.demucs_shifts}
                                onChange={e => setSettings({ ...settings, demucs_shifts: parseInt(e.target.value) || 1 })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                            />
                            <p className="text-xs text-neutral-500 mt-1">Higher = better quality but slower.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Overlap</label>
                            <input
                                type="number"
                                min={0} max={0.9} step={0.05}
                                value={settings.demucs_overlap}
                                onChange={e => setSettings({ ...settings, demucs_overlap: parseFloat(e.target.value) || 0.25 })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                            />
                        </div>
                    </div>
                </section>

                {/* Section 3: Speech Transcription */}
                <section className="space-y-4 bg-white p-6 rounded-xl border border-neutral-200 shadow-sm">
                    <div className="flex items-center gap-2 pb-4 border-b border-neutral-100 mb-4">
                        <Mic className="w-5 h-5 text-red-600" />
                        <h2 className="text-lg font-semibold text-neutral-800">Speech Transcription (Whisper)</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Model Size</label>
                            <select
                                value={settings.whisper_model}
                                onChange={e => setSettings({ ...settings, whisper_model: e.target.value })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2 bg-neutral-50"
                            >
                                <option value="tiny">tiny (Fastest)</option>
                                <option value="base">base</option>
                                <option value="small">small (Balanced)</option>
                                <option value="medium">medium</option>
                                <option value="large-v3">large-v3 (Best Quality)</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Beam Size</label>
                            <input
                                type="number"
                                min={1} max={10}
                                value={settings.whisper_beam_size}
                                onChange={e => setSettings({ ...settings, whisper_beam_size: parseInt(e.target.value) || 5 })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                            />
                        </div>
                    </div>
                </section>

                {/* Section 4: Music Transcription */}
                <section className="space-y-4 bg-white p-6 rounded-xl border border-neutral-200 shadow-sm">
                    <div className="flex items-center gap-2 pb-4 border-b border-neutral-100 mb-4">
                        <Music className="w-5 h-5 text-green-600" />
                        <h2 className="text-lg font-semibold text-neutral-800">Music Transcription (Basic Pitch)</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Onset Threshold ({settings.bp_onset_threshold})</label>
                            <input
                                type="range"
                                min={0.1} max={0.9} step={0.05}
                                value={settings.bp_onset_threshold}
                                onChange={e => setSettings({ ...settings, bp_onset_threshold: parseFloat(e.target.value) })}
                                className="w-full"
                            />
                            <p className="text-xs text-neutral-500 mt-1">Sensitivity. Lower (0.3) = More Notes, Higher (0.7) = Clean.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Min Frequency (Hz)</label>
                            <input
                                type="number"
                                min={20} max={200}
                                value={settings.bp_min_frequency}
                                onChange={e => setSettings({ ...settings, bp_min_frequency: parseFloat(e.target.value) || 80.0 })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                            />
                            <p className="text-xs text-neutral-500 mt-1">E2=82Hz, D2=73Hz. Lower for Drop tuning.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Quantization Grid</label>
                            <select
                                value={settings.bp_quantize_grid}
                                onChange={e => setSettings({ ...settings, bp_quantize_grid: parseInt(e.target.value) })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2 bg-neutral-50"
                            >
                                <option value={2}>8th Notes (2)</option>
                                <option value={4}>16th Notes (4)</option>
                                <option value={8}>32nd Notes (8)</option>
                            </select>
                        </div>
                    </div>
                </section>

                <div className="pt-4 border-t border-neutral-100 flex justify-end sticky bottom-0 bg-white/80 p-4 border-t backdrop-blur-sm shadow-lg rounded-t-xl">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 bg-neutral-900 text-white px-8 py-3 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50 shadow-md"
                    >
                        {saving ? "Saving..." : <><Save className="w-4 h-4" /> Save All Settings</>}
                    </button>
                </div>
            </div>
        </div>
    )
}
