/** S04 Phone Entry: +91 and 10 digits, Send OTP (spec §4.7). */
import { useState } from 'react';
import { router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { requestOtp } from '@/api/endpoints';
import { AppText, Button, ErrorBanner, MascotBubble, Screen, TextField } from '@/components';
import { MOBILE_RE } from '@/lib/constants';

export default function Phone() {
  const { t } = useTranslation();
  const [phone, setPhone] = useState('');
  const [touched, setTouched] = useState(false);
  const valid = MOBILE_RE.test(phone);
  const send = useMutation({
    mutationFn: () => requestOtp(`+91${phone}`),
    onSuccess: (res) => router.push({ pathname: '/onboarding/otp', params: { phone, resend: String(res.resend_after_sec) } }),
  });
  const err = send.error;
  const rateLimited = err instanceof ApiError && err.code === 'RATE_LIMITED';

  return (
    <Screen back
      footer={
        <Button label={t('onboarding.phone.send')} loading={send.isPending}
          disabled={!valid} onPress={() => { setTouched(true); if (valid) send.mutate(); }} />
      }>
      <MascotBubble pose="wave" text={t('onboarding.phone.bubble')} />
      <AppText variant="h2">{t('onboarding.phone.title')}</AppText>
      <TextField
        label={t('onboarding.phone.label')}
        prefix="+91"
        value={phone}
        onChangeText={(v) => setPhone(v.replace(/\D/g, '').slice(0, 10))}
        onBlur={() => setTouched(true)}
        keyboardType="number-pad"
        textContentType="telephoneNumber"
        autoComplete="tel"
        maxLength={10}
        placeholder="98765 43210"
        error={touched && phone.length > 0 && !valid ? t('errors.phone_invalid') : null}
        helper={t('onboarding.phone.helper')}
      />
      {err ? (
        rateLimited && err.retryAfterSec
          ? <ErrorBanner message={t('onboarding.phone.waitSeconds', { count: err.retryAfterSec })} />
          : <ErrorBanner error={err} onRetry={() => send.mutate()} />
      ) : null}
    </Screen>
  );
}
