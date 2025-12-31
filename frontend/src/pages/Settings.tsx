import { useState, useEffect } from "react"
import { api } from "../lib/api"
import { Save, Lock, AlertCircle } from "lucide-react"

export function Settings() {
    const [settings, setSettings] = useState({
        llm_provider: "openai",
        openai_api_key: "",
        llm_model: "gpt-3.5-turbo",
        system_prompt: ""
    })
    const [originalApiKeyMasked, setOriginalApiKeyMasked] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

    useEffect(() => {
        api.getSettings().then(data => {
            setSettings({
                llm_provider: data.llm_provider,
                openai_api_key: "", // Don't show masked key in input
                llm_model: data.llm_model,
                system_prompt: data.system_prompt
            })
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
            // Refresh to get masked key status update if needed
            const data = await api.getSettings();
            setOriginalApiKeyMasked(data.openai_api_key_masked)
            setSettings(prev => ({ ...prev, openai_api_key: "" })) // Clear input
        } catch (e) {
            setMessage({ type: 'error', text: "Failed to save settings." })
        } finally {
            setSaving(false)
        }
    }

    if (loading) return <div className="p-8">Loading settings...</div>

    return (
        <div className="max-w-2xl mx-auto space-y-8 animate-in fade-in duration-500 pb-20">
            <div className="flex items-center justify-between border-b border-neutral-200 pb-4">
                <h1 className="text-2xl font-bold">Settings</h1>
            </div>

            {message && (
                <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {message.type === 'success' ? <Save className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    {message.text}
                </div>
            )}

            <div className="space-y-6 bg-white p-6 rounded-xl border border-neutral-200 shadow-sm">

                {/* Provider */}
                <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-1">LLM Provider</label>
                    <select
                        value={settings.llm_provider}
                        onChange={e => setSettings({ ...settings, llm_provider: e.target.value })}
                        className="w-full border border-neutral-300 rounded-lg px-3 py-2 bg-neutral-50"
                    >
                        <option value="openai">OpenAI</option>
                        {/* Future: <option value="ollama">Ollama (Local)</option> */}
                    </select>
                </div>

                {/* API Key */}
                <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-1 flex justify-between">
                        <span>OpenAI API Key</span>
                        {originalApiKeyMasked && <span className="text-xs text-green-600 flex items-center gap-1"><Lock className="w-3 h-3" /> Configured ({originalApiKeyMasked})</span>}
                    </label>
                    <input
                        type="password"
                        value={settings.openai_api_key}
                        onChange={e => setSettings({ ...settings, openai_api_key: e.target.value })}
                        placeholder={originalApiKeyMasked ? "Has configured key (Leave empty to keep)" : "sk-..."}
                        className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                    />
                    <p className="text-xs text-neutral-500 mt-1">
                        Required for summarization. Leave empty to keep existing key.
                    </p>
                </div>

                {/* Model */}
                <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-1">Model Name</label>
                    <input
                        type="text"
                        value={settings.llm_model}
                        onChange={e => setSettings({ ...settings, llm_model: e.target.value })}
                        className="w-full border border-neutral-300 rounded-lg px-3 py-2 font-mono text-sm"
                    />
                </div>

                {/* System Prompt */}
                <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-1">System Prompt</label>
                    <textarea
                        value={settings.system_prompt}
                        onChange={e => setSettings({ ...settings, system_prompt: e.target.value })}
                        className="w-full border border-neutral-300 rounded-lg px-3 py-2 h-40 font-mono text-sm leading-relaxed"
                    />
                    <p className="text-xs text-neutral-500 mt-1">
                        Instructions for audio summarization. Must instruct to return JSON with 'summary', 'key_points', 'chords'.
                    </p>
                </div>

                <div className="pt-4 border-t border-neutral-100 flex justify-end">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 bg-neutral-900 text-white px-6 py-2.5 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50"
                    >
                        {saving ? "Saving..." : <><Save className="w-4 h-4" /> Save Settings</>}
                    </button>
                </div>
            </div>
        </div>
    )
}
