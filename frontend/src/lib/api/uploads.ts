import { env } from "@/config/env";
import { ApiError } from "@/lib/http/client";
import type { AudioUploadResponse } from "@/types/upload";

function parseXhrError(xhr: XMLHttpRequest): string {
  try {
    const data = JSON.parse(xhr.responseText);
    if (typeof data.detail === "string") return data.detail;
    return data.message ?? "Upload failed";
  } catch {
    return xhr.statusText || "Upload failed";
  }
}

export function uploadAudio(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<AudioUploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append("file", file, file.name);

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as AudioUploadResponse);
        } catch {
          reject(new ApiError("Invalid server response", xhr.status));
        }
        return;
      }
      reject(new ApiError(parseXhrError(xhr), xhr.status));
    });

    xhr.addEventListener("error", () => {
      reject(new ApiError("Network error during upload", 0));
    });

    xhr.addEventListener("abort", () => {
      reject(new ApiError("Upload cancelled", 0));
    });

    xhr.open("POST", `${env.apiUrl}/api/v1/uploads`);
    xhr.send(form);
  });
}
