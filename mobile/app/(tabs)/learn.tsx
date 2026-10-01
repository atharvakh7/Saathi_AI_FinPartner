/** Placeholder until step 27 builds this tab. */
import { useTranslation } from 'react-i18next';

import { EmptyState, Screen } from '@/components';

export default function Tab() {
  const { t } = useTranslation();
  return (
    <Screen title={t('tabs.learn')}>
      <EmptyState pose="thumbs_up" message={t('common.comingSoon')} />
    </Screen>
  );
}
