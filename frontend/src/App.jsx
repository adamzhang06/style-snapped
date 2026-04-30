import { useState, useRef, useCallback, useEffect } from 'react'
import axios from 'axios'
import WebcamCapture from './components/WebcamCapture'

const VIBE_SUGGESTIONS = {
  Athleisure: {
    description: 'Performance meets everyday comfort — clean lines, stretch fabrics, and effortless movement.',
    outfits: [
      'High-waist performance leggings',
      'Moisture-wicking zip-up hoodie',
      'Athletic crop top',
      'Sleek running shoes',
      'Track jacket + biker shorts',
      'Ribbed sports bra + wide-leg joggers',
      'Tennis-style skirt + fitted tank',
      'Seamless long-sleeve + cycling shorts',
    ],
    decor: [
      'Wall-mounted yoga mat holder',
      'Minimalist floor-length mirror',
      'Clean white floating shelves',
      'Motivational typographic wall print',
      'Woven basket for resistance bands',
      'Indoor trailing pothos plant',
      'Sleek LED strip accent lighting',
      'Neutral linen throw for cool-downs',
    ],
  },
  'Boho / Cottagecore': {
    description: 'Soft florals, cozy textures, and handcrafted charm for free-spirited pastoral comfort.',
    outfits: [
      'Tiered floral midi dress',
      'Woven straw hat',
      'Oversized knit cardigan',
      'Rattan crossbody bag',
      'Lace-trim cotton blouse',
      'Wide-leg linen trousers',
      'Embroidered peasant top',
      'Strappy leather sandals',
    ],
    decor: [
      'Dried wildflower bundle',
      'Pastel linen throw pillows',
      'Natural wood side table',
      'Botanical wall prints',
      'Macramé wall hanging',
      'Rattan accent chair',
      'Wicker basket storage',
      'Gauze curtains in ivory',
    ],
  },
  'Boho Chic': {
    description: 'Effortless layers, earthy tones, and free-spirited details with an elevated edge.',
    outfits: [
      'Flowy maxi skirt + fitted tank',
      'Fringed suede jacket',
      'Stacked coin necklaces',
      'Block-print wrap dress',
      'Crochet cover-up + wide-leg pants',
      'Platform espadrilles',
      'Embroidered denim jacket',
      'Leather belt with turquoise buckle',
    ],
    decor: [
      'Layered kilim rug',
      'Hammered brass candle holders',
      'Trailing ivy in terracotta pot',
      'Woven wall tapestry',
      'Low-slung floor cushions',
      'Rattan pendant lamp',
      'Gallery wall of travel photos',
      'Handmade ceramic vases',
    ],
  },
  'Business Casual': {
    description: 'Polished without being stiff — smart pieces that move from desk to dinner with ease.',
    outfits: [
      'Tailored chinos + crisp button-down',
      'Unstructured blazer over a tee',
      'Midi wrap skirt + silk blouse',
      'Clean leather loafers',
      'Slim-fit trousers + knit polo',
      'Structured leather tote',
      'Straight-cut jeans + relaxed blazer',
      'Simple silk blouse + cigarette trousers',
    ],
    decor: [
      'Clean desk organizer set',
      'Muted geometric area rug',
      'Structured hardback bookshelf',
      'Linen Roman blind in warm white',
      'Minimalist brass desk lamp',
      'Framed abstract line art',
      'Leather catch-all tray',
      'Potted fiddle-leaf fig',
    ],
  },
  'Business Formal': {
    description: 'Authoritative, refined, and impeccably tailored — dressing for the room you want to own.',
    outfits: [
      'Tailored suit in navy or charcoal',
      'Crisp white dress shirt + silk tie',
      'Sheath dress + structured blazer',
      'Pointed-toe leather heels',
      'Silk blouse + high-waist wide-leg trousers',
      'Structured leather briefcase',
      'Polished Oxford shoes',
      'Wool overcoat in camel or black',
    ],
    decor: [
      'Dark walnut executive desk',
      'Tufted leather desk chair',
      'Framed credential or diploma display',
      'Brushed brass accent accessories',
      'Architect-style reading lamp',
      'Law-book or hardback styling shelf',
      'Marble desk accessories set',
      'Muted corporate canvas art',
    ],
  },
  'Casual Basics': {
    description: 'The quiet confidence of perfectly fitted, fuss-free wardrobe staples done right.',
    outfits: [
      'Classic white tee + straight-leg jeans',
      'Relaxed crew-neck sweatshirt',
      'Chino shorts + clean canvas sneakers',
      'Quarter-zip pullover',
      'Straight-leg chinos + OCBD shirt',
      'Washed denim jacket + white tee',
      'Simple crewneck sweater + slim jeans',
      'Linen shirt + khaki joggers',
    ],
    decor: [
      'Chunky knit throw blanket',
      'Simple solid-oak floating shelf',
      'Warm-tone neutral rug',
      'Arc floor lamp with linen shade',
      'Linen duvet cover in off-white',
      'Minimal 3-photo gallery wall',
      'Cotton pillowcases in earth tones',
      'Small succulent arrangement',
    ],
  },
  'Edgy / Alternative': {
    description: 'Dark, deliberate, and unapologetically bold — fashion as attitude and armor.',
    outfits: [
      'Black moto jacket + vintage band tee',
      'Skinny black jeans + Chelsea boots',
      'Fishnet layering under a slip dress',
      'Studded statement belt',
      'Distressed denim jacket with patches',
      'Graphic oversized tee + cargo pants',
      'Platform lace-up boots',
      'Silver chain accessories',
    ],
    decor: [
      'Dark velvet accent cushions',
      'Neon sign in red or purple',
      'Vintage band or film poster',
      'Gothic taper candle holders',
      'Black steel pipe shelving',
      'Exposed Edison bulb pendant',
      'Abstract or skull canvas art',
      'Deep charcoal painted accent wall',
    ],
  },
  'Loungewear / Sleepwear': {
    description: 'Elevated comfort for doing nothing at peak softness — cozy is a whole aesthetic.',
    outfits: [
      'Matching ribbed lounge set',
      'Oversized fleece hoodie + sweatpants',
      'Satin sleep shorts + cami top',
      'Plush terry slide sandals',
      'Cropped sweatpants + cozy crewneck',
      'Bamboo pajama button set',
      'Fluffy zip-up robe',
      'Ribbed tank + wide-leg lounge pants',
    ],
    decor: [
      'Chunky knit bedroom throw',
      'Dimmer bedside touch lamp',
      'Scented candle tray arrangement',
      'Weighted blanket in warm grey',
      'High-pile shag bedside rug',
      'Blackout curtain panels',
      'Calming watercolor wall art',
      'Velvet drawer organizer',
    ],
  },
  Streetwear: {
    description: 'Casual confidence with bold branding, relaxed cuts, and drop-culture attitude.',
    outfits: [
      'Graphic oversized hoodie',
      'Wide-leg denim pants',
      'Chunky white sneakers',
      'Bucket hat or snapback',
      'Varsity bomber jacket',
      'Cargo pants + fitted cropped tee',
      'Bold color-block windbreaker',
      'Limited-edition collab kicks',
    ],
    decor: [
      'Neon wall art sign',
      'Low-profile modular lounge sofa',
      'Layered street art posters',
      'Textured area rug + oversized throw',
      'Acrylic sneaker display shelf',
      'Graffiti-style canvas print',
      'Cube shelving unit',
      'Oversized wall clock',
    ],
  },
  'Smart Casual / Office': {
    description: 'Sharp enough for the office, relaxed enough for after — versatile modern dressing.',
    outfits: [
      'Tailored blazer + dark jeans + loafers',
      'Smart chinos + Oxford shirt',
      'Knit polo + straight trousers',
      'Midi skirt + tucked-in blouse',
      'Structured tote + clean white sneakers',
      'Cashmere crewneck + slim chinos',
      'Fitted turtleneck + wide-leg trousers',
      'Relaxed linen suit set',
    ],
    decor: [
      'Warm-toned task lamp',
      'Linen pinboard with copper tacks',
      'Structured desk organizer',
      'Low-maintenance desk plant (ZZ plant)',
      'Framed architectural photo print',
      'Woven storage basket under desk',
      'Neutral grid rug',
      'Leather-bound journal + pen tray',
    ],
  },
  'Traditional / Ethnic Wear': {
    description: 'Heritage craftsmanship and vibrant textile traditions worn with cultural pride.',
    outfits: [
      'Embroidered kurta + churidar set',
      'Silk sari with gold border',
      'Salwar kameez in block-print cotton',
      'Intricately beaded statement jewelry',
      'Embellished juttis or kolhapuris',
      'Handwoven Banarasi dupatta',
      'Mirror-work skirt + fitted blouse',
      'Chikankari embroidered kurta',
    ],
    decor: [
      'Hand-painted ceramic vase collection',
      'Woven kilim or dhurrie rug',
      'Engraved brass decorative tray',
      'Block-printed cushion covers',
      'Carved sandalwood accent piece',
      'Clay pot + dried grass arrangement',
      'Embroidered wall hanging',
      'Jali-pattern lantern lamp',
    ],
  },
}

function pickRandom(arr, n) {
  const shuffled = [...arr].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, n)
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
  const [showWebcam, setShowWebcam] = useState(false)
  const [picks, setPicks] = useState(null)
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

  useEffect(() => {
    if (!result) { setPicks(null); return }
    const info = VIBE_SUGGESTIONS[result.vibe]
    if (!info) { setPicks(null); return }
    setPicks({
      outfits: pickRandom(info.outfits, 4),
      decor: pickRandom(info.decor, 4),
    })
  }, [result])

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

  const removeFromBoard = (id) => {
    setBoard((current) => current.filter((item) => item.id !== id))
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
      outfit: picks?.outfits[0] ?? VIBE_SUGGESTIONS[result.vibe]?.outfits[0] ?? 'Outfit idea',
    }
    setBoard((current) => [entry, ...current])
  }

  const vibeInfo = result ? VIBE_SUGGESTIONS[result.vibe] : null

  return (
    <div className="min-h-screen bg-[#f8f8f8] text-slate-900">
      {showWebcam && (
        <WebcamCapture
          onCapture={(file, imageSrc) => {
            setShowWebcam(false)
            setImage(file)
            setResult(null)
            setError(null)
            setPreview(imageSrc)
          }}
          onClose={() => setShowWebcam(false)}
        />
      )}
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
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    className={[
                      'mt-6 rounded-[28px] border-2 border-dashed transition-all duration-200 overflow-hidden',
                      preview ? 'border-slate-200 bg-slate-50 cursor-default' : 'cursor-pointer hover:border-[#db8146] hover:bg-[#fff2e8]',
                      dragging ? 'border-[#db8146] bg-[#ffe7d9]' : 'border-[#d9d3cb]',
                    ].join(' ')}
                    onClick={() => !preview && inputRef.current?.click()}
                  >
                    {preview ? (
                      <div className="relative flex items-center justify-center bg-[#faf8f6] min-h-[280px]">
                        <img
                          src={preview}
                          alt="Outfit preview"
                          className="max-w-full max-h-[520px] w-auto h-auto object-contain"
                          style={{ display: 'block' }}
                        />
                        <button
                          onClick={(e) => { e.stopPropagation(); reset() }}
                          className="absolute right-4 top-4 rounded-full bg-white/90 p-2 text-slate-700 shadow-md hover:bg-white transition"
                          title="Remove photo"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <div className="flex min-h-[260px] flex-col items-center justify-center gap-4 p-8 text-center text-slate-600">
                        <UploadIcon />
                        <div>
                          <p className="text-base font-semibold text-slate-800">Drag & drop an outfit photo</p>
                          <p className="text-sm">or click to choose a file</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-slate-400">or</span>
                          <button
                            onClick={(e) => { e.stopPropagation(); setShowWebcam(true) }}
                            className="inline-flex items-center gap-2 rounded-2xl border border-[#e5d6c6] bg-white px-4 py-2.5 text-sm font-semibold text-[#8e5e43] shadow-sm hover:border-[#db8146] hover:text-[#db8146] transition"
                          >
                            📷 Use Webcam
                          </button>
                        </div>
                        <p className="text-xs text-slate-400">Supports JPG, PNG, WEBP</p>
                      </div>
                    )}
                  </div>

                  <input ref={inputRef} type="file" accept="image/*" onChange={handleInputChange} className="hidden" />

                  <div className="mt-6 flex flex-wrap gap-3 items-center">
                    <button
                      onClick={checkVibe}
                      disabled={!image || loading}
                      className={[
                        'inline-flex items-center gap-2 justify-center rounded-2xl px-6 py-3 text-sm font-semibold tracking-wide transition',
                        image && !loading ? 'bg-[#db8146] text-white shadow-lg shadow-[#c77d50]/20 hover:bg-[#c66736]' : 'bg-slate-200 text-slate-400 cursor-not-allowed',
                      ].join(' ')}
                    >
                      {loading ? (
                        <>
                          <Spinner />
                          <span>Analyzing…</span>
                        </>
                      ) : (
                        'Check vibe'
                      )}
                    </button>
                    <button
                      onClick={() => setShowWebcam(true)}
                      disabled={loading}
                      className="inline-flex items-center gap-2 rounded-2xl border border-[#e5d6c6] bg-white px-5 py-3 text-sm font-semibold text-[#8e5e43] transition hover:border-[#db8146] hover:text-[#db8146] disabled:opacity-40"
                    >
                      📷 Webcam
                    </button>
                    <button
                      onClick={reset}
                      disabled={loading}
                      className="ml-auto rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-500 transition hover:border-[#db8146] hover:text-[#db8146] disabled:opacity-40"
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
                  <section className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-6 shadow-lg shadow-[#cdb097]/10">
                    {/* Top match header */}
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm uppercase tracking-[0.35em] text-[#88614f]">Top match</p>
                        <h2 className="text-2xl font-semibold text-slate-900">{result.vibe}</h2>
                      </div>
                      <div className="rounded-3xl bg-[#db8146] px-4 py-2 text-sm font-bold text-white shadow-md shadow-[#c77d50]/30">
                        {Math.round(result.confidence)}%
                      </div>
                    </div>

                    {/* Top-3 softmax bar */}
                    {result.top_k?.length > 1 && (
                      <div className="mt-4 flex flex-col gap-2">
                        {result.top_k.map((match, i) => (
                          <div key={match.vibe} className="flex items-center gap-3">
                            <span className={`w-36 shrink-0 text-sm font-medium truncate ${i === 0 ? 'text-slate-900' : 'text-slate-400'}`}>
                              {match.vibe}
                            </span>
                            <div className="flex-1 h-2.5 rounded-full bg-slate-100 overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${i === 0 ? 'bg-[#db8146]' : 'bg-[#d9c4b8]'}`}
                                style={{ width: `${Math.round(match.confidence)}%` }}
                              />
                            </div>
                            <span className={`w-10 text-right text-xs font-semibold tabular-nums ${i === 0 ? 'text-[#db8146]' : 'text-slate-400'}`}>
                              {Math.round(match.confidence)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    <p className="mt-5 text-sm leading-7 text-slate-600">{vibeInfo?.description}</p>

                    <div className="mt-6 grid gap-4 grid-cols-2">
                      <div className="rounded-3xl bg-[#fff4ec] p-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[#88614f] mb-3">🛍️ Outfits</p>
                        <ul className="space-y-2 text-sm text-slate-700">
                          {(picks?.outfits ?? []).map((item) => (
                            <li key={item} className="rounded-xl bg-white px-3 py-2 shadow-sm shadow-[#d2beb1]/40 leading-snug">{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="rounded-3xl bg-[#fdf5ec] p-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[#88614f] mb-3">🛋️ Decor</p>
                        <ul className="space-y-2 text-sm text-slate-700">
                          {(picks?.decor ?? []).map((item) => (
                            <li key={item} className="rounded-xl bg-white px-3 py-2 shadow-sm shadow-[#d2beb1]/40 leading-snug">{item}</li>
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
                      <div key={item.id} className="group relative rounded-3xl border border-[#f1d7c3] bg-[#fff5ef] p-4 shadow-sm shadow-[#d2beb1]/40">
                        <button
                          onClick={() => removeFromBoard(item.id)}
                          className="absolute right-3 top-3 hidden group-hover:flex items-center justify-center w-7 h-7 rounded-full bg-white/90 text-slate-400 hover:text-red-500 hover:bg-white shadow-sm transition text-xs z-10"
                          title="Remove"
                        >✕</button>
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

            <div className="rounded-[32px] border border-[#e5d6c6] bg-white/95 p-6 shadow-lg shadow-[#cdb097]/10">
              <div className="flex items-center justify-between gap-3 mb-5">
                <div>
                  <p className="text-sm uppercase tracking-[0.35em] text-[#88614f]">Pinned board</p>
                  <h3 className="text-xl font-semibold text-slate-900">Saved looks</h3>
                </div>
                <span className="inline-flex rounded-full bg-[#fff0e6] px-3 py-1 text-xs font-semibold text-[#8e5e43]">{board.length} items</span>
              </div>
              {board.length === 0 ? (
                <div className="rounded-3xl bg-[#faf5f1] p-4 text-sm text-slate-600">
                  Save your first look to build a personal mood board.
                </div>
              ) : (
                <div className="space-y-3">
                  {board.map((item) => (
                    <div key={item.id} className="group relative rounded-3xl border border-[#f1d7c3] bg-[#fff5ef] p-4">
                      <button
                        onClick={() => removeFromBoard(item.id)}
                        className="absolute right-3 top-3 hidden group-hover:flex items-center justify-center w-6 h-6 rounded-full bg-white/80 text-slate-400 hover:text-red-500 hover:bg-white shadow-sm transition text-xs"
                        title="Remove"
                      >✕</button>
                      {item.preview && (
                        <div className="w-full aspect-video rounded-2xl overflow-hidden mb-3 bg-slate-100">
                          <img src={item.preview} alt={item.vibe} className="w-full h-full object-cover" />
                        </div>
                      )}
                      <p className="font-semibold text-slate-900">{item.vibe}</p>
                      <p className="mt-1 text-sm text-slate-600">{item.outfit}</p>
                      <p className="mt-2 text-xs text-slate-500">Saved {new Date(item.date).toLocaleDateString()}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
