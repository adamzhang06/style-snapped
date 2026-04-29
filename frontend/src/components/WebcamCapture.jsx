import { useRef, useCallback } from 'react'
import Webcam from 'react-webcam'

export default function WebcamCapture({ onCapture, onClose }) {
  const webcamRef = useRef(null)

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot()
    if (!imageSrc) return
    fetch(imageSrc)
      .then((r) => r.blob())
      .then((blob) => {
        const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' })
        onCapture(file, imageSrc)
      })
  }, [onCapture])

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden w-full max-w-lg shadow-2xl shadow-black">
        <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
          <div>
            <p className="text-xs uppercase tracking-widest text-orange-500 font-semibold mb-0.5">
              Webcam
            </p>
            <h3 className="text-sm font-semibold text-zinc-100">Snap Your Outfit</h3>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition-colors text-sm"
          >
            ✕
          </button>
        </div>

        <div className="p-4">
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            screenshotQuality={0.92}
            className="w-full rounded-xl"
            videoConstraints={{ facingMode: 'user' }}
            mirrored
          />
        </div>

        <div className="px-5 pb-5 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium border border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={capture}
            className="flex-1 py-2.5 rounded-xl text-sm font-semibold bg-orange-500 hover:bg-orange-400 text-white transition-colors shadow-lg shadow-orange-900/30"
          >
            Capture Photo
          </button>
        </div>
      </div>
    </div>
  )
}
