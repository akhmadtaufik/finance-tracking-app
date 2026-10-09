/**
 * Utility to compress and resize receipt images strictly in-memory (RAM)
 * using the HTML5 Canvas API before uploading.
 * 
 * Never writes or caches files to local storage or persistent disk.
 */

export async function compressReceiptImage(file, maxDimension = 1200, quality = 0.85) {
  if (!file || !file.type.startsWith('image/')) {
    return file
  }

  return new Promise((resolve) => {
    const objectUrl = URL.createObjectURL(file)
    const img = new Image()

    img.onload = () => {
      URL.revokeObjectURL(objectUrl)

      let { width, height } = img

      // If image is already smaller than maxDimension, no downscaling needed
      if (width <= maxDimension && height <= maxDimension && file.size < 1024 * 1024) {
        return resolve(file)
      }

      // Constrain aspect ratio
      if (width > height) {
        if (width > maxDimension) {
          height = Math.round((height * maxDimension) / width)
          width = maxDimension
        }
      } else {
        if (height > maxDimension) {
          width = Math.round((width * maxDimension) / height)
          height = maxDimension
        }
      }

      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height

      const ctx = canvas.getContext('2d')
      if (!ctx) {
        return resolve(file)
      }

      // Clean fill for transparency
      ctx.fillStyle = '#FFFFFF'
      ctx.fillRect(0, 0, width, height)
      ctx.drawImage(img, 0, 0, width, height)

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            return resolve(file)
          }

          // Wrap in in-memory File object with original name
          const newFileName = file.name.replace(/\.[^/.]+$/, '') + '.jpg'
          const compressedFile = new File([blob], newFileName, {
            type: 'image/jpeg',
            lastModified: Date.now()
          })

          // Free canvas memory
          canvas.width = 0
          canvas.height = 0

          resolve(compressedFile)
        },
        'image/jpeg',
        quality
      )
    }

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl)
      resolve(file) // Fallback to original file on decoding error
    }

    img.src = objectUrl
  })
}
