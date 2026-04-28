import { useState, useRef, useCallback } from 'react'
import axios from 'axios'

function Spinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-zinc-400"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}

function UploadIcon() {
  return (
    <svg className="w-8 h-8 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
      />
    </svg>
  )
}

export default function App() {
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return
    setImage(file)
    setResult(null)
    setError(null)
    setPreview(URL.createObjectURL(file))
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }, [handleFile])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragging(false)
  }, [])

  const handleInputChange = useCallback((e) => {
    handleFile(e.target.files[0])
  }, [handleFile])

  const checkVibe = async () => {
    if (!image) return
    setLoading(true)
    setError(null)
    setResult(null)

    const form = new FormData()
    form.append('file', image)

    try {
      const { data } = await axios.post('http://localhost:8000/predict', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(data)
    } catch {
      setError('Could not reach the server. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setImage(null)
    setPreview(null)
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16 bg-[#09090b]">
      <div className="w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-10">
          <p className="text-xs font-medium tracking-[0.2em] uppercase text-zinc-500 mb-3">
            AI Fashion Analysis
          </p>
          <h1 className="text-3xl font-semibold text-zinc-100 tracking-tight">
            Style Vibe Classifier
          </h1>
        </div>

        {/* Card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl shadow-black/50">

          {/* Upload zone */}
          <div
            onClick={() => !preview && inputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={[
              'relative rounded-xl border-2 border-dashed transition-all duration-200 overflow-hidden',
              preview
                ? 'border-zinc-700 cursor-default'
                : 'cursor-pointer hover:border-zinc-500 hover:bg-zinc-800/50',
              dragging
                ? 'border-violet-500 bg-violet-500/5'
                : 'border-zinc-700',
            ].join(' ')}
          >
            {preview ? (
              <div className="relative">
                <img
                  src={preview}
                  alt="Outfit preview"
                  className="w-full max-h-80 object-cover rounded-xl"
                />
                <button
                  onClick={(e) => { e.stopPropagation(); reset() }}
                  className="absolute top-2 right-2 bg-zinc-900/80 backdrop-blur-sm border border-zinc-700 text-zinc-400 hover:text-zinc-100 rounded-full w-7 h-7 flex items-center justify-center text-sm transition-colors"
                  title="Remove"
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center gap-3 py-14 px-6 text-center">
                <UploadIcon />
                <div>
                  <p className="text-sm font-medium text-zinc-300">Drop an outfit photo here</p>
                  <p className="text-xs text-zinc-600 mt-1">or click to browse · JPG, PNG, WEBP</p>
                </div>
              </div>
            )}
          </div>

          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            onChange={handleInputChange}
            className="hidden"
          />

          {/* Check Vibe button */}
          <button
            onClick={checkVibe}
            disabled={!image || loading}
            className={[
              'mt-4 w-full py-3 rounded-xl text-sm font-medium tracking-wide transition-all duration-200 flex items-center justify-center gap-2',
              image && !loading
                ? 'bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-900/30'
                : 'bg-zinc-800 text-zinc-600 cursor-not-allowed',
            ].join(' ')}
          >
            {loading ? (
              <>
                <Spinner />
                <span>Analyzing…</span>
              </>
            ) : (
              'Check Vibe'
            )}
          </button>

          {/* Result */}
          {result && (
            <div className="mt-4 animate-slide-up">
              <div className="bg-zinc-800/60 border border-zinc-700/60 rounded-xl px-5 py-4 flex items-center justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-widest text-zinc-500 mb-0.5">
                    Aesthetic
                  </p>
                  <p className="text-lg font-semibold text-zinc-100 leading-tight">
                    {result.vibe}
                  </p>
                </div>
                <div className="flex-shrink-0 text-center">
                  <div className="w-16 h-16 rounded-full border-2 border-violet-500/60 bg-violet-500/10 flex items-center justify-center">
                    <span className="text-lg font-bold text-violet-300">
                      {Math.round(result.confidence)}
                      <span className="text-xs font-normal">%</span>
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-600 mt-1 tracking-wide">confidence</p>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 animate-fade-in bg-red-950/40 border border-red-900/50 rounded-xl px-4 py-3">
              <p className="text-xs text-red-400 text-center">{error}</p>
            </div>
          )}
        </div>

        <p className="text-center text-zinc-700 text-xs mt-6">
          Powered by a custom ResNet classifier
        </p>
      </div>
    </div>
  )
}
