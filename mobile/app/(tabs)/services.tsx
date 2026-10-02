/**
 * Services tab (wireframe bottom bar "Services"): everything beyond Home, grouped —
 * Plan & protect (Income Planner, Risk Report, Emergency Fund, Fraud Shield),
 * Discover (Scheme Scout, Learn, Insights), Your money (Transactions, Debts, Add entry).
 */
import { Pressable, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import {
  BookOpen, ChartNoAxesColumn, CirclePlus, Gauge, Landmark, Lightbulb, ReceiptText, ShieldAlert, ShieldCheck, Wallet,
  type LucideIcon,
} from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { AppText, PageHeader, Screen } from '@/components';
import { color, radius, shadow, space } from '@/theme';

type Item = { key: string; icon: LucideIcon; route: string };

const SECTIONS: { title: string; items: Item[] }[] = [
  { title: 'services.planProtect', items: [
    { key: 'planner', icon: ChartNoAxesColumn, route: '/plan' },
    { key: 'risk', icon: Gauge, route: '/risk' },
    { key: 'emergency', icon: ShieldCheck, route: '/emergency-fund' },
    { key: 'fraud', icon: ShieldAlert, route: '/fraud' },
  ] },
  { title: 'services.discover', items: [
    { key: 'schemes', icon: Landmark, route: '/schemes' },
    { key: 'learn', icon: BookOpen, route: '/learn' },
    { key: 'insights', icon: Lightbulb, route: '/insights' },
  ] },
  { title: 'services.yourMoney', items: [
    { key: 'transactions', icon: ReceiptText, route: '/finance/transactions' },
    { key: 'debts', icon: Wallet, route: '/finance/debts' },
    { key: 'addEntry', icon: CirclePlus, route: '/finance/transaction?type=expense' },
  ] },
];

export default function Services() {
  const { t } = useTranslation();
  return (
    <Screen>
      <PageHeader title={t('services.title')} subtitle={t('services.subtitle')} pose="point_up" />
      {SECTIONS.map((section) => (
        <View key={section.title} style={styles.section}>
          <AppText variant="small" muted style={styles.sectionTitle}>{t(section.title).toUpperCase()}</AppText>
          <View style={styles.grid}>
            {section.items.map((it) => (
              <Pressable key={it.key} onPress={() => router.push(it.route as never)} accessibilityRole="button"
                accessibilityLabel={t(`services.item.${it.key}.title`)} style={({ pressed }) => [styles.tile, pressed && styles.pressed]}>
                <View style={styles.icon}><it.icon color={color.primary} size={22} /></View>
                <AppText variant="bodyMedium" numberOfLines={2}>{t(`services.item.${it.key}.title`)}</AppText>
                <AppText variant="caption" muted numberOfLines={2}>{t(`services.item.${it.key}.hint`)}</AppText>
              </Pressable>
            ))}
          </View>
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: { gap: space.md },
  sectionTitle: { letterSpacing: 0.6 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: space.md },
  tile: {
    width: '48.3%', minHeight: 128, padding: space.lg, gap: space.xs, borderRadius: radius.md,
    backgroundColor: color.surface, ...shadow,
  },
  icon: {
    width: 44, height: 44, borderRadius: 14, backgroundColor: color.primaryTint, alignItems: 'center', justifyContent: 'center',
    marginBottom: space.sm,
  },
  pressed: { opacity: 0.85, transform: [{ scale: 0.99 }] },
});
