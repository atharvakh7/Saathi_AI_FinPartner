/**
 * Minimal Markdown for static legal/lesson text: #/##/### headings, "-"/"*" bullets, numbered
 * items, paragraphs and **bold**. Enough for the privacy notice and lessons; no links or images.
 */
import { StyleSheet, View } from 'react-native';

import { color, space } from '@/theme';
import { AppText } from './AppText';

function Inline({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith('**') && p.endsWith('**')
          ? <AppText key={i} variant="bodyMedium">{p.slice(2, -2)}</AppText>
          : p,
      )}
    </>
  );
}

export function Markdown({ source }: { source: string }) {
  const blocks: { kind: 'h1' | 'h2' | 'h3' | 'li' | 'ol' | 'p'; text: string; n?: string }[] = [];
  let para: string[] = [];
  const flush = () => {
    if (para.length) blocks.push({ kind: 'p', text: para.join(' ') });
    para = [];
  };
  for (const raw of source.split(/\r?\n/)) {
    const line = raw.trim();
    let m: RegExpExecArray | null;
    if (!line) flush();
    else if ((m = /^(#{1,3})\s+(.*)$/.exec(line))) {
      flush();
      blocks.push({ kind: (['h1', 'h2', 'h3'] as const)[m[1]!.length - 1]!, text: m[2]! });
    } else if ((m = /^[-*]\s+(.*)$/.exec(line))) {
      flush();
      blocks.push({ kind: 'li', text: m[1]! });
    } else if ((m = /^(\d+)[.)]\s+(.*)$/.exec(line))) {
      flush();
      blocks.push({ kind: 'ol', text: m[2]!, n: m[1]! });
    } else para.push(line);
  }
  flush();
  return (
    <View style={styles.wrap}>
      {blocks.map((b, i) => {
        if (b.kind === 'h1' || b.kind === 'h2' || b.kind === 'h3') {
          return <AppText key={i} variant={b.kind} accessibilityRole="header" style={styles.heading}>{b.text}</AppText>;
        }
        if (b.kind === 'li' || b.kind === 'ol') {
          return (
            <View key={i} style={styles.item}>
              <AppText muted>{b.kind === 'ol' ? `${b.n}.` : '•'}</AppText>
              <AppText style={styles.flex}><Inline text={b.text} /></AppText>
            </View>
          );
        }
        return <AppText key={i}><Inline text={b.text} /></AppText>;
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: space.md },
  heading: { marginTop: space.sm, color: color.text },
  item: { flexDirection: 'row', gap: space.sm, paddingLeft: space.xs },
  flex: { flex: 1 },
});
