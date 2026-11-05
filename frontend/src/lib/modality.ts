export type ModalityType = 'Image' | 'Video' | 'Audio' | 'Text' | 'Mixed';

/**
 * State-independent modality derivation.
 * Eliminates lingering state bugs by strictly inspecting file extensions, MIME types, and payload prefixes.
 */
export function deriveModality(filename?: string, mimeType?: string, hasBothMediaAndText?: boolean): ModalityType {
  if (hasBothMediaAndText) return 'Mixed';

  const cleanName = (filename || '').trim().toLowerCase();
  const cleanMime = (mimeType || '').trim().toLowerCase();

  if (cleanName.includes('claim vs evidence') || cleanName.includes('multi-modal pair') || cleanName.includes('mixed modality')) {
    return 'Mixed';
  }

  // 1. Video detection
  if (
    cleanMime.startsWith('video/') ||
    cleanName.includes('video container payload:') ||
    /\.(mp4|mov|avi|mkv|webm|m4v|3gp|flv|wmv)\b/i.test(cleanName)
  ) {
    return 'Video';
  }

  // 2. Audio detection
  if (
    cleanMime.startsWith('audio/') ||
    cleanName.includes('audio track payload:') ||
    /\.(mp3|wav|ogg|m4a|aac|flac)\b/i.test(cleanName)
  ) {
    return 'Audio';
  }

  // 3. Image detection
  if (
    cleanMime.startsWith('image/') ||
    cleanName.includes('visual payload:') ||
    /\.(png|jpe?g|webp|gif|svg|bmp|ico|tiff)\b/i.test(cleanName)
  ) {
    return 'Image';
  }

  // 4. Default to Text
  return 'Text';
}
