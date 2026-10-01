/** Placeholder until step 25 builds this tab. */
import { useTranslation } from 'react-i18next';

import { EmptyState, Screen } from '@/components';

export default function Tab() {
  const { t } = useTranslation();
  return (
    <Screen title={t('tabs.saathi')}>
      <EmptyState pose="speaking" message={t('common.comingSoon')} />
    </Screen>
  );
}
