/** S37 Language (spec §4.7): radio list with a greeting in each language; Apply -> PATCH /me. */
import { useState } from 'react';
import { router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { patchMe } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, ErrorBanner, LanguageOption, MascotBubble, Screen } from '@/components';
import { LANGUAGES, type Language } from '@/i18n';
import { ME_KEY } from '@/lib/session';
import { useLanguageStore } from '@/stores/language';
import { useSessionStore } from '@/stores/session';

const ORDER: Language[] = ['hi', 'mr', 'ta', 'en'];

export default function LanguageScreen() {
  const { t } = useTranslation();
  const current = useLanguageStore((s) => s.language);
  const [choice, setChoice] = useState<Language>(current);
  const apply = useMutation({
    mutationFn: async () => {
      const user = await patchMe({ preferred_language: choice }); // server first: a failure keeps the old language
      useSessionStore.getState().setUser(user);
      await useLanguageStore.getState().setLanguage(choice, { syncServer: false });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries(); // server text (insights, schemes…) is per language
      router.back();
    },
  });

  return (
    <Screen title={t('settings.language.title')} back
      footer={<Button label={t('settings.language.apply')} disabled={choice === current} loading={apply.isPending}
        onPress={() => apply.mutate()} />}>
      <AppText variant="h2">{t('settings.language.header')}</AppText>
      {ORDER.filter((l) => LANGUAGES.includes(l)).map((l) => (
        <LanguageOption key={l} language={l} selected={choice === l} onPress={() => setChoice(l)} />
      ))}
      {apply.error ? <ErrorBanner error={apply.error} onRetry={() => apply.mutate()} /> : null}
      <MascotBubble pose="speaking" text={t('settings.language.bubble')} />
    </Screen>
  );
}
