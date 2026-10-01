/**
 * Chat building blocks (spec §4.4): MessageBubble, ChatCard, TermSheet, MicButton.
 * Presentational only; data fetching and recording are wired by the chat screen (steps 25–26).
 */
import { Fragment, useEffect, useRef, useState } from 'react';
import { Modal, Pressable, StyleSheet, View } from 'react-native';
import { Mic, Square, Volume2 } from 'lucide-react-native';
import Animated, { useAnimatedStyle, useSharedValue, withRepeat, withTiming } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { displayDate, inr } from '@/lib/format';
import { splitHighlights, type TermSpan } from '@/lib/highlight';
import { color, MIN_TOUCH, radius, shadow, space, toneColors } from '@/theme';
import { AppText } from './AppText';
import { Button } from './Button';
import { ProgressRing, SchemeCard, type MatchStatus } from './data';
import { Card } from './layout';

export function MessageBubble({ role, content, time, highlights = [], onTermPress, onSpeak, speaking, children }: {
  role: 'user' | 'assistant'; content: string; time?: string; highlights?: TermSpan[];
  onTermPress?: (slug: string) => void; onSpeak?: () => void; speaking?: boolean; children?: React.ReactNode;
}) {
  const { t } = useTranslation();
  const mine = role === 'user';
  return (
    <View style={[styles.bubbleWrap, mine ? styles.right : styles.left]}>
      <View style={[styles.bubble, mine ? styles.mine : styles.theirs]}>
        <AppText tint={mine ? color.onPrimary : color.text}>
          {splitHighlights(content, highlights).map((p, i) =>
            p.slug ? (
              <AppText key={i} tint={mine ? color.onPrimary : color.primary} style={styles.term}
                onPress={onTermPress ? () => onTermPress(p.slug!) : undefined} accessibilityRole="link">
                {p.text}
              </AppText>
            ) : (
              <Fragment key={i}>{p.text}</Fragment>
            ),
          )}
        </AppText>
        {children}
        <View style={styles.meta}>
          {time ? <AppText variant="caption" tint={mine ? color.primaryTint : color.textMuted}>{time}</AppText> : null}
          {!mine && onSpeak ? (
            <Pressable onPress={onSpeak} hitSlop={10} accessibilityRole="button"
              accessibilityLabel={speaking ? t('common.stop') : t('common.listen')} style={styles.speak}>
              {speaking ? <Square color={color.primary} size={16} /> : <Volume2 color={color.primary} size={18} />}
            </Pressable>
          ) : null}
        </View>
      </View>
    </View>
  );
}

/** Cards inside assistant messages (spec §7.4 card payloads). */
export type ChatCardData =
  | { type: 'term'; payload: { slug: string; term: string; definition: string; key_takeaway: string } }
  | { type: 'fraud_result'; payload: { verdict: 'safe' | 'suspicious' | 'dangerous'; risk_score: number; summary: string; id: string } }
  | { type: 'scheme_list'; payload: { items: { id: string; name: string; benefit_summary: string; level: 'central' | 'state'; match_status: MatchStatus | null }[] } }
  | { type: 'budget_summary'; payload: { month: string; mode: string; needs_limit_inr: number; wants_limit_inr: number; savings_target_inr: number; spent_needs_inr: number; spent_wants_inr: number } }
  | { type: 'goal'; payload: { id: string; title: string; target_amount_inr: number; current_amount_inr: number; progress_pct: number; target_date: string | null } }
  | { type: 'transaction_draft'; payload: { type: 'income' | 'expense'; amount_inr: number; category: string; occurred_on: string; note: string | null } };

const VERDICT_TONE = { safe: 'positive', suspicious: 'warning', dangerous: 'danger' } as const;

export function ChatCard({ card, onOpen }: { card: ChatCardData; onOpen?: (route: string) => void }) {
  const { t } = useTranslation();
  switch (card.type) {
    case 'term':
      return (
        <Card onPress={onOpen ? () => onOpen(`/learn/term/${card.payload.slug}`) : undefined}>
          <AppText variant="bodyMedium">{card.payload.term}</AppText>
          <AppText variant="small" muted>{card.payload.definition}</AppText>
        </Card>
      );
    case 'fraud_result': {
      const tone = toneColors[VERDICT_TONE[card.payload.verdict]];
      return (
        <Card onPress={onOpen ? () => onOpen(`/fraud/result/${card.payload.id}`) : undefined} style={{ backgroundColor: tone.bg }}>
          <AppText variant="bodyMedium" tint={tone.fg}>{`${t(`verdict.${card.payload.verdict}`)} · ${card.payload.risk_score}/100`}</AppText>
          <AppText variant="small">{card.payload.summary}</AppText>
        </Card>
      );
    }
    case 'scheme_list':
      return (
        <View style={{ gap: space.sm }}>
          {card.payload.items.map((s) => (
            <SchemeCard key={s.id} name={s.name} benefit={s.benefit_summary} level={s.level} status={s.match_status}
              onPress={onOpen ? () => onOpen(`/schemes/${s.id}`) : undefined} />
          ))}
        </View>
      );
    case 'budget_summary': {
      const b = card.payload;
      return (
        <Card onPress={onOpen ? () => onOpen('/plan') : undefined}>
          <AppText variant="bodyMedium">{b.month}</AppText>
          <AppText variant="small">{`${inr(b.spent_needs_inr)} / ${inr(b.needs_limit_inr)}`}</AppText>
          <AppText variant="small">{`${inr(b.spent_wants_inr)} / ${inr(b.wants_limit_inr)}`}</AppText>
          <AppText variant="small" tint={color.success}>{inr(b.savings_target_inr)}</AppText>
        </Card>
      );
    }
    case 'goal': {
      const g = card.payload;
      return (
        <Card onPress={onOpen ? () => onOpen(`/goals/${g.id}`) : undefined} style={styles.goalCard}>
          <ProgressRing pct={g.progress_pct} size={56} stroke={6} />
          <View style={{ flex: 1 }}>
            <AppText variant="bodyMedium">{g.title}</AppText>
            <AppText variant="small" muted>{`${inr(g.current_amount_inr)} / ${inr(g.target_amount_inr)}`}</AppText>
            {g.target_date ? <AppText variant="caption" muted>{displayDate(g.target_date)}</AppText> : null}
          </View>
        </Card>
      );
    }
    case 'transaction_draft': {
      const d = card.payload;
      return (
        <Card>
          <AppText variant="h3" tint={d.type === 'income' ? color.success : color.text}>
            {`${d.type === 'income' ? '+' : '−'}${inr(d.amount_inr)}`}
          </AppText>
          <AppText variant="small">{t(`txcat.${d.category}`)}</AppText>
          <AppText variant="caption" muted>{displayDate(d.occurred_on)}{d.note ? ` · ${d.note}` : ''}</AppText>
        </Card>
      );
    }
    default:
      return null;
  }
}

/** Bottom sheet with a term's summary (opened by tapping a highlighted term). */
export function TermSheet({ visible, term, definition, keyTakeaway, loading, onClose, onMore }: {
  visible: boolean; term?: string; definition?: string; keyTakeaway?: string; loading?: boolean;
  onClose: () => void; onMore?: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose} accessibilityLabel={t('common.close')} />
      <SafeAreaView edges={['bottom']} style={styles.sheet}>
        <View style={styles.grabber} />
        {loading ? <AppText muted>{t('common.loading')}</AppText> : (
          <View style={{ gap: space.md }}>
            <AppText variant="h2">{term ?? ''}</AppText>
            <AppText>{definition ?? ''}</AppText>
            {keyTakeaway ? (
              <View style={styles.takeaway}><AppText variant="small" tint={color.primary}>{keyTakeaway}</AppText></View>
            ) : null}
            {onMore ? <Button label={t('common.seeAll')} variant="secondary" onPress={onMore} /> : null}
          </View>
        )}
      </SafeAreaView>
    </Modal>
  );
}

/**
 * Hold-to-record (or tap to start / tap to stop) mic with a pulsing ring.
 * The parent owns recording; this only reports onStart/onStop.
 */
export function MicButton({ recording, onStart, onStop, size = 64, disabled }: {
  recording: boolean; onStart: () => void; onStop: () => void; size?: number; disabled?: boolean;
}) {
  const { t } = useTranslation();
  const pulse = useSharedValue(1);
  const heldRef = useRef(false);
  const [held, setHeld] = useState(false);
  useEffect(() => {
    pulse.value = recording ? withRepeat(withTiming(1.25, { duration: 600 }), -1, true) : 1;
  }, [recording, pulse]);
  const ring = useAnimatedStyle(() => ({ transform: [{ scale: pulse.value }], opacity: recording ? 0.35 : 0 }));
  return (
    <View style={{ width: size * 1.4, height: size * 1.4, alignItems: 'center', justifyContent: 'center' }}>
      <Animated.View style={[styles.ring, { width: size, height: size, borderRadius: size / 2 }, ring]} />
      <Pressable
        disabled={disabled}
        accessibilityRole="button"
        accessibilityLabel={recording ? t('common.stop') : t('tabs.saathi')}
        accessibilityState={{ busy: recording, disabled: !!disabled }}
        onPress={() => (recording && !held ? onStop() : !recording ? onStart() : undefined)}
        onLongPress={() => { heldRef.current = true; setHeld(true); if (!recording) onStart(); }}
        onPressOut={() => { if (heldRef.current) { heldRef.current = false; setHeld(false); onStop(); } }}
        style={[styles.mic, { width: size, height: size, borderRadius: size / 2 }, recording && styles.micOn, disabled && { opacity: 0.5 }]}
      >
        {recording ? <Square color={color.onPrimary} size={size * 0.36} /> : <Mic color={color.onPrimary} size={size * 0.42} />}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  bubbleWrap: { flexDirection: 'row', marginVertical: space.xs },
  left: { justifyContent: 'flex-start' },
  right: { justifyContent: 'flex-end' },
  bubble: { maxWidth: '85%', padding: space.md, borderRadius: radius.md, gap: space.sm },
  mine: { backgroundColor: color.primary, borderBottomRightRadius: radius.sm },
  theirs: { backgroundColor: color.surface, borderWidth: 1, borderColor: color.border, borderBottomLeftRadius: radius.sm },
  term: { textDecorationLine: 'underline', textDecorationStyle: 'dotted' },
  meta: { flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end', gap: space.sm },
  speak: { minWidth: 32, minHeight: 32, alignItems: 'center', justifyContent: 'center' },
  goalCard: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  backdrop: { flex: 1, backgroundColor: 'rgba(20,35,43,0.4)' },
  sheet: {
    backgroundColor: color.surface, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg,
    paddingHorizontal: space.xl, paddingBottom: space.xl,
  },
  grabber: { alignSelf: 'center', width: 40, height: 4, borderRadius: 2, backgroundColor: color.border, marginVertical: space.md },
  takeaway: { backgroundColor: color.primaryTint, padding: space.md, borderRadius: radius.sm },
  ring: { position: 'absolute', backgroundColor: color.primaryLight },
  mic: { backgroundColor: color.primary, alignItems: 'center', justifyContent: 'center', minWidth: MIN_TOUCH, minHeight: MIN_TOUCH, ...shadow },
  micOn: { backgroundColor: color.danger },
});
