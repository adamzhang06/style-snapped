import { useState, useRef, useCallback, useEffect } from 'react'
import axios from 'axios'

const VIBE_SUGGESTIONS = {
  Techwear: {
    description: 'Sharp, layered silhouettes with street-ready utility and modern edge.',
    outfits: [
      'Matte nylon cargo jacket',
      'Technical hooded layering tee',
      'Black tapered utility pants',
      'High-top trainer boots',
    ],
    decor: [
      'Industrial metal shelving',
      'Monochrome accent pillows',
      'Concrete + matte black lighting',
      'Minimal storage crates',
    ],
  },
  Streetwear: {
    description: 'Casual confidence with bold branding, relaxed cuts, and playful attitude.',
    outfits: [
      'Graphic oversized hoodie',
      'Wide-leg denim pants',
      'Chunky white sneakers',
      'Bucket hat or snapback',
    ],
    decor: [
      'Neon wall art',
      'Low-profile lounge sofa',
      'Layered street posters',
      'Textured rugs and throw blankets',
    ],
  },
  'Dark Academia': {
    description: 'Warm neutrals, vintage books, and quiet elegance for moody study vibes.',
    outfits: [
      'Tweed blazer',
      'Soft wool turtleneck',
      'Corduroy skirt or trousers',
      'Leather loafers',
    ],
    decor: [
      'Antique brass desk lamp',
      'Leather-bound books',
      'Velvet armchair',
      'Earth-tone tapestry',
    ],
  },
  Cottagecore: {
    description: 'Soft florals, cozy textures, and handcrafted charm for pastoral comfort.',
    outfits: [
      'Tiered floral dress',
      'Woven straw hat',
      'Knit cardigan',
      'Rattan crossbody bag',
    ],
    decor: [
      'Dried flower bundle',
      'Pastel throw pillows',
      'Natural wood side table',
      'Botanical wall prints',
    ],
  },
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-[#db8146]"
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
    <svg className="w-8 h-8 text-[#8e5e43]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
  const [username, setUsername] = useState('')
  const [signedIn, setSignedIn] = useState(false)
  const [board, setBoard] = useState([])
  const [activeTab, setActiveTab] = useState('home')
  const inputRef = useRef(null)

  useEffect(() => {
    const savedBoard = localStorage.getItem('vibeBoard')
    const savedUser = localStorage.getItem('styleUser')
    if (savedBoard) setBoard(JSON.parse(savedBoard))
    if (savedUser) {
      setUsername(savedUser)
      setSignedIn(true)
    }
  }, [])

  useEffect(() => {
    localStorage.setItem('vibeBoard', JSON.stringify(board))
  }, [board])

  useEffect(() => {
    if (signedIn && username.trim()) {
      localStorage.setItem('styleUser', username.trim())
    } else {
      localStorage.removeItem('styleUser')
    }
  }, [signedIn, username])

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

  const signIn = () => {
    if (!username.trim()) return
    setSignedIn(true)
  }

  const signOut = () => {
    setSignedIn(false)
    setUsername('')
    setBoard([])
  }

  const saveToBoard = () => {
    if (!result) return
    const entry = {
      id:
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      vibe: result.vibe,
      confidence: result.confidence,
      date: new Date().toISOString(),
      preview,
      outfit: VIBE_SUGGESTIONS[result.vibe]?.outfits[0] ?? 'Outfit idea',
    }
    setBoard((current) => [entry, ...current])
  }

  const vibeInfo = result ? VIBE_SUGGESTIONS[result.vibe] : null

  return (
    <div className="min-h-screen bg-[#f8f8f8] text-slate-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-col gap-4 rounded-[32px] border border-[#e4d7ce] bg-white/90 p-6 shadow-xl shadow-[#cdb097]/20 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[#88614f] mb-2">Style Social</p>
            <h1 className="text-3xl font-semibold tracking-tight text-[#2b2b2b]">StyleSnapped</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Upload any outfit photo and discover its aesthetic, curated outfit ideas, room decor inspiration, and a Pinterest-style board for saving your favorite looks.
            </p>
          </div>

          <div className="flex flex-col gap-3 rounded-3xl border border-[#fde8df] bg-[#fff0e6] p-4 text-sm text-slate-800 shadow-sm sm:w-[320px]">
            {signedIn ? (
              <>
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-2xl bg-[#db8146] grid place-items-center text-xl font-bold text-white">{username[0]?.toUpperCase() ?? 'S'}</div>
                  <div>
                    <p className="font-semibold">{username}</p>
                    <p className="text-xs text-slate-600">Signed in to save boards</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-semibold text-slate-700">
                  <span>{board.length} Saves</span>
                  <span>{result ? result.vibe : 'Discover'}</span>
                  <span>Profile</span>
                </div>
                <button
                  onClick={signOut}
                  className="mt-1 rounded-2xl bg-[#db8146] px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-[#c77d50]/30 transition hover:bg-[#c36734]"
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <p className="font-semibold">Welcome back!</p>
                <p className="text-xs text-slate-600">Sign in to save looks and pin your aesthetic boards.</p>
                <div className="grid gap-3">
                  <input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Choose a display name"
                    className="rounded-2xl border border-[#e4d7ce] bg-white px-4 py-3 text-sm outline-none transition focus:border-[#db8146]"
                  />
                  <button
                    onClick={signIn}
                    className="rounded-2xl bg-[#db8146] px-4 py-3 text-sm font-semibold text-white shadow-sm shadow-[#c77d50]/30 transition hover:bg-[#c36734]"
                  >
                    Sign in
                  </button>
                </div>
              </>
            )}
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1.5fr_0.9fr]">
          <main className="space-y-6">
            {/* Tab Navigation */}
            <div className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-1 shadow-lg shadow-[#cdb097]/10">
              <div className="flex">
                <button
                  onClick={() => setActiveTab('home')}
                  className={[
                    'flex-1 rounded-[24px] px-6 py-3 text-sm font-semibold transition',
                    activeTab === 'home' ? 'bg-[#db8146] text-white shadow-lg shadow-[#c77d50]/20' : 'text-slate-600 hover:text-slate-900',
                  ].join(' ')}
                >
                  🏠 Home
                </button>
                <button
                  onClick={() => setActiveTab('board')}
                  className={[
                    'flex-1 rounded-[24px] px-6 py-3 text-sm font-semibold transition',
                    activeTab === 'board' ? 'bg-[#db8146] text-white shadow-lg shadow-[#c77d50]/20' : 'text-slate-600 hover:text-slate-900',
                  ].join(' ')}
                >
                  📌 My Board ({board.length})
                </button>
              </div>
            </div>

            {activeTab === 'home' && (
              <>
                <section className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-6 shadow-lg shadow-[#cdb097]/10">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.35em] text-[#88614f]">Outfit analysis</p>
                      <h2 className="text-2xl font-semibold text-slate-900">Upload your look</h2>
                    </div>
                    <div className="rounded-3xl bg-[#fff6ed] px-4 py-3 text-sm font-medium text-[#8e5e43] shadow-sm">
                      Trending: <span className="font-semibold">Cottagecore refresh</span>
                    </div>
                  </div>

                  <div
                    onClick={() => !preview && inputRef.current?.click()}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    className={[
                      'mt-6 rounded-[28px] border-2 border-dashed transition-all duration-200 overflow-hidden',
                      preview ? 'border-slate-300 bg-slate-100 cursor-default' : 'cursor-pointer hover:border-[#db8146] hover:bg-[#fff2e8]',
                      dragging ? 'border-[#db8146] bg-[#ffe7d9]' : 'border-[#d9d3cb]',
                    ].join(' ')}
                  >
                    {preview ? (
                      <div className="relative">
                        <img src={preview} alt="Outfit preview" className="w-full max-h-[420px] object-cover" />
                        <button
                          onClick={(e) => { e.stopPropagation(); reset() }}
                          className="absolute right-4 top-4 rounded-full bg-white/90 p-2 text-slate-700 shadow-md"
                          title="Remove"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <div className="flex min-h-[260px] flex-col items-center justify-center gap-3 p-8 text-center text-slate-600">
                        <UploadIcon />
                        <div>
                          <p className="text-base font-semibold text-slate-800">Drag & drop an outfit photo</p>
                          <p className="text-sm">or click anywhere to choose a file</p>
                        </div>
                        <p className="text-xs text-slate-400">Supports JPG, PNG, WEBP</p>
                      </div>
                    )}
                  </div>

                  <input ref={inputRef} type="file" accept="image/*" onChange={handleInputChange} className="hidden" />

                  <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <button
                      onClick={checkVibe}
                      disabled={!image || loading}
                      className={[
                        'inline-flex items-center justify-center rounded-2xl px-6 py-3 text-sm font-semibold tracking-wide transition',
                        image && !loading ? 'bg-[#db8146] text-white shadow-lg shadow-[#c77d50]/20 hover:bg-[#c66736]' : 'bg-slate-200 text-slate-400 cursor-not-allowed',
                      ].join(' ')}
                    >
                      {loading ? (
                        <>
                          <Spinner />
                          <span>Analyzing</span>
                        </>
                      ) : (
                        'Check vibe'
                      )}
                    </button>
                    <button
                      onClick={reset}
                      className="rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:border-[#db8146] hover:text-[#db8146]"
                    >
                      Reset
                    </button>
                  </div>

                  {error && (
                    <div className="mt-4 rounded-3xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                      {error}
                    </div>
                  )}
                </section>

                {result && (
                  <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
                    <div className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-6 shadow-lg shadow-[#cdb097]/10">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="text-sm uppercase tracking-[0.35em] text-[#88614f]">Result</p>
                          <h2 className="text-2xl font-semibold text-slate-900">{result.vibe}</h2>
                        </div>
                        <div className="rounded-3xl bg-[#fde8df] px-4 py-2 text-sm font-semibold text-[#8e5e43]">
                          {Math.round(result.confidence)}% match
                        </div>
                      </div>

                      <p className="mt-4 text-sm leading-7 text-slate-600">{vibeInfo?.description}</p>

                      <div className="mt-6 grid gap-4 sm:grid-cols-2">
                        <div className="rounded-3xl bg-[#fff4ec] p-5">
                          <p className="text-xs uppercase tracking-[0.35em] text-[#88614f]">🛍️ Outfit recommendations</p>
                          <ul className="mt-3 space-y-3 text-sm text-slate-700">
                            {vibeInfo?.outfits.map((item) => (
                              <li key={item} className="rounded-2xl bg-white p-3 shadow-sm shadow-[#d2beb1]/40">{item}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="rounded-3xl bg-[#fdf5ec] p-5">
                          <p className="text-xs uppercase tracking-[0.35em] text-[#88614f]">🛋️ Room decor suggestions</p>
                          <ul className="mt-3 space-y-3 text-sm text-slate-700">
                            {vibeInfo?.decor.map((item) => (
                              <li key={item} className="rounded-2xl bg-white p-3 shadow-sm shadow-[#d2beb1]/40">{item}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      <button
                        onClick={saveToBoard}
                        className="mt-6 inline-flex items-center justify-center rounded-2xl bg-[#db8146] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[#c77d50]/20 transition hover:bg-[#c66736]"
                      >
                        📌 Save to Pinterest board
                      </button>
                    </div>

                    <div className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-6 shadow-lg shadow-[#cdb097]/10">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm uppercase tracking-[0.35em] text-[#88614f]">Pinned board</p>
                          <h3 className="text-xl font-semibold text-slate-900">Saved looks</h3>
                        </div>
                        <span className="inline-flex rounded-full bg-[#fff0e6] px-3 py-1 text-xs font-semibold text-[#8e5e43]">{board.length} items</span>
                      </div>
                      <div className="mt-5 space-y-3">
                        {board.length === 0 ? (
                          <div className="rounded-3xl bg-[#faf5f1] p-4 text-sm text-slate-600">
                            Save your first look to build a personal mood board.
                          </div>
                        ) : (
                          board.slice(0, 4).map((item) => (
                            <div key={item.id} className="rounded-3xl border border-[#f1d7c3] bg-[#fff5ef] p-4">
                              <p className="font-semibold text-slate-900">{item.vibe}</p>
                              <p className="mt-1 text-sm text-slate-600">{item.outfit}</p>
                              <p className="mt-2 text-xs text-slate-500">Saved {new Date(item.date).toLocaleDateString()}</p>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </section>
                )}
              </>
            )}

            {activeTab === 'board' && (
              <section className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-6 shadow-lg shadow-[#cdb097]/10">
                <div className="flex items-center justify-between gap-3 mb-6">
                  <div>
                    <p className="text-sm uppercase tracking-[0.35em] text-[#88614f]">Your collection</p>
                    <h2 className="text-2xl font-semibold text-slate-900">Pinterest Board</h2>
                  </div>
                  <span className="inline-flex rounded-full bg-[#fff0e6] px-4 py-2 text-sm font-semibold text-[#8e5e43]">{board.length} saved looks</span>
                </div>

                {board.length === 0 ? (
                  <div className="rounded-3xl bg-[#faf5f1] p-8 text-center">
                    <p className="text-lg font-semibold text-slate-800 mb-2">No saved looks yet</p>
                    <p className="text-sm text-slate-600 mb-4">Upload an outfit and save your favorite aesthetic results to build your personal mood board.</p>
                    <button
                      onClick={() => setActiveTab('home')}
                      className="inline-flex items-center justify-center rounded-2xl bg-[#db8146] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[#c77d50]/20 transition hover:bg-[#c66736]"
                    >
                      Start analyzing →
                    </button>
                  </div>
                ) : (
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {board.map((item) => (
                      <div key={item.id} className="rounded-3xl border border-[#f1d7c3] bg-[#fff5ef] p-4 shadow-sm shadow-[#d2beb1]/40">
                        <div className="aspect-square rounded-2xl bg-slate-200 mb-3 overflow-hidden">
                          {item.preview && <img src={item.preview} alt={item.vibe} className="w-full h-full object-cover" />}
                        </div>
                        <p className="font-semibold text-slate-900">{item.vibe}</p>
                        <p className="mt-1 text-sm text-slate-600">{item.outfit}</p>
                        <p className="mt-2 text-xs text-slate-500">Saved {new Date(item.date).toLocaleDateString()}</p>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}
          </main>

          <aside className="space-y-6">
            <div className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-6 shadow-lg shadow-[#cdb097]/10">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm uppercase tracking-[0.35em] text-[#88614f]">Social hub</p>
                  <h2 className="text-xl font-semibold text-slate-900">Community board</h2>
                </div>
                <div className="rounded-3xl bg-[#fff4ec] px-3 py-1 text-xs font-semibold text-[#8e5e43]">Live</div>
              </div>
              <div className="mt-5 space-y-4">
                <div className="rounded-3xl bg-[#fdf5ef] p-4">
                  <p className="font-semibold text-slate-900">@alexa.urban</p>
                  <p className="mt-2 text-sm text-slate-600">Pinned a moody Dark Academia study board with leather accents.</p>
                </div>
                <div className="rounded-3xl bg-[#f7f1ec] p-4">
                  <p className="font-semibold text-slate-900">@noah.street</p>
                  <p className="mt-2 text-sm text-slate-600">Added a new Streetwear look with bold sneakers and graphic layers.</p>
                </div>
                <div className="rounded-3xl bg-[#faf7f3] p-4">
                  <p className="font-semibold text-slate-900">@cottage.day</p>
                  <p className="mt-2 text-sm text-slate-600">Saved floral décor suggestions for a sunlit bedroom.</p>
                </div>
              </div>
            </div>

            <div className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-6 shadow-lg shadow-[#cdb097]/10">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm uppercase tracking-[0.35em] text-[#88614f]">Your profile</p>
                  <h3 className="text-xl font-semibold text-slate-900">{signedIn ? username : 'Guest explorer'}</h3>
                </div>
                <span className="rounded-full bg-[#e9d0c1] px-3 py-1 text-xs font-semibold text-[#7f553f]">{signedIn ? 'Signed in' : 'Guest'}</span>
              </div>
              <div className="mt-5 space-y-3 text-sm text-slate-600">
                <p>Sign in to save presets, track boards, and share your aesthetic feed.</p>
                <div className="rounded-3xl bg-[#fff5ef] p-4 text-sm text-slate-700">
                  <p className="font-semibold">Features live now</p>
                  <ul className="mt-2 space-y-1">
                    <li>• Outfit recommendations</li>
                    <li>• Room decor inspiration</li>
                    <li>• Pinterest-style saved board</li>
                  </ul>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
