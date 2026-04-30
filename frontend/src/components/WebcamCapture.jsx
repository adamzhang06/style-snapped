import { useRef, useCallback, useState, useEffect } from 'react'
import Webcam from 'react-webcam'

export default function WebcamCapture({ onCapture, onClose }) {
  const webcamRef = useRef(null)
  const [countdown, setCountdown] = useState(null)

  const shoot = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot()
    if (!imageSrc) return
    fetch(imageSrc)
      .then((r) => r.blob())
      .then((blob) => {
        const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' })
        onCapture(file, imageSrc)
      })
  }, [onCapture])

  useEffect(() => {
    if (countdown === null) return
    if (countdown === 0) {
      shoot()
      setCountdown(null)
      return
    }
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000)
    return () => clearTimeout(t)
  }, [countdown, shoot])

  const startCountdown = () => setCountdown(3)
  const cancelCountdown = () => setCountdown(null)
  const isCounting = countdown !== null

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget && !isCounting) onClose() }}
    >
      <div className="bg-zinc-900 border border-zinc-800 rounded-[28px] overflow-hidden w-full max-w-lg shadow-2xl shadow-black">
        <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
          <div>
            <p className="text-xs uppercase tracking-widest text-[#db8146] font-semibold mb-0.5">Webcam</p>
            <h3 className="text-sm font-semibold text-zinc-100">Snap Your Outfit</h3>
          </div>
          {!isCounting && (
            <button
              onClick={onClose}
              className="w-7 h-7 flex items-center justify-center text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition-colors text-sm"
            >
              ✕
            </button>
          )}
        </div>

        <div className="p-4 relative">
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            screenshotQuality={0.92}
            className="w-full rounded-2xl"
            videoConstraints={{ facingMode: 'user' }}
            mirrored
          />

          {isCounting && (
            <div className="absolute inset-4 rounded-2xl flex items-center justify-center bg-black/40 backdrop-blur-[2px]">
              <div className="flex flex-col items-center gap-2">
                <span
                  key={countdown}
                  className="text-8xl font-bold text-white drop-shadow-2xl"
                  style={{ animation: 'countPulse 1s ease-out forwards' }}
                >
                  {countdown}
                </span>
                <p className="text-sm text-white/70 font-medium tracking-wide">Hold still…</p>
              </div>
            </div>
          )}
        </div>

        <div className="px-5 pb-5 flex gap-3">
          {isCounting ? (
            <button
              onClick={cancelCountdown}
              className="flex-1 py-3 rounded-2xl text-sm font-medium border border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 transition-colors"
            >
              Cancel
            </button>
          ) : (
            <>
              <button
                onClick={onClose}
                className="flex-1 py-3 rounded-2xl text-sm font-medium border border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={startCountdown}
                className="flex-1 py-3 rounded-2xl text-sm font-semibold bg-[#db8146] hover:bg-[#c66736] text-white transition-colors shadow-lg shadow-orange-900/30"
              >
                📷 Take Photo (3s)
              </button>
            </>
          )}
        </div>
      </div>

      <style>{`
        @keyframes countPulse {
          0%   { transform: scale(1.4); opacity: 0.4; }
          30%  { transform: scale(1);   opacity: 1;   }
          80%  { transform: scale(1);   opacity: 1;   }
          100% { transform: scale(0.9); opacity: 0.6; }
        }
      `}</style>
    </div>
  )
}
