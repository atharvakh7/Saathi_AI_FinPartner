/**
 * S10 Home — minimal & clean: greeting with bell (-> S13) and mascot; one hero card for this month
 * (saved, income vs spent with a thin bar, quick add); health row (money risk gauge -> S12,
 * emergency-fund ring -> S21); Top Goals; a compact debt row; the latest insights (-> S11).
 * No entries yet -> "tell me about your money". Plan, Learn, Schemes and Fraud Shield live in Services.
 */
import { Pressable, RefreshControl, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ArrowDownLeft, ArrowUpRight, Bell, ChevronRight, Plus, Wallet } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { getSummary, listGoals, listInsights, type SummaryDTO } from '@/api/endpoints';
import {
  AppText, Button, Card, ErrorBanner, InsightCard, MascotBubble, PageHeader, ProgressBar, ProgressRing, RiskGauge, Screen,
  SectionHeader, SkeletonCard,
} from '@/components';
import { financeKeys } from '@/features/finance/queries';
import { GoalRow } from '@/features/goals/GoalCard';
import { goalKeys } from '@/features/goals/goals';
import { insightKeys, insightText } from '@/features/insights/insights';
import { openInsight } from '@/features/insights/open';
import { displayMonth, inr } from '@/lib/format';
import { useMe } from '@/lib/session';
import { useLanguageStore } from '@/stores/language';
import { color, radius, space, toneColors } from '@/theme';

function greetingKey(hour: number): 'home.morning' | 'home.afternoon' | 'home.evening' {
  if (hour < 12) return 'home.morning';
  if (hour < 17) return 'home.afternoon';
  return 'home.evening';
}

const addTx = (type: 'income' | 'expense') => router.push({ pathname: '/finance/transaction', params: { type } });

export default function Home() {
  const { t, i18n } = useTranslation();
  const language = useLanguageStore((st) => st.language);
  const me = useMe();
  const summary = useQuery({ queryKey: financeKeys.summary(), queryFn: () => getSummary() });
  const goals = useQuery({ queryKey: goalKeys.list('active'), queryFn: () => listGoals('active') });
  const insights = useQuery({ queryKey: insightKeys.list('all', language), queryFn: () => listInsights('all') });
  const s = summary.data;
  const name = me.data?.user.first_name;
  const topGoals = (goals.data ?? []).filter((g) => g.status === 'active').slice(0, 3);
  const topInsights = (insights.data?.items ?? []).slice(0, 2);
  const refresh = () => { void summary.refetch(); void goals.refetch(); void insights.refetch(); };

  return (
    <Screen refreshControl={<RefreshControl refreshing={summary.isRefetching} onRefresh={refresh} />}>
      <PageHeader title={name ? t('home.hello', { name }) : t('home.helloNoName')} subtitle={t(greetingKey(new Date().getHours()))}
        pose="wave" mascotSize={52} right={<BellButton unread={s?.unread_notifications ?? 0} />} />

      {summary.isPending ? <><SkeletonCard lines={3} /><SkeletonCard lines={2} /></> : null}
      {summary.error ? <ErrorBanner error={summary.error} onRetry={refresh} /> : null}

      {s && !s.has_transactions ? (
        <Card>
          <MascotBubble pose="point_up" text={t('home.empty')} size={72} />
          <View style={styles.actions}>
            <Button label={t('home.addIncome')} onPress={() => addTx('income')} style={styles.flex} />
            <Button label={t('home.addExpense')} variant="secondary" onPress={() => addTx('expense')} style={styles.flex} />
          </View>
        </Card>
      ) : null}

      {s && s.has_transactions ? <MonthHero s={s} /> : null}

      {s && (s.risk || s.has_transactions) ? (
        <View style={styles.row}>
          <Card style={styles.half} onPress={() => router.push('/risk')} accessibilityLabel={t('risk.title')}>
            <AppText variant="small" muted numberOfLines={1}>{t('risk.title')}</AppText>
            {s.risk ? (
              <View style={styles.center}><RiskGauge score={s.risk.score} level={s.risk.level} size={120} /></View>
            ) : <AppText variant="caption" muted>{t('plan.riskEmpty')}</AppText>}
          </Card>
          <Card style={styles.half} onPress={() => router.push('/emergency-fund')} accessibilityLabel={t('plan.ef.title')}>
            <AppText variant="small" muted numberOfLines={1}>{t('plan.ef.title')}</AppText>
            <View style={styles.center}><ProgressRing pct={s.emergency_fund.pct} size={84} stroke={8} /></View>
            <AppText variant="caption" align="center" numberOfLines={1}
              tint={!s.emergency_fund.exists ? color.primaryLight : s.emergency_fund.on_track ? color.success : toneColors.warning.fg}>
              {!s.emergency_fund.exists ? t('plan.ef.setUp') : s.emergency_fund.on_track ? t('goals.onTrack') : t('goals.behind')}
            </AppText>
          </Card>
        </View>
      ) : null}

      {s ? (
        <Card>
          <SectionHeader title={t('home.topGoals')} action={(goals.data ?? []).length ? t('home.viewAll') : undefined}
            onAction={() => router.push('/goals')} />
          {topGoals.map((g) => (
            <Pressable key={g.id} onPress={() => router.push(`/goals/${g.id}`)} style={({ pressed }) => pressed && styles.pressed}>
              <GoalRow goal={g} />
            </Pressable>
          ))}
          {goals.data && topGoals.length === 0 ? (
            <Pressable onPress={() => router.push('/goals/new')} accessibilityRole="button" style={styles.listRow}>
              <View style={styles.rowIcon}><Plus color={color.primary} size={18} /></View>
              <View style={styles.flex}>
                <AppText variant="bodyMedium">{t('home.setGoal')}</AppText>
                <AppText variant="caption" muted>{t('home.setGoalHint')}</AppText>
              </View>
              <ChevronRight color={color.textMuted} size={18} />
            </Pressable>
          ) : null}
        </Card>
      ) : null}

      {s && s.has_transactions ? (
        <Pressable onPress={() => router.push('/finance/debts')} accessibilityRole="button"
          accessibilityLabel={`${t('home.debt')}: ${inr(s.debt_outstanding_inr)}`} style={({ pressed }) => [styles.debt, pressed && styles.pressed]}>
          <View style={styles.rowIcon}><Wallet color={color.primary} size={18} /></View>
          <View style={styles.flex}>
            <AppText variant="bodyMedium">{t('home.debt')}</AppText>
            <AppText variant="caption" tint={s.active_debts_count ? color.textMuted : color.success}>
              {s.active_debts_count ? t('home.debtActive', { count: s.active_debts_count }) : t('home.goodGoing')}
            </AppText>
          </View>
          <AppText variant="bodyMedium">{inr(s.debt_outstanding_inr)}</AppText>
          <ChevronRight color={color.textMuted} size={18} />
        </Pressable>
      ) : null}

      {topInsights.length ? (
        <View style={styles.insights}>
          <SectionHeader title={t('insights.title')} action={t('home.viewAll')} onAction={() => router.push('/insights')} />
          {topInsights.map((i) => {
            const text = insightText(i, language, t, (k) => i18n.exists(k));
            return <InsightCard key={i.id} tone={i.tone} title={text.title} body={text.body} unread={!i.is_read} onPress={() => openInsight(i)} />;
          })}
        </View>
      ) : null}
    </Screen>
  );
}

/** This month at a glance: saved (big), income vs spent with a thin bar, quick add. */
function MonthHero({ s }: { s: SummaryDTO }) {
  const { t } = useTranslation();
  const spentPct = s.income_inr > 0 ? (100 * s.expenses_inr) / s.income_inr : s.expenses_inr > 0 ? 100 : 0;
  return (
    <Card>
      <View style={styles.heroTop}>
        <AppText variant="small" muted style={styles.flex}>{`${displayMonth(s.month)} · ${t('home.savings')}`}</AppText>
        <Pressable onPress={() => router.push('/finance/transactions')} hitSlop={10} accessibilityRole="link">
          <AppText variant="small" tint={color.primaryLight}>{t('home.viewAll')}</AppText>
        </Pressable>
      </View>
      <AppText style={styles.big} tint={s.savings_inr < 0 ? color.danger : color.text} numberOfLines={1} adjustsFontSizeToFit>
        {inr(s.savings_inr)}
      </AppText>
      <View style={styles.row}>
        <Pressable style={styles.flow} onPress={() => router.push({ pathname: '/finance/transactions', params: { type: 'income' } })}
          accessibilityRole="button" accessibilityLabel={`${t('home.income')}: ${inr(s.income_inr)}`}>
          <View style={[styles.flowIcon, { backgroundColor: color.successTint }]}><ArrowDownLeft color={color.success} size={16} /></View>
          <View style={styles.flex}>
            <AppText variant="caption" muted>{t('home.income')}</AppText>
            <AppText variant="bodyMedium" numberOfLines={1} adjustsFontSizeToFit>{inr(s.income_inr)}</AppText>
          </View>
        </Pressable>
        <Pressable style={styles.flow} onPress={() => router.push({ pathname: '/finance/transactions', params: { type: 'expense' } })}
          accessibilityRole="button" accessibilityLabel={`${t('home.expenses')}: ${inr(s.expenses_inr)}`}>
          <View style={[styles.flowIcon, { backgroundColor: color.dangerTint }]}><ArrowUpRight color={color.danger} size={16} /></View>
          <View style={styles.flex}>
            <AppText variant="caption" muted>{t('home.expenses')}</AppText>
            <AppText variant="bodyMedium" numberOfLines={1} adjustsFontSizeToFit>{inr(s.expenses_inr)}</AppText>
          </View>
        </Pressable>
      </View>
      <View style={styles.spent}>
        <ProgressBar pct={spentPct} height={6} tint={spentPct > 90 ? color.danger : spentPct > 70 ? color.warning : color.primaryLight} />
        <AppText variant="caption" muted>{t('home.spentShare', { pct: Math.round(Math.min(spentPct, 999)) })}</AppText>
      </View>
      <View style={styles.actions}>
        <Button label={t('home.addIncome')} variant="secondary" size="sm" style={styles.flex} onPress={() => addTx('income')} />
        <Button label={t('home.addExpense')} variant="secondary" size="sm" style={styles.flex} onPress={() => addTx('expense')} />
      </View>
    </Card>
  );
}

/** Bell with the unread count (S13). */
function BellButton({ unread }: { unread: number }) {
  const { t } = useTranslation();
  return (
    <Pressable onPress={() => router.push('/notifications')} accessibilityRole="button" hitSlop={6}
      accessibilityLabel={unread ? t('notifications.unreadCount', { count: unread }) : t('notifications.title')} style={styles.bell}>
      <Bell color={color.text} size={22} />
      {unread ? (
        <View style={styles.badge}><AppText variant="caption" tint={color.onPrimary}>{unread > 9 ? '9+' : String(unread)}</AppText></View>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  pressed: { opacity: 0.7 },
  row: { flexDirection: 'row', gap: space.md },
  half: { flex: 1, minWidth: 0 },
  center: { alignItems: 'center', paddingVertical: space.xs },
  actions: { flexDirection: 'row', gap: space.md },
  heroTop: { flexDirection: 'row', alignItems: 'center' },
  big: { fontSize: 38, lineHeight: 46, fontFamily: 'Poppins_600SemiBold', letterSpacing: -1 },
  flow: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: space.sm, padding: space.md, borderRadius: radius.sm + 4, backgroundColor: color.bg },
  flowIcon: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  spent: { gap: space.xs },
  listRow: { flexDirection: 'row', alignItems: 'center', gap: space.md, paddingVertical: space.xs },
  rowIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: color.primaryTint, alignItems: 'center', justifyContent: 'center' },
  debt: {
    flexDirection: 'row', alignItems: 'center', gap: space.md, padding: space.lg, borderRadius: radius.md, backgroundColor: color.surface,
  },
  insights: { gap: space.md },
  bell: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 22, backgroundColor: color.surface },
  badge: {
    position: 'absolute', top: 4, right: 2, minWidth: 18, height: 18, borderRadius: 9, paddingHorizontal: 4,
    backgroundColor: color.danger, alignItems: 'center', justifyContent: 'center',
  },
});
