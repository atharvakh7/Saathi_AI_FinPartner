/**
 * Component gallery (development builds only): every shared component in every language, used to
 * check layout, fonts and Indic text rendering. Open saathi://dev/gallery or /dev/gallery on web.
 */
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Redirect } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Landmark, PiggyBank, TrendingUp, Wallet } from 'lucide-react-native';

import { ApiError } from '@/api/client';
import {
  AmountInput, AppText, Button, Card, ChatCard, Chip, EmptyState, ErrorBanner, InsightCard, LanguageOption, Mascot,
  MascotBubble, MessageBubble, MetricCard, MicButton, ProgressRing, RiskGauge, Screen, SchemeCard, SegmentedTabs, Select,
  SkeletonCard, StepList, TextField,
} from '@/components';
import { LANGUAGES } from '@/i18n';
import { inr } from '@/lib/format';
import { useLanguageStore } from '@/stores/language';
import { useUiStore } from '@/stores';
import { color, space } from '@/theme';

export default function Gallery() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const [tab, setTab] = useState<'all' | 'savings' | 'spending' | 'goals'>('all');
  const [amount, setAmount] = useState<number | null>(124000);
  const [occupation, setOccupation] = useState<string | null>('farmer');
  const [recording, setRecording] = useState(false);
  if (!__DEV__) return <Redirect href="/" />;

  return (
    <Screen title={t('gallery.title')} back>
      <View style={styles.wrap}>
        {LANGUAGES.map((l) => (
          <Chip key={l} label={t(`language.${l}`)} selected={l === language} onPress={() => void setLanguage(l, { syncServer: false })} />
        ))}
      </View>
      <AppText variant="h1">{t('common.appName')}</AppText>
      <AppText variant="h2">{t('risk.title')}</AppText>
      <AppText>{t('insight.I01.body', { pct: 15, amt: '1,200' })}</AppText>
      <AppText variant="caption" muted>{t('scheme.disclaimer')}</AppText>

      <View style={styles.wrap}>
        {(['wave', 'point_up', 'shield', 'listening', 'speaking', 'thumbs_up', 'thinking'] as const).map((p) => (
          <Mascot key={p} pose={p} size={72} bounce={false} />
        ))}
      </View>
      <MascotBubble pose="wave" text={t('language.greeting.' + language)} />

      <Button label={t('common.continue')} onPress={() => useUiStore.getState().showToast(t('common.done'), 'success')} />
      <Button label={t('common.cancel')} variant="secondary" />
      <Button label={t('common.tryAgain')} variant="ghost" />
      <Button label={t('common.delete')} variant="danger" loading />

      <TextField label={t('eligibility.q.age_years')} placeholder="35" keyboardType="number-pad" helper={t('common.optional')} />
      <TextField label={t('eligibility.field.state_code')} error={t('errors.VALIDATION_ERROR')} prefix="+91" />
      <AmountInput label={t('eligibility.field.declared_monthly_income_max_inr')} value={amount} onChange={setAmount} />
      <AppText variant="small" muted>{inr(amount)}</AppText>
      <Select
        label={t('eligibility.q.occupation_type')}
        value={occupation}
        onChange={setOccupation}
        options={['farmer', 'student', 'gig_worker', 'senior_citizen', 'small_business_owner', 'salaried', 'other']
          .map((v) => ({ value: v, label: t(`options.occupation.${v}`) }))}
      />
      {LANGUAGES.map((l) => (
        <LanguageOption key={l} language={l} selected={l === language} onPress={() => void setLanguage(l, { syncServer: false })} />
      ))}

      <SegmentedTabs
        value={tab}
        onChange={setTab}
        options={[
          { value: 'all', label: t('common.seeAll') },
          { value: 'savings', label: t('txcat.other_income') },
          { value: 'spending', label: t('txcat.food') },
          { value: 'goals', label: t('goalcat.custom') },
        ]}
      />
      <View style={styles.row}>
        <MetricCard icon={<Wallet color={color.primary} size={20} />} label={t('txcat.salary')} value={inr(24000)} subtitle={t('common.today')} />
        <MetricCard icon={<PiggyBank color={color.success} size={20} />} label={t('goalcat.emergency_fund')} value={inr(9440)} tone="positive" />
      </View>
      <View style={styles.row}>
        <ProgressRing pct={70} label={t('goalcat.emergency_fund')} />
        <ProgressRing pct={35} size={64} stroke={7} tint={color.warning} />
      </View>
      <RiskGauge score={2.1} level="low" />
      <RiskGauge score={3.8} level="high" size={180} />

      <InsightCard tone="warning" title={t('insight.I01.title')} body={t('insight.I01.body', { pct: 15, amt: '1,200' })}
        ctaLabel={t('common.seeAll')} onPress={() => undefined} unread />
      <InsightCard tone="positive" title={t('insight.I04.title')} body={t('insight.I04.body', { pct: 20 })} />
      <InsightCard tone="info" title={t('insight.I07.title')} body={t('insight.I07.body')} />

      <SchemeCard name="PM-KISAN" benefit="₹6,000 per year in three installments" level="central" status="eligible" onPress={() => undefined} />
      <SchemeCard name="Namo Shetkari" benefit="Additional ₹6,000 per year" level="state" status="possibly_eligible"
        needs={[t('eligibility.field.is_income_tax_payer')]} />
      <StepList steps={[{ title: t('common.continue'), description: t('scheme.disclaimer') }, { title: t('common.done') }]} />

      <MessageBubble role="user" content="SIP kya hota hai?" time="10:02" />
      <MessageBubble role="assistant" content="SIP means putting a small fixed amount into a mutual fund every month." time="10:02"
        highlights={[{ slug: 'sip', surface: 'SIP', start: 0, end: 3 }, { slug: 'mutual-fund', surface: 'mutual fund', start: 45, end: 56 }]}
        onTermPress={(slug) => useUiStore.getState().showToast(slug)} onSpeak={() => undefined}>
        <ChatCard card={{ type: 'transaction_draft', payload: { type: 'income', amount_inr: 4500, category: 'crop_sale', occurred_on: '2026-09-30', note: 'onions' } }} />
      </MessageBubble>
      <ChatCard card={{ type: 'fraud_result', payload: { id: 'x', verdict: 'dangerous', risk_score: 90, summary: t('verdict.subtitle.dangerous') } }} />
      <ChatCard card={{ type: 'goal', payload: { id: 'g', title: t('goalcat.farm_equipment'), target_amount_inr: 300000, current_amount_inr: 45000, progress_pct: 15, target_date: '2028-10-01' } }} />
      <View style={styles.center}>
        <MicButton recording={recording} onStart={() => setRecording(true)} onStop={() => setRecording(false)} />
      </View>

      <ErrorBanner error={new ApiError('UPSTREAM_AI_UNAVAILABLE', 'x', 503)} onRetry={() => undefined} />
      <ErrorBanner error={new ApiError('NETWORK', 'x')} />
      <SkeletonCard />
      <Card><AppText>{t('gallery.sample')}</AppText><TrendingUp color={color.primary} /><Landmark color={color.primary} /></Card>
      <EmptyState pose="thumbs_up" message={t('insight.I07.body')} actionLabel={t('common.continue')} onAction={() => undefined} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  row: { flexDirection: 'row', gap: space.md, alignItems: 'center' },
  center: { alignItems: 'center' },
});
