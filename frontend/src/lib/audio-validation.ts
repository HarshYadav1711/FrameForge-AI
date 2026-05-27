export const ALLOWED_AUDIO_EXTENSIONS = [".mp3", ".wav", ".m4a"] as const;
export const ALLOWED_AUDIO_ACCEPT = ".mp3,.wav,.m4a,audio/mpeg,audio/wav,audio/mp4";
export const MAX_AUDIO_BYTES = 50 * 1024 * 1024;

export type AllowedAudioExtension = (typeof ALLOWED_AUDIO_EXTENSIONS)[number];

export interface AudioValidationResult {
  valid: boolean;
  error?: string;
  extension?: AllowedAudioExtension;
}

export function getFileExtension(filename: string): string {
  const i = filename.lastIndexOf(".");
  return i >= 0 ? filename.slice(i).toLowerCase() : "";
}

export function validateAudioFile(file: File): AudioValidationResult {
  const ext = getFileExtension(file.name) as AllowedAudioExtension;

  if (!ALLOWED_AUDIO_EXTENSIONS.includes(ext as AllowedAudioExtension)) {
    return {
      valid: false,
      error: "Only MP3, WAV, and M4A files are supported.",
    };
  }

  if (file.size === 0) {
    return { valid: false, error: "File is empty." };
  }

  if (file.size > MAX_AUDIO_BYTES) {
    return { valid: false, error: "File exceeds 50 MB limit." };
  }

  return { valid: true, extension: ext };
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}
