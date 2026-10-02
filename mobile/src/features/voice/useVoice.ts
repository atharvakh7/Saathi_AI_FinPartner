/**
 * Recording and playback for voice chat (step 26), on expo-audio + expo-speech.
 *  - useRecorder: asks for the microphone, records (m4a on phones, webm in the browser), stops itself
 *    at 59 s, and hands back something /chat/voice can upload.
 *  - usePlayback: plays a reply — the server's voice (Piper, via a short-lived URL) when there is one,
 *    otherwise on-device speech (always for Tamil, spec A8; also when the server voice fails).
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import {
  RecordingPresets, requestRecordingPermissionsAsync, setAudioModeAsync, useAudioPlayer, useAudioPlayerStatus,
  useAudioRecorder,
} from 'expo-audio';
import * as Speech from 'expo-speech';

import { textToSpeech, type RecordedAudio } from '@/api/endpoints';
import type { Language } from '@/i18n';
import { MAX_RECORDING_SEC, speechLanguage, uploadMeta } from './voice';

export type RecordResult = { audio: RecordedAudio; seconds: number } | null;

export function useRecorder(onAutoStop?: () => void) {
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const startedAt = useRef(0);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const autoStop = useRef(onAutoStop);
  autoStop.current = onAutoStop;

  const clear = () => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
  };
  useEffect(() => clear, []);

  /** false = the user refused the microphone. */
  const start = useCallback(async (): Promise<boolean> => {
    const perm = await requestRecordingPermissionsAsync();
    if (!perm.granted) return false;
    await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
    await recorder.prepareToRecordAsync();
    recorder.record();
    startedAt.current = Date.now();
    setSeconds(0);
    setRecording(true);
    timer.current = setInterval(() => {
      const s = (Date.now() - startedAt.current) / 1000;
      setSeconds(s);
      if (s >= MAX_RECORDING_SEC) autoStop.current?.();
    }, 250);
    return true;
  }, [recorder]);

  const stop = useCallback(async (): Promise<RecordResult> => {
    clear();
    if (!recording) return null;
    setRecording(false);
    await recorder.stop();
    await setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true }).catch(() => undefined);
    const secs = (Date.now() - startedAt.current) / 1000;
    const uri = recorder.uri;
    if (!uri) return null;
    const meta = uploadMeta(Platform.OS);
    if (Platform.OS === 'web') {
      const blob = await (await fetch(uri)).blob(); // the browser recorder gives a blob: URL
      return { audio: { blob, name: meta.name }, seconds: secs };
    }
    return { audio: { uri, ...meta }, seconds: secs };
  }, [recorder, recording]);

  return { start, stop, recording, seconds };
}

export function usePlayback() {
  const player = useAudioPlayer(null);
  const status = useAudioPlayerStatus(player);
  const [speakingId, setSpeakingId] = useState<string | null>(null);

  useEffect(() => {
    if (status.didJustFinish) setSpeakingId(null);
  }, [status.didJustFinish]);

  const stop = useCallback(() => {
    try { player.pause(); } catch { /* not loaded */ }
    void Speech.stop();
    setSpeakingId(null);
  }, [player]);

  const speakOnDevice = useCallback((id: string, text: string, language: Language | null) => {
    setSpeakingId(id);
    Speech.speak(text, {
      language: speechLanguage(language),
      onDone: () => setSpeakingId((cur) => (cur === id ? null : cur)),
      onStopped: () => setSpeakingId((cur) => (cur === id ? null : cur)),
      onError: () => setSpeakingId((cur) => (cur === id ? null : cur)),
    });
  }, []);

  const playUrl = useCallback((id: string, url: string) => {
    void setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true }).catch(() => undefined);
    player.replace({ uri: url });
    player.play();
    setSpeakingId(id);
  }, [player]);

  /** Speak a reply: a ready URL if the API sent one, else ask /chat/tts, else the device voice. */
  const speak = useCallback(async (id: string, text: string, language: Language | null, url?: string | null) => {
    stop();
    if (url) return playUrl(id, url);
    if (language === 'ta') return speakOnDevice(id, text, language);
    try {
      const res = await textToSpeech(text, language);
      if (res.url) playUrl(id, res.url);
      else speakOnDevice(id, text, language);
    } catch {
      speakOnDevice(id, text, language);
    }
  }, [playUrl, speakOnDevice, stop]);

  const toggle = useCallback((id: string, text: string, language: Language | null) => {
    if (speakingId === id) stop();
    else void speak(id, text, language);
  }, [speak, speakingId, stop]);

  return { speak, toggle, stop, speakingId };
}
