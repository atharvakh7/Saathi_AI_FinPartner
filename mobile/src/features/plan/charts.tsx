/**
 * Plan charts (wireframe "Irregular Income Planner"), plain react-native-svg:
 *  - IncomeBars: last months' income, lean months in amber.
 *  - OutlookChart: next months' expected income line with its likely range (band) and expected
 *    spending (dashed), so tight months are visible where the lines cross.
 * Each chart has a text summary for screen readers.
 */
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Line, Path, Rect } from 'react-native-svg';
import { useTranslation } from 'react-i18next';

import type { ForecastMonthDTO } from '@/api/endpoints';
import { AppText } from '@/components';
import { inr, inrShort, shortMonth } from '@/lib/format';
import { color, space } from '@/theme';

const H = 140;

export function IncomeBars({ data }: { data: { month: string; income_inr: number; is_lean: boolean }[] }) {
  const { t } = useTranslation();
  const [w, setW] = useState(0);
  const max = Math.max(1, ...data.map((d) => d.income_inr));
  const gap = 8;
  const bw = data.length ? Math.max(6, (w - gap * (data.length - 1)) / data.length) : 0;
  const summary = data.map((d) => `${shortMonth(d.month)} ${inr(d.income_inr)}${d.is_lean ? ` (${t('plan.lean')})` : ''}`).join(', ');
  return (
    <View onLayout={(e) => setW(e.nativeEvent.layout.width)} accessible accessibilityLabel={summary}>
      <AppText variant="caption" muted>{inrShort(max)}</AppText>
      {w > 0 ? (
        <Svg width={w} height={H}>
          <Line x1={0} x2={w} y1={H - 0.5} y2={H - 0.5} stroke={color.border} />
          {data.map((d, i) => {
            const h = Math.max(2, (d.income_inr / max) * (H - 8));
            return <Rect key={d.month} x={i * (bw + gap)} y={H - h} width={bw} height={h} rx={4}
              fill={d.is_lean ? color.warning : color.primaryLight} />;
          })}
        </Svg>
      ) : <View style={{ height: H }} />}
      <View style={styles.axis}>
        {data.map((d) => <AppText key={d.month} variant="caption" muted style={styles.axisLabel} numberOfLines={1}>{shortMonth(d.month)}</AppText>)}
      </View>
    </View>
  );
}

export function OutlookChart({ data }: { data: ForecastMonthDTO[] }) {
  const { t } = useTranslation();
  const [w, setW] = useState(0);
  const values = data.flatMap((d) => [d.upper_income_inr, d.expected_expense_inr, d.lower_income_inr]);
  const max = Math.max(1, ...values);
  const pad = 6;
  const x = (i: number) => (data.length <= 1 ? w / 2 : pad + (i * (w - 2 * pad)) / (data.length - 1));
  const y = (v: number) => H - 4 - (Math.max(0, v) / max) * (H - 12);
  const line = (pick: (d: ForecastMonthDTO) => number) => data.map((d, i) => `${i ? 'L' : 'M'}${x(i)},${y(pick(d))}`).join(' ');
  const band = data.length
    ? `${data.map((d, i) => `${i ? 'L' : 'M'}${x(i)},${y(d.upper_income_inr)}`).join(' ')} ${[...data].reverse().map((d, i) => `L${x(data.length - 1 - i)},${y(d.lower_income_inr)}`).join(' ')} Z`
    : '';
  const summary = data.map((d) => `${shortMonth(d.month)}: ${t('plan.income')} ${inr(d.expected_income_inr)}, ${t('plan.spending')} ${inr(d.expected_expense_inr)}`).join('; ');
  return (
    <View onLayout={(e) => setW(e.nativeEvent.layout.width)} accessible accessibilityLabel={summary}>
      <AppText variant="caption" muted>{inrShort(max)}</AppText>
      {w > 0 && data.length ? (
        <Svg width={w} height={H}>
          <Line x1={0} x2={w} y1={H - 0.5} y2={H - 0.5} stroke={color.border} />
          <Path d={band} fill={color.primaryTint} />
          <Path d={line((d) => d.expected_expense_inr)} stroke={color.danger} strokeWidth={2} strokeDasharray="5 4" fill="none" />
          <Path d={line((d) => d.expected_income_inr)} stroke={color.primaryLight} strokeWidth={3} fill="none" strokeLinejoin="round" />
        </Svg>
      ) : <View style={{ height: H }} />}
      <View style={styles.axis}>
        {data.map((d) => <AppText key={d.month} variant="caption" muted style={styles.axisLabel} numberOfLines={1}>{shortMonth(d.month)}</AppText>)}
      </View>
      <View style={styles.legend}>
        <Legend swatch={<View style={[styles.swatchLine, { backgroundColor: color.primaryLight }]} />} label={t('plan.income')} />
        <Legend swatch={<View style={[styles.swatchBand]} />} label={t('plan.likelyRange')} />
        <Legend swatch={<View style={[styles.swatchLine, { backgroundColor: color.danger }]} />} label={t('plan.spending')} />
      </View>
    </View>
  );
}

function Legend({ swatch, label }: { swatch: React.ReactNode; label: string }) {
  return <View style={styles.legendItem}>{swatch}<AppText variant="caption" muted>{label}</AppText></View>;
}

const styles = StyleSheet.create({
  axis: { flexDirection: 'row', marginTop: space.xs },
  axisLabel: { flex: 1, textAlign: 'center' },
  legend: { flexDirection: 'row', flexWrap: 'wrap', gap: space.md, marginTop: space.sm },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: space.xs },
  swatchLine: { width: 14, height: 3, borderRadius: 2 },
  swatchBand: { width: 14, height: 10, borderRadius: 2, backgroundColor: color.primaryTint },
});
