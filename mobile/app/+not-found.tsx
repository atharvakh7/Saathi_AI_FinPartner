/** Unknown route (an old link, a typo): a friendly page with a way home instead of a blank screen. */
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { EmptyState, Screen } from '@/components';

export default function NotFound() {
  const { t } = useTranslation();
  return (
    <Screen title={t('common.appName')}>
      <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('tabs.home')} onAction={() => router.replace('/')} />
    </Screen>
  );
}
