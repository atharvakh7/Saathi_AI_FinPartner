/** S10 Home — placeholder until steps 21–22 build the tabs and Home. */
import { useTranslation } from 'react-i18next';

import { AppText, Mascot, Screen } from '@/components';

export default function Home() {
  const { t } = useTranslation();
  return (
    <Screen title={t('tabs.home')}>
      <Mascot pose="point_up" size={160} />
      <AppText variant="h2" align="center">{t('common.appName')}</AppText>
    </Screen>
  );
}
