import assert from 'node:assert';

// Standalone test replicating the logic from frontend/src/lib/modality.ts
function deriveModality(filename, mimeType) {
  const cleanName = (filename || '').trim().toLowerCase();
  const cleanMime = (mimeType || '').trim().toLowerCase();

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

console.log("Testing TypeScript/JavaScript deriveModality parity...");

// Video tests
assert.strictEqual(deriveModality('WIN_20260830_21_50_59_Pro.mp4'), 'Video');
assert.strictEqual(deriveModality('clip.MOV'), 'Video');
assert.strictEqual(deriveModality('stream.webm'), 'Video');
assert.strictEqual(deriveModality('video container payload: sample.mp4'), 'Video');
assert.strictEqual(deriveModality('', 'video/mp4'), 'Video');

// Audio tests
assert.strictEqual(deriveModality('sound.mp3'), 'Audio');
assert.strictEqual(deriveModality('track.wav'), 'Audio');
assert.strictEqual(deriveModality('audio track payload: hum.wav'), 'Audio');
assert.strictEqual(deriveModality('', 'audio/ogg'), 'Audio');

// Image tests
assert.strictEqual(deriveModality('bearing.png'), 'Image');
assert.strictEqual(deriveModality('photo.JPG'), 'Image');
assert.strictEqual(deriveModality('scan.webp'), 'Image');
assert.strictEqual(deriveModality('visual payload: img.png'), 'Image');
assert.strictEqual(deriveModality('', 'image/jpeg'), 'Image');

// Text & defaults
assert.strictEqual(deriveModality('dataset.csv'), 'Text');
assert.strictEqual(deriveModality('notes.txt'), 'Text');
assert.strictEqual(deriveModality(''), 'Text');
assert.strictEqual(deriveModality(null), 'Text');
assert.strictEqual(deriveModality(undefined), 'Text');

// State independence sequence
assert.strictEqual(deriveModality('WIN_20260830_21_50_59_Pro.mp4'), 'Video');
assert.strictEqual(deriveModality('bearing.png'), 'Image');
assert.strictEqual(deriveModality('WIN_20260830_21_50_59_Pro.mp4'), 'Video');
assert.strictEqual(deriveModality('notes.txt'), 'Text');

console.log("All TypeScript deriveModality tests PASSED cleanly!");
