"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { uploadAudio } from "@/lib/api/uploads";
import { getErrorMessage } from "@/lib/async-state";
import { validateAudioFile } from "@/lib/audio-validation";
import type { AudioUploadState } from "@/types/upload";

const INITIAL: AudioUploadState = {
  phase: "idle",
  progress: 0,
  uploadId: null,
  error: null,
};

export function useAudioUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [state, setState] = useState<AudioUploadState>(INITIAL);
  const abortRef = useRef(false);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const clear = useCallback(() => {
    abortRef.current = true;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setState(INITIAL);
  }, [previewUrl]);

  const selectFile = useCallback(
    async (next: File) => {
      abortRef.current = false;
      const validation = validateAudioFile(next);
      if (!validation.valid) {
        setState({
          phase: "error",
          progress: 0,
          uploadId: null,
          error: validation.error ?? "Invalid file",
        });
        setFile(null);
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
        return;
      }

      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setFile(next);
      setPreviewUrl(URL.createObjectURL(next));
      setState({ phase: "validating", progress: 0, uploadId: null, error: null });

      setState({ phase: "uploading", progress: 0, uploadId: null, error: null });

      try {
        const result = await uploadAudio(next, (progress) => {
          if (!abortRef.current) {
            setState((s) => ({ ...s, phase: "uploading", progress }));
          }
        });
        if (abortRef.current) return;
        setState({
          phase: "complete",
          progress: 100,
          uploadId: result.id,
          error: null,
        });
      } catch (err) {
        if (abortRef.current) return;
        setState({
          phase: "error",
          progress: 0,
          uploadId: null,
          error: getErrorMessage(err),
        });
      }
    },
    [previewUrl],
  );

  const retry = useCallback(() => {
    if (file) selectFile(file);
  }, [file, selectFile]);

  const isReady = state.phase === "complete" && state.uploadId != null;

  return {
    file,
    previewUrl,
    state,
    isReady,
    uploadId: state.uploadId,
    selectFile,
    clear,
    retry,
  };
}
