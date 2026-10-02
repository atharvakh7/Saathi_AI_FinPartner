/**
 * Voice mode (step 26; wireframe "Voice Assistant (full screen)"): dark teal screen, status pill
 * (Listening 0:07 / Thinking / Speaking), mascot in a glowing circle that pulses while listening or
 * speaking, a bubble with what Saathi heard and its reply, and Keyboard · Mic · End.
 * Tap the mic to start, tap again to send (auto-sends at 59 s). Each turn joins the current chat
 * conversation. The reply is spoken if "voice replies" is on: server voice (en/hi/mr) or on-device
 * speech (Tamil, or when the server voice fails).
 */
import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { Keyboard, Mic, PhoneOff, Square, X } from 'lucide-react-native';
import Animated, { cancelAnimation, useAnimatedStyle, useSharedValue, withRepeat, withTiming } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { sendVoiceMessage, type RecordedAudio, type VoiceReplyDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Mascot, useErrorMessage } from '@/components';
import type { MascotPose } from '@/components';
import { changesMoneyData, chatKeys, withReply } from '@/features/chat/chat';
import { invalidateFinance } from '@/features/finance/queries';
import { invalidateGoals } from '@/features/goals/goals';
import { usePlayback, useRecorder } from '@/features/voice/useVoice';
import { clock, MAX_RECORDING_SEC, MIN_RECORDING_SEC } from '@/features/voice/voice';
import { useChatStore } from '@/stores';
import { useLanguageStore } from '@/stores/language';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { MIN_TOUCH, radius, space } from '@/theme';

type Phase = 'idle' | 'recording' | 'thinking' | 'speaking';

const DARK = '#0B3A40';
const GLOW = '#1BA39C';
const ON_DARK = '#FFFFFF';
const ON_DARK_MUTED = '#B8D9DB';

export default function VoiceMode() {
  const { t } = useTranslation();
  const toMessage = useErrorMessage();
  const loggedIn = useSessionStore(isLoggedIn);
  const voiceReplies = useSessionStore((s) => s.user?.voice_reply_enabled ?? true);
  const language = useLanguageStore((s) => s.language);
  const [phase, setPhase] = useState<Phase>('idle');
  const [heard, setHeard] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const playback = usePlayback();
  const recorder = useRecorder(() => void finish());

  const send = useMutation({
    mutationFn: (audio: RecordedAudio) => sendVoiceMessage(audio, useChatStore.getState().activeConversationId, language),
    onSuccess: (reply: VoiceReplyDTO) => {
      queryClient.setQueryData(chatKeys.messages(reply.conversation_id), (old: Parameters<typeof withReply>[0]) => withReply(old, reply));
      useChatStore.getState().setActiveConversation(reply.conversation_id);
      void queryClient.invalidateQueries({ queryKey: chatKeys.conversations });
      if (changesMoneyData(reply.assistant_message.intent)) { invalidateFinance(); invalidateGoals(); }
      setHeard(reply.transcript);
      setAnswer(reply.assistant_message.content);
      if (voiceReplies) {
        setPhase('speaking');
        void playback.speak(reply.assistant_message.id, reply.assistant_message.content,
          reply.assistant_message.language ?? reply.detected_language, reply.audio?.url);
      } else {
        setPhase('idle');
      }
    },
    onError: (e) => {
      setPhase('idle');
      setNotice(e instanceof ApiError && e.code === 'TRANSCRIPTION_FAILED' ? t('voice.notHeard') : toMessage(e));
    },
  });

  // Speaking ends -> ready for the next question.
  useEffect(() => {
    if (phase === 'speaking' && playback.speakingId === null) {
      const id = setTimeout(() => setPhase((p) => (p === 'speaking' ? 'idle' : p)), 600);
      return () => clearTimeout(id);
    }
    return undefined;
  }, [phase, playback.speakingId]);

  async function begin() {
    setNotice(null);
    playback.stop();
    try {
      const ok = await recorder.start();
      if (!ok) { setNotice(t('voice.micDenied')); return; }
      setHeard(null);
      setAnswer(null);
      setPhase('recording');
    } catch {
      setNotice(t('voice.micError'));
    }
  }

  async function finish() {
    const result = await recorder.stop();
    if (!result || result.seconds < MIN_RECORDING_SEC) {
      setPhase('idle');
      setNotice(t('voice.tooShort'));
      return;
    }
    setPhase('thinking');
    send.mutate(result.audio);
  }

  const leave = () => {
    playback.stop();
    void recorder.stop();
    if (router.canGoBack()) router.back(); else router.replace('/saathi');
  };

  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;

  const pose: MascotPose = phase === 'recording' ? 'listening' : phase === 'thinking' ? 'thinking' : phase === 'speaking' ? 'speaking' : 'wave';
  const pill = phase === 'recording' ? `${t('voice.listening')} ${clock(recorder.seconds)} / ${clock(MAX_RECORDING_SEC)}`
    : phase === 'thinking' ? t('voice.thinking') : phase === 'speaking' ? t('voice.speaking') : t('voice.tapToSpeak');
  const bubble = notice ?? answer ?? t('voice.prompt');

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.top}>
        <Pressable onPress={leave} accessibilityRole="button" accessibilityLabel={t('common.close')} hitSlop={8} style={styles.iconBtn}>
          <X color={ON_DARK} size={26} />
        </Pressable>
        <View style={styles.pill} accessibilityLiveRegion="polite">
          {phase === 'recording' ? <View style={styles.recDot} /> : null}
          <AppText variant="small" tint={ON_DARK}>{pill}</AppText>
        </View>
        <View style={styles.iconBtn} />
      </View>

      <View style={styles.center}>
        <Glow active={phase === 'recording' || phase === 'speaking'} />
        <Mascot pose={pose} size={226} variant="avatar" ringColor="transparent" />
      </View>

      <View style={styles.texts}>
        {heard ? <AppText variant="small" tint={ON_DARK_MUTED} align="center" numberOfLines={3}>{`“${heard}”`}</AppText> : null}
        <View style={styles.bubble}>
          <AppText tint={notice ? '#FFD7D7' : ON_DARK} align="center" numberOfLines={8}>{bubble}</AppText>
        </View>
      </View>

      <View style={styles.bottom}>
        <Control label={t('voice.keyboard')} onPress={() => { playback.stop(); void recorder.stop(); router.replace('/saathi'); }}>
          <Keyboard color={ON_DARK} size={24} />
        </Control>
        <Pressable
          onPress={() => (phase === 'recording' ? void finish() : phase === 'thinking' ? undefined : void begin())}
          disabled={phase === 'thinking'}
          accessibilityRole="button"
          accessibilityLabel={phase === 'recording' ? t('voice.stopAndSend') : t('voice.tapToSpeak')}
          accessibilityState={{ disabled: phase === 'thinking', busy: phase === 'recording' }}
          style={({ pressed }) => [styles.mic, phase === 'recording' && styles.micOn, phase === 'thinking' && styles.micOff, pressed && { opacity: 0.85 }]}>
          {phase === 'recording' ? <Square color={ON_DARK} size={30} /> : <Mic color={ON_DARK} size={34} />}
        </Pressable>
        <Control label={t('voice.end')} onPress={leave} danger><PhoneOff color={ON_DARK} size={24} /></Control>
      </View>
    </SafeAreaView>
  );
}

function Control({ label, onPress, children, danger }: { label: string; onPress: () => void; children: React.ReactNode; danger?: boolean }) {
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={label} style={styles.control}>
      <View style={[styles.controlIcon, danger && styles.controlDanger]}>{children}</View>
      <AppText variant="caption" tint={ON_DARK_MUTED}>{label}</AppText>
    </Pressable>
  );
}

/** Two soft rings behind the mascot; they breathe while listening or speaking. */
function Glow({ active }: { active: boolean }) {
  const scale = useSharedValue(1);
  useEffect(() => {
    if (active) scale.value = withRepeat(withTiming(1.12, { duration: 700 }), -1, true);
    else { cancelAnimation(scale); scale.value = withTiming(1, { duration: 300 }); }
  }, [active, scale]);
  const outer = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  return (
    <>
      <Animated.View style={[styles.ring, styles.ringOuter, outer]} />
      <View style={[styles.ring, styles.ringInner]} />
    </>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: DARK },
  top: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: space.md, paddingTop: space.sm },
  iconBtn: { width: MIN_TOUCH, height: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
  pill: {
    flexDirection: 'row', alignItems: 'center', gap: space.sm, paddingHorizontal: space.lg, paddingVertical: space.sm,
    borderRadius: radius.pill, backgroundColor: 'rgba(255,255,255,0.12)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.18)',
  },
  recDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#FF6B6B' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: 260 },
  ring: { position: 'absolute', borderRadius: 999 },
  ringOuter: { width: 270, height: 270, borderWidth: 2, borderColor: GLOW, backgroundColor: 'rgba(27,163,156,0.10)' },
  ringInner: { width: 230, height: 230, backgroundColor: 'rgba(27,163,156,0.22)' },
  texts: { paddingHorizontal: space.xxl, gap: space.sm, minHeight: 120, justifyContent: 'flex-end' },
  bubble: {
    alignSelf: 'center', maxWidth: 520, paddingHorizontal: space.xl, paddingVertical: space.lg, borderRadius: radius.lg,
    backgroundColor: 'rgba(255,255,255,0.10)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.16)',
  },
  bottom: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', paddingVertical: space.xxl },
  control: { alignItems: 'center', gap: space.xs, minWidth: 72 },
  controlIcon: {
    width: 52, height: 52, borderRadius: 26, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.12)',
  },
  controlDanger: { backgroundColor: '#D64545' },
  mic: { width: 84, height: 84, borderRadius: 42, backgroundColor: GLOW, alignItems: 'center', justifyContent: 'center', borderWidth: 4, borderColor: 'rgba(255,255,255,0.25)' },
  micOn: { backgroundColor: '#D64545' },
  micOff: { opacity: 0.5 },
});
