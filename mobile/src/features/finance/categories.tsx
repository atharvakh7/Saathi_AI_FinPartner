/** Category icons and the S15 category grid (icon + name tiles, 3 per row). */
import { Pressable, StyleSheet, View } from 'react-native';
import {
  Bike, Briefcase, Building2, Bus, CircleDollarSign, CircleEllipsis, CreditCard, Gift, GraduationCap, HandCoins,
  HeartPulse, House, Landmark, PiggyBank, Repeat, ShieldCheck, Sprout, Store, Ticket, Users, UtensilsCrossed,
  Wallet, Wheat, Zap, type LucideIcon,
} from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { AppText } from '@/components';
import { CATEGORIES_BY_TYPE, type DebtType, type TxCategory, type TxType } from '@/lib/constants';
import { color, MIN_TOUCH, radius, shadow, space } from '@/theme';

export const CATEGORY_ICON: Record<TxCategory, LucideIcon> = {
  crop_sale: Wheat, wages: HandCoins, salary: Briefcase, gig_payout: Bike, allowance: Gift, pension: PiggyBank,
  business: Store, other_income: CircleDollarSign,
  food: UtensilsCrossed, housing_rent: House, utilities: Zap, transport: Bus, health: HeartPulse,
  education: GraduationCap, farm_inputs: Sprout, debt_repayment: Landmark, insurance_premium: ShieldCheck,
  subscriptions: Repeat, entertainment: Ticket, other_expense: CircleEllipsis,
};

export const DEBT_ICON: Record<DebtType, LucideIcon> = {
  bank_loan: Building2, kisan_credit_card: Sprout, credit_card: CreditCard, microfinance: Users,
  moneylender: Wallet, family_friend: Users, other: CircleEllipsis,
};

export function CategoryIcon({ category, type, size = 40 }: { category: TxCategory; type: TxType; size?: number }) {
  const Icon = CATEGORY_ICON[category] ?? CircleEllipsis;
  const income = type === 'income';
  return (
    <View style={[styles.badge, { width: size, height: size, borderRadius: size * 0.3 },
      { backgroundColor: income ? color.successTint : color.primaryTint }]}>
      <Icon color={income ? color.success : color.primary} size={size * 0.5} />
    </View>
  );
}

export function CategoryGrid({ type, value, onChange, error }: {
  type: TxType; value: TxCategory | null; onChange: (c: TxCategory) => void; error?: string | null;
}) {
  const { t } = useTranslation();
  return (
    <View style={styles.wrap}>
      <AppText variant="small">{t('finance.form.category')}</AppText>
      <View style={styles.grid} accessibilityRole="radiogroup">
        {CATEGORIES_BY_TYPE[type].map((c) => {
          const on = c === value;
          const Icon = CATEGORY_ICON[c];
          return (
            <Pressable key={c} onPress={() => onChange(c)} accessibilityRole="radio" accessibilityState={{ checked: on }}
              accessibilityLabel={t(`txcat.${c}`)} style={[styles.tile, on && styles.tileOn]}>
              <Icon color={on ? color.onPrimary : color.primary} size={22} />
              <AppText variant="caption" tint={on ? color.onPrimary : color.text} align="center" numberOfLines={2}>
                {t(`txcat.${c}`)}
              </AppText>
            </Pressable>
          );
        })}
      </View>
      {error ? <AppText variant="caption" tint={color.danger}>{error}</AppText> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { alignItems: 'center', justifyContent: 'center' },
  wrap: { gap: space.xs },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  tile: {
    width: '31%', flexGrow: 1, minHeight: MIN_TOUCH + 28, padding: space.sm, gap: space.xs, borderRadius: radius.md,
    borderWidth: 1.5, borderColor: 'transparent', backgroundColor: color.surface, alignItems: 'center', justifyContent: 'center', ...shadow,
  },
  tileOn: { backgroundColor: color.primary, borderColor: color.primary },
});
