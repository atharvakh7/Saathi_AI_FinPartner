/** Full Privacy Notice (Suggested, spec S06): GET /legal/privacy-notice?lang= rendered as Markdown. */
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { getPrivacyNotice } from '@/api/endpoints';
import { ErrorBanner, Markdown, Screen, SkeletonCard } from '@/components';
import { useLanguageStore } from '@/stores/language';

export default function Privacy() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const notice = useQuery({ queryKey: ['privacy', language], queryFn: () => getPrivacyNotice(language), staleTime: Infinity });
  return (
    <Screen title={t('onboarding.consent.privacyTitle')} back>
      {notice.isPending ? <SkeletonCard lines={8} /> : null}
      {notice.error ? <ErrorBanner error={notice.error} onRetry={() => void notice.refetch()} /> : null}
      {notice.data ? <Markdown source={notice.data.markdown} /> : null}
    </Screen>
  );
}
