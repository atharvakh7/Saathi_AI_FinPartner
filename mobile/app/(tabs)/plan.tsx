/** Placeholder until step 24 builds this tab. */
import { useTranslation } from 'react-i18next';

import { EmptyState, Screen } from '@/components';

export default function Tab() {
  const { t } = useTranslation();
  return (
    <Screen title={t('tabs.plan')}>
      <EmptyState pose="point_up" message={t('common.comingSoon')} />
    </Screen>
  );
}
