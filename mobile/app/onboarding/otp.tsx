/**
 * S05 OTP Verify (spec §4.7): six boxes backed by ONE hidden input, so paste and SMS autofill
 * (textContentType=oneTimeCode / autoComplete=sms-otp) fill all digits at once. Auto-submits on the
 * 6th digit. OTP_INVALID shakes and shows attempts left; OTP_EXPIRED offers resend; OTP_LOCKED
 * disables input and shows minutes remaining; resend has a 30 s countdown.
 */
import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';
import { Redirect, router, useLocalSearchParams } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import Animated, { useAnimatedStyle, useSharedValue, withSequence, withTiming } from 'react-native-reanimated';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { requestOtp, verifyOtp } from '@/api/endpoints';
import { AppText, Button, ErrorBanner, Mascot, Screen } from '@/components';
import { completeLogin } from '@/lib/session';
import { color, fontFamily, radius, space } from '@/theme';

const LENGTH = 6;
const DEFAULT_RESEND_SEC = 30;

export default function Otp() {
  const { t } = useTranslation();
  const params = useLocalSearchParams<{ phone?: string; resend?: string }>();
  const phone = params.phone ?? '';
  const [code, setCode] = useState('');
  const [resendIn, setResendIn] = useState(Number(params.resend) || DEFAULT_RESEND_SEC);
  const [lockedUntil, setLockedUntil] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const input = useRef<TextInput>(null);
  const shake = useSharedValue(0);
  const shakeStyle = useAnimatedStyle(() => ({ transform: [{ translateX: shake.value }] }));

  useEffect(() => {
    const id = setInterval(() => setResendIn((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => clearInterval(id);
  }, []);

  const locked = lockedUntil !== null && Date.now() < lockedUntil;

  const verify = useMutation({
    mutationFn: (c: string) => verifyOtp(`+91${phone}`, c),
    onSuccess: async (res) => router.replace((await completeLogin(res)) as never),
    onError: (e) => {
      setCode('');
      if (e instanceof ApiError && e.code === 'OTP_INVALID') {
        shake.value = withSequence(...[-10, 10, -8, 8, -4, 0].map((x) => withTiming(x, { duration: 50 })));
      }
      if (e instanceof ApiError && e.code === 'OTP_LOCKED') {
        const secs = Number((e.details as { retry_after_sec?: number } | null)?.retry_after_sec) || 900;
        setLockedUntil(Date.now() + secs * 1000);
        input.current?.blur();
      } else {
        input.current?.focus();
      }
    },
  });

  const resend = useMutation({
    mutationFn: () => requestOtp(`+91${phone}`),
    onSuccess: (res) => {
      setResendIn(res.resend_after_sec || DEFAULT_RESEND_SEC);
      setNotice(t('onboarding.otp.resent'));
      verify.reset();
      setCode('');
    },
  });

  const onChange = (raw: string) => {
    const digits = raw.replace(/\D/g, '').slice(0, LENGTH);
    setCode(digits);
    setNotice(null);
    if (digits.length === LENGTH && !verify.isPending && !locked) verify.mutate(digits);
  };

  const err = verify.error instanceof ApiError ? verify.error : null;
  const errorText = (() => {
    if (!err) return null;
    if (err.code === 'OTP_INVALID') {
      const left = (err.details as { attempts_left?: number } | null)?.attempts_left;
      return typeof left === 'number' ? t('onboarding.otp.wrongLeft', { count: left }) : t('errors.OTP_INVALID');
    }
    if (err.code === 'OTP_LOCKED') {
      const mins = (err.details as { minutes_remaining?: number } | null)?.minutes_remaining ?? 15;
      return t('onboarding.otp.locked', { count: mins });
    }
    return null; // other errors use the default banner
  })();

  if (!phone) return <Redirect href="/onboarding/phone" />;

  return (
    <Screen back>
      <View style={styles.center}>
        <Mascot pose="listening" size={110} variant="bust" />
        <AppText variant="h2" align="center">{t('onboarding.otp.title')}</AppText>
        <AppText muted align="center">{t('onboarding.otp.sentTo', { phone: `+91 ${phone.slice(0, 5)} ${phone.slice(5)}` })}</AppText>
      </View>

      <Pressable onPress={() => input.current?.focus()} accessibilityLabel={t('onboarding.otp.title')} disabled={locked}>
        <Animated.View style={[styles.boxes, shakeStyle]}>
          {Array.from({ length: LENGTH }, (_, i) => {
            const filled = i < code.length;
            const active = i === code.length && !locked;
            return (
              <View key={i} style={[styles.box, active && styles.boxActive, !!err && styles.boxError, locked && styles.boxLocked]}>
                <AppText variant="h2" style={styles.digit}>{code[i] ?? ''}</AppText>
                {!filled && active ? <View style={styles.caret} /> : null}
              </View>
            );
          })}
        </Animated.View>
      </Pressable>
      <TextInput
        ref={input}
        value={code}
        onChangeText={onChange}
        keyboardType="number-pad"
        textContentType="oneTimeCode"
        autoComplete="sms-otp"
        maxLength={LENGTH}
        autoFocus
        editable={!locked && !verify.isPending}
        style={styles.hidden}
        accessibilityLabel={t('onboarding.otp.title')}
        importantForAutofill="yes"
      />

      {verify.isPending ? <AppText muted align="center">{t('onboarding.otp.checking')}</AppText> : null}
      {errorText ? <AppText tint={color.danger} align="center" accessibilityRole="alert">{errorText}</AppText> : null}
      {err && !errorText ? (
        err.code === 'OTP_EXPIRED'
          ? <ErrorBanner error={err} onRetry={() => resend.mutate()} />
          : <ErrorBanner error={err} onRetry={code.length === LENGTH ? () => verify.mutate(code) : undefined} />
      ) : null}
      {resend.error ? <ErrorBanner error={resend.error} /> : null}
      {notice ? <AppText tint={color.success} align="center">{notice}</AppText> : null}

      <View style={styles.center}>
        {resendIn > 0 ? (
          <AppText muted>{t('onboarding.otp.resendIn', { count: resendIn })}</AppText>
        ) : (
          <Button label={t('onboarding.otp.resend')} variant="ghost" fullWidth={false} loading={resend.isPending}
            disabled={locked} onPress={() => resend.mutate()} />
        )}
        <Button label={t('onboarding.otp.changeNumber')} variant="ghost" fullWidth={false}
          onPress={() => router.replace('/onboarding/phone')} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', gap: space.sm },
  boxes: { flexDirection: 'row', justifyContent: 'center', gap: space.sm },
  box: {
    width: 46, height: 56, borderRadius: radius.sm + 4, borderWidth: 1.5, borderColor: 'transparent', backgroundColor: color.fill,
    alignItems: 'center', justifyContent: 'center',
  },
  boxActive: { borderColor: color.primary },
  boxError: { borderColor: color.danger },
  boxLocked: { backgroundColor: color.bg },
  digit: { fontFamily: fontFamily.headingLatin },
  caret: { position: 'absolute', width: 2, height: 24, backgroundColor: color.primary },
  hidden: { position: 'absolute', width: 1, height: 1, opacity: 0 },
});
