import { useState, useRef, useCallback } from 'react'
import axios from 'axios'
import WebcamCapture from './components/WebcamCapture'

// ─── Recommendation data ───────────────────────────────────────────────────────
const RECS = {
  Athleisure: {
    fashion: ['Ribbed Sports Set', 'Oversized Track Jacket', 'Seamless Leggings'],
    decor: ['Minimalist Gym Corner', 'Storage Ottoman', 'Modern Yoga Mat'],
    fashionGrads: ['from-sky-900 to-zinc-950', 'from-cyan-900 to-zinc-950', 'from-teal-900 to-zinc-950'],
    decorGrads: ['from-slate-800 to-zinc-950', 'from-zinc-800 to-zinc-950', 'from-neutral-800 to-zinc-950'],
  },
  'Boho / Cottagecore': {
    fashion: ['Flowy Maxi Dress', 'Crochet Cardigan', 'Patchwork Tote Bag'],
    decor: ['Dried Flower Arrangement', 'Rattan Bookshelf', 'Linen Throw Pillow'],
    fashionGrads: ['from-amber-900 to-stone-950', 'from-yellow-900 to-stone-950', 'from-orange-900 to-stone-950'],
    decorGrads: ['from-amber-800 to-stone-950', 'from-yellow-800 to-stone-950', 'from-lime-900 to-stone-950'],
  },
  'Business Casual': {
    fashion: ['Tailored Chino Set', 'Crisp Button-Down', 'Leather Loafers'],
    decor: ['Walnut Desk Organizer', 'Linen Curtain Panels', 'Ceramic Table Lamp'],
    fashionGrads: ['from-stone-700 to-stone-950', 'from-slate-700 to-slate-950', 'from-neutral-700 to-neutral-950'],
    decorGrads: ['from-amber-900 to-stone-950', 'from-stone-700 to-stone-950', 'from-neutral-800 to-zinc-950'],
  },
  'Business Formal': {
    fashion: ['Wool Blazer', 'Pleated Dress Trousers', 'Oxford Block Heels'],
    decor: ['Mahogany Bookend Set', 'Marble Desk Clock', 'Leather Desk Pad'],
    fashionGrads: ['from-zinc-700 to-zinc-950', 'from-slate-800 to-slate-950', 'from-neutral-800 to-neutral-950'],
    decorGrads: ['from-stone-800 to-zinc-950', 'from-zinc-800 to-zinc-950', 'from-slate-800 to-zinc-950'],
  },
  'Casual Basics': {
    fashion: ['Classic White Tee', 'Raw Hem Jeans', 'Clean Canvas Sneakers'],
    decor: ['Minimalist Floating Shelf', 'Cotton Throw Blanket', 'Line-Art Print'],
    fashionGrads: ['from-zinc-600 to-zinc-900', 'from-stone-600 to-stone-900', 'from-slate-600 to-slate-900'],
    decorGrads: ['from-zinc-700 to-zinc-950', 'from-neutral-700 to-neutral-950', 'from-stone-700 to-stone-950'],
  },
  'Edgy / Alternative': {
    fashion: ['Moto Leather Jacket', 'Fishnet Layer Top', 'Platform Combat Boots'],
    decor: ['Industrial Pipe Shelving', 'Neon Sign Accent', 'Exposed Brick Canvas'],
    fashionGrads: ['from-red-950 to-zinc-950', 'from-fuchsia-950 to-zinc-950', 'from-purple-950 to-zinc-950'],
    decorGrads: ['from-red-900 to-zinc-950', 'from-violet-900 to-zinc-950', 'from-zinc-700 to-zinc-950'],
  },
  'Loungewear / Sleepwear': {
    fashion: ['Cloud Fleece Matching Set', 'Silk Pajama Pants', 'Knit Oversized Cardigan'],
    decor: ['Oversized Floor Pillow', 'Plush Faux-Fur Rug', 'Candle & Diffuser Set'],
    fashionGrads: ['from-rose-900 to-zinc-950', 'from-pink-900 to-zinc-950', 'from-fuchsia-900 to-zinc-950'],
    decorGrads: ['from-rose-900 to-zinc-950', 'from-pink-800 to-zinc-950', 'from-indigo-900 to-zinc-950'],
  },
  Streetwear: {
    fashion: ['Graphic Drop-Shoulder Tee', 'Utility Cargo Pants', 'Chunky Dad Sneakers'],
    decor: ['Graffiti Canvas Art Print', 'LED Light Strip', 'Vinyl Record Display'],
    fashionGrads: ['from-violet-900 to-zinc-950', 'from-indigo-900 to-zinc-950', 'from-blue-900 to-zinc-950'],
    decorGrads: ['from-purple-900 to-zinc-950', 'from-blue-900 to-zinc-950', 'from-indigo-900 to-zinc-950'],
  },
  'Traditional / Ethnic Wear': {
    fashion: ['Embroidered Kurta Set', 'Silk Dupatta', 'Hand-Crafted Juttis'],
    decor: ['Block Print Tapestry', 'Brass Decorative Vase', 'Hand-Woven Dhurrie Rug'],
    fashionGrads: ['from-amber-800 to-orange-950', 'from-red-800 to-rose-950', 'from-yellow-800 to-amber-950'],
    decorGrads: ['from-amber-900 to-orange-950', 'from-red-900 to-rose-950', 'from-yellow-900 to-amber-950'],
  },
}

const FALLBACK_RECS = {
  fashion: ['Signature Top', 'Key Bottoms', 'Statement Accessory'],
  decor: ['Accent Piece', 'Functional Decor', 'Statement Item'],
  fashionGrads: ['from-zinc-800 to-zinc-950', 'from-zinc-700 to-zinc-950', 'from-zinc-800 to-zinc-950'],
  decorGrads: ['from-zinc-800 to-zinc-950', 'from-zinc-700 to-zinc-950', 'from-zinc-800 to-zinc-950'],
}

// ─── Vault helpers ─────────────────────────────────────────────────────────────
const VAULT_KEY = 'style-vibe-vault'
const loadVault = () => {
  try { return JSON.parse(localStorage.getItem(VAULT_KEY) ?? '[]') }
  catch { return [] }
}
const persistVault = (v) => localStorage.setItem(VAULT_KEY, JSON.stringify(v))

// ─── Sub-components ────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

function VibeResult({ result }) {
  const topK = result.top_k ?? [{ vibe: result.vibe, confidence: result.confidence }]
  return (
    <div className="animate-slide-up bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
      <div className="flex items-start justify-between mb-5">
        <div>
          <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1">Detected Aesthetic</p>
          <p className="text-2xl font-bold text-zinc-100 leading-tight">{result.vibe}</p>
        </div>
        <div className="flex-shrink-0 w-16 h-16 rounded-full border-2 border-orange-500/70 bg-orange-500/10 flex flex-col items-center justify-center">
          <span className="text-lg font-bold text-orange-400 leading-none">
            {Math.round(result.confidence)}
            <span className="text-xs font-normal">%</span>
          </span>
          <span className="text-[9px] text-orange-500/60 tracking-wide">match</span>
        </div>
      </div>

      {topK.length > 1 && (
        <div className="space-y-2.5 pt-4 border-t border-zinc-800">
          <p className="text-[10px] uppercase tracking-widest text-zinc-600 mb-3">Top Predictions</p>
          {topK.map((item, i) => (
            <div key={item.vibe} className="flex items-center gap-3">
              <span className="text-[10px] text-zinc-600 w-3 tabular-nums">{i + 1}</span>
              <div className="flex-1 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${i === 0 ? 'bg-orange-500' : 'bg-zinc-600'}`}
                  style={{ width: `${item.confidence}%` }}
                />
              </div>
              <span className="text-xs text-zinc-400 w-32 truncate">{item.vibe}</span>
              <span className="text-xs text-zinc-600 w-9 text-right tabular-nums">{item.confidence}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function RecCard({ title, gradient }) {
  return (
    <div className="rounded-xl overflow-hidden border border-zinc-800 hover:border-orange-500/30 transition-all duration-200 group cursor-pointer">
      <div className={`h-32 bg-gradient-to-br ${gradient} relative`}>
        <div className="absolute inset-0 flex items-center justify-center opacity-20">
          <div className="w-10 h-10 rounded-full border border-white/30" />
        </div>
      </div>
      <div className="px-3 py-2.5 bg-zinc-900/90">
        <p className="text-xs font-medium text-zinc-300 truncate leading-tight">{title}</p>
        <p className="text-[10px] text-zinc-600 mt-0.5 group-hover:text-orange-500/60 transition-colors">View item →</p>
      </div>
    </div>
  )
}

function Recommendations({ vibe }) {
  const rec = RECS[vibe] ?? FALLBACK_RECS
  return (
    <div className="mt-6 animate-slide-up">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-[10px] uppercase tracking-widest text-zinc-500 mb-3 flex items-center gap-2">
            <span className="w-1 h-3 bg-orange-500 rounded-full" />
            Fashion Picks
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {rec.fashion.map((title, i) => (
              <RecCard key={title} title={title} gradient={rec.fashionGrads[i]} />
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-[10px] uppercase tracking-widest text-zinc-500 mb-3 flex items-center gap-2">
            <span className="w-1 h-3 bg-orange-500/50 rounded-full" />
            Room Decor
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {rec.decor.map((title, i) => (
              <RecCard key={title} title={title} gradient={rec.decorGrads[i]} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function VaultGallery({ vault, onRemove }) {
  if (vault.length === 0) return null
  return (
    <div className="mt-12">
      <div className="flex items-center gap-3 mb-4">
        <svg className="w-4 h-4 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
          <path fillRule="evenodd" d="M6.32 2.577a49.255 49.255 0 0111.36 0c1.497.174 2.57 1.46 2.57 2.93V21a.75.75 0 01-1.085.67L12 18.089l-7.165 3.583A.75.75 0 013.75 21V5.507c0-1.47 1.073-2.756 2.57-2.93z" clipRule="evenodd" />
        </svg>
        <h2 className="text-sm font-semibold text-zinc-100">My Vault</h2>
        <span className="text-xs text-zinc-600">({vault.length} saved)</span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {vault.map((item) => (
          <div
            key={item.id}
            className="group relative rounded-xl overflow-hidden border border-zinc-800 hover:border-zinc-700 transition-colors"
          >
            <img
              src={item.preview}
              alt={item.vibe}
              className="w-full aspect-square object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950/95 via-zinc-950/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-2">
              <button
                onClick={() => onRemove(item.id)}
                className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center bg-zinc-900/90 border border-zinc-700 text-zinc-500 hover:text-red-400 hover:border-red-800 rounded-lg transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="px-2.5 py-2 bg-zinc-900 border-t border-zinc-800">
              <p className="text-[11px] font-medium text-zinc-300 truncate">{item.vibe}</p>
              <p className="text-[10px] text-orange-500/60">{item.confidence}% match</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState('upload')
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [webcamOpen, setWebcamOpen] = useState(false)
  const [vault, setVault] = useState(loadVault)
  const [savedToVault, setSavedToVault] = useState(false)
  const inputRef = useRef(null)

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return
    setImage(file)
    setResult(null)
    setError(null)
    setSavedToVault(false)
    setPreview(URL.createObjectURL(file))
  }, [])

  const handleWebcamCapture = useCallback((file, dataUrl) => {
    setImage(file)
    setResult(null)
    setError(null)
    setSavedToVault(false)
    setPreview(dataUrl)
    setWebcamOpen(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }, [handleFile])

  const checkVibe = async () => {
    if (!image) return
    setLoading(true)
    setError(null)
    setResult(null)
    setSavedToVault(false)
    const form = new FormData()
    form.append('file', image)
    try {
      const { data } = await axios.post('http://localhost:8000/predict', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(data)
    } catch {
      setError('Could not reach the server. Make sure the backend is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  const saveToVault = () => {
    if (!result || !preview || savedToVault) return
    const entry = {
      id: Date.now(),
      preview,
      vibe: result.vibe,
      confidence: result.confidence,
      timestamp: new Date().toISOString(),
    }
    const updated = [entry, ...vault]
    setVault(updated)
    persistVault(updated)
    setSavedToVault(true)
  }

  const removeFromVault = (id) => {
    const updated = vault.filter((v) => v.id !== id)
    setVault(updated)
    persistVault(updated)
  }

  const reset = () => {
    setImage(null)
    setPreview(null)
    setResult(null)
    setError(null)
    setSavedToVault(false)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="min-h-screen bg-[#09090b] px-4 py-12 md:py-16">
      <div className="max-w-4xl mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <p className="text-[10px] font-bold tracking-[0.3em] uppercase text-orange-500 mb-3">
            AI Fashion Analysis
          </p>
          <h1 className="text-3xl md:text-4xl font-bold text-zinc-100 tracking-tight">
            Style Vibe Classifier
          </h1>
          <p className="text-sm text-zinc-500 mt-2 max-w-sm mx-auto">
            Upload a photo or snap your outfit — we'll identify its aesthetic in seconds.
          </p>
        </div>

        {/* Main grid: Input (left) | Results (right) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 items-start">

          {/* ── Input panel ── */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 shadow-2xl shadow-black/50">

            {/* Input method tabs */}
            <div className="flex gap-1 mb-4 bg-zinc-800/60 rounded-xl p-1">
              <button
                onClick={() => setTab('upload')}
                className={[
                  'flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all duration-150',
                  tab === 'upload'
                    ? 'bg-zinc-700 text-zinc-100 shadow'
                    : 'text-zinc-500 hover:text-zinc-300',
                ].join(' ')}
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                Upload Photo
              </button>
              <button
                onClick={() => setTab('webcam')}
                className={[
                  'flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all duration-150',
                  tab === 'webcam'
                    ? 'bg-zinc-700 text-zinc-100 shadow'
                    : 'text-zinc-500 hover:text-zinc-300',
                ].join(' ')}
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z" />
                </svg>
                Webcam
              </button>
            </div>

            {/* Preview or input zone */}
            {preview ? (
              /* Shared preview: shown regardless of tab */
              <div
                className="relative rounded-xl overflow-hidden border border-zinc-700 mb-4"
              >
                <img
                  src={preview}
                  alt="Outfit preview"
                  className="w-full max-h-72 object-contain bg-zinc-950"
                />
                <button
                  onClick={reset}
                  className="absolute top-2 right-2 bg-zinc-900/80 backdrop-blur-sm border border-zinc-700 text-zinc-400 hover:text-zinc-100 rounded-full w-7 h-7 flex items-center justify-center text-xs transition-colors"
                >
                  ✕
                </button>
              </div>
            ) : tab === 'upload' ? (
              /* Drop zone */
              <div
                onClick={() => inputRef.current?.click()}
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                className={[
                  'rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer mb-4',
                  dragging
                    ? 'border-orange-500 bg-orange-500/5'
                    : 'border-zinc-700 hover:border-orange-500/40 hover:bg-zinc-800/30',
                ].join(' ')}
              >
                <div className="flex flex-col items-center justify-center gap-3 py-14 px-6 text-center">
                  <div className="w-14 h-14 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center">
                    <svg className="w-6 h-6 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-zinc-300">Drop an outfit photo here</p>
                    <p className="text-xs text-zinc-600 mt-1">or click to browse · JPG, PNG, WEBP</p>
                  </div>
                </div>
              </div>
            ) : (
              /* Webcam prompt */
              <div className="rounded-xl border-2 border-dashed border-zinc-700 flex flex-col items-center justify-center gap-4 py-14 px-6 text-center mb-4">
                <div className="w-14 h-14 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center">
                  <svg className="w-6 h-6 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-zinc-300">Snap your outfit</p>
                  <p className="text-xs text-zinc-600 mt-1">Use your camera for a live capture</p>
                </div>
                <button
                  onClick={() => setWebcamOpen(true)}
                  className="px-5 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600 text-zinc-200 rounded-xl text-xs font-medium transition-colors"
                >
                  Open Camera
                </button>
              </div>
            )}

            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              onChange={(e) => handleFile(e.target.files[0])}
              className="hidden"
            />

            {/* Webcam retake button */}
            {preview && tab === 'webcam' && (
              <button
                onClick={() => { reset(); setWebcamOpen(true) }}
                className="w-full mb-3 py-2 rounded-xl text-xs font-medium border border-zinc-700 text-zinc-500 hover:text-zinc-300 hover:border-zinc-600 transition-colors"
              >
                Retake Photo
              </button>
            )}

            {/* Analyze button */}
            <button
              onClick={checkVibe}
              disabled={!image || loading}
              className={[
                'w-full py-3 rounded-xl text-sm font-semibold tracking-wide transition-all duration-200 flex items-center justify-center gap-2',
                image && !loading
                  ? 'bg-orange-500 hover:bg-orange-400 text-white shadow-lg shadow-orange-900/30'
                  : 'bg-zinc-800 text-zinc-600 cursor-not-allowed',
              ].join(' ')}
            >
              {loading ? (
                <><Spinner /><span>Analyzing…</span></>
              ) : (
                'Check Vibe →'
              )}
            </button>

            {error && (
              <div className="mt-3 bg-red-950/40 border border-red-900/50 rounded-xl px-4 py-3 animate-fade-in">
                <p className="text-xs text-red-400 text-center">{error}</p>
              </div>
            )}
          </div>

          {/* ── Results panel ── */}
          <div>
            {result ? (
              <div className="space-y-3">
                <VibeResult result={result} />
                <button
                  onClick={saveToVault}
                  disabled={savedToVault}
                  className={[
                    'w-full py-2.5 rounded-xl text-sm font-medium transition-all duration-200 flex items-center justify-center gap-2 border',
                    savedToVault
                      ? 'border-orange-500/40 bg-orange-500/10 text-orange-400 cursor-default'
                      : 'border-zinc-700 bg-zinc-900 hover:border-orange-500/50 hover:bg-orange-500/5 text-zinc-300 hover:text-orange-300',
                  ].join(' ')}
                >
                  <svg
                    className="w-4 h-4"
                    fill={savedToVault ? 'currentColor' : 'none'}
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z"
                    />
                  </svg>
                  {savedToVault ? 'Saved to My Vault ✓' : 'Save to My Vault'}
                </button>
              </div>
            ) : (
              <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-6 flex flex-col items-center justify-center text-center gap-3 min-h-48">
                <div className="w-12 h-12 rounded-full bg-zinc-800/80 border border-zinc-700/50 flex items-center justify-center">
                  <svg className="w-5 h-5 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-zinc-500 font-medium">Your vibe analysis will appear here</p>
                  <p className="text-xs text-zinc-700 mt-1">Upload or capture an outfit to begin</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Recommendations */}
        {result && <Recommendations vibe={result.vibe} />}

        {/* Vault */}
        <VaultGallery vault={vault} onRemove={removeFromVault} />

        <p className="text-center text-zinc-700 text-xs mt-12">
          Powered by a custom ResNet-50 classifier
        </p>
      </div>

      {webcamOpen && (
        <WebcamCapture
          onCapture={handleWebcamCapture}
          onClose={() => setWebcamOpen(false)}
        />
      )}
    </div>
  )
}
