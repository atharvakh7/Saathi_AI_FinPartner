/**
 * S22 Saathi chat. Voice (step 26): the mic (shown when the box is empty) opens voice mode;
 * each answer has a speaker button. Reopens the latest conversation (or starts fresh after
 * "New chat"); messages newest-at-bottom with older ones loaded on scroll; glossary terms in replies
 * are tappable (TermSheet); cards (goal, budget, term, schemes, scam result, transaction draft) render
 * inside the reply; the latest reply's suggested replies show as chips. While waiting: the user's
 * message plus a "Saathi is thinking" bubble. If the AI is down the message isn't kept by the API,
 * so Try again simply resends it.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { FlatList, KeyboardAvoidingView, Platform, Pressable, StyleSheet, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useInfiniteQuery, useMutation, useQuery } from '@tanstack/react-query';
import { History, Mic, SendHorizontal, SquarePen } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import {
  getGreeting, getTerm, listChatMessages, listConversations, sendChatMessage, type ChatMessageDTO,
} from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import {
  AppText, ChatCard, Chip, ErrorBanner, Mascot, MascotBubble, MessageBubble, Screen, SkeletonCard, TermSheet,
} from '@/components';
import type { ChatCardData } from '@/components';
import { cardAction, changesMoneyData, chatKeys, clockTime, withReply } from '@/features/chat/chat';
import { invalidateFinance } from '@/features/finance/queries';
import { invalidateGoals } from '@/features/goals/goals';
import { usePlayback } from '@/features/voice/useVoice';
import { useChatStore, useUiStore } from '@/stores';
import { useLanguageStore } from '@/stores/language';
import { color, fontFor, MAX_FONT_SCALE, MIN_TOUCH, radius, shadow, space } from '@/theme';

type Row = { kind: 'msg'; msg: ChatMessageDTO } | { kind: 'pending'; text: string } | { kind: 'thinking' };

export default function Saathi() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const activeId = useChatStore((s) => s.activeConversationId);
  const fresh = useChatStore((s) => s.freshChat);
  const setActive = useChatStore((s) => s.setActiveConversation);
  const [text, setText] = useState('');
  const [pending, setPending] = useState<string | null>(null);
  const list = useRef<FlatList<Row>>(null);
  const playback = usePlayback();
  useEffect(() => () => playback.stop(), [playback.stop]); // leaving the tab stops speech

  // Reopen the latest conversation unless the user asked for a new chat.
  const convs = useQuery({ queryKey: chatKeys.conversations, queryFn: () => listConversations(), enabled: !activeId && !fresh });
  useEffect(() => {
    const latest = convs.data?.items[0];
    if (!activeId && !fresh && latest) setActive(latest.id);
  }, [convs.data, activeId, fresh, setActive]);

  const messages = useInfiniteQuery({
    queryKey: chatKeys.messages(activeId ?? 'none'),
    queryFn: ({ pageParam }) => listChatMessages(activeId!, pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
    enabled: !!activeId,
  });
  const items = useMemo(() => messages.data?.pages.flatMap((p) => p.items) ?? [], [messages.data]);
  const isNew = !activeId || (messages.isSuccess && items.length === 0);
  const greeting = useQuery({ queryKey: chatKeys.greeting(language), queryFn: () => getGreeting(language), enabled: isNew, staleTime: 10 * 60_000 });

  const send = useMutation({
    mutationFn: (msg: string) => sendChatMessage(msg, activeId),
    onMutate: (msg) => { setPending(msg); setText(''); },
    onSuccess: (reply) => {
      queryClient.setQueryData(chatKeys.messages(reply.conversation_id), (old: Parameters<typeof withReply>[0]) => withReply(old, reply));
      if (reply.conversation_id !== activeId) setActive(reply.conversation_id);
      void queryClient.invalidateQueries({ queryKey: chatKeys.conversations });
      if (changesMoneyData(reply.assistant_message.intent)) { invalidateFinance(); invalidateGoals(); }
      setPending(null);
    },
    onError: () => undefined, // the banner below offers Try again with the same text
  });
  const submit = (msg: string) => {
    const clean = msg.trim();
    if (!clean || send.isPending) return;
    send.mutate(clean);
  };

  // Newest first for the inverted list: thinking bubble, pending user text, then saved messages.
  const rows: Row[] = [
    ...(send.isPending ? [{ kind: 'thinking' } as Row] : []),
    ...(pending ? [{ kind: 'pending', text: pending } as Row] : []),
    ...items.map((msg) => ({ kind: 'msg', msg }) as Row),
  ];
  const latestAssistant = items.find((m) => m.role === 'assistant');
  const chips = send.isPending ? [] : isNew && !pending ? (greeting.data?.suggested_replies ?? []) : latestAssistant?.suggested_replies ?? [];

  const openCard = (card: ChatCardData, route?: string) => {
    const a = cardAction(card, route);
    if (!a) return;
    if (a.kind === 'term') useUiStore.getState().openTerm(a.slug);
    else if (a.kind === 'route') router.push(a.route as never);
    else useUiStore.getState().showToast(t('common.comingSoon'), 'info');
  };

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Screen scroll={false} padded={false} footer={
        <View style={styles.footerWrap}>
          {chips.length ? (
            <FlatList horizontal data={chips} keyExtractor={(c, i) => `${i}-${c}`} showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.chips} keyboardShouldPersistTaps="handled"
              renderItem={({ item }) => <Chip label={item} onPress={() => submit(item)} />} />
          ) : null}
          <Composer value={text} onChange={setText} onSend={() => submit(text)} busy={send.isPending} language={language}
            onMic={() => { playback.stop(); router.push('/voice'); }} />
        </View>
      }>
        <View style={styles.header}>
          <Mascot pose={send.isPending ? 'thinking' : 'speaking'} size={44} variant="avatar" />
          <View style={styles.flex}>
            <AppText variant="h3">{t('tabs.saathi')}</AppText>
            <AppText variant="caption" muted>{send.isPending ? t('chat.typing') : t('chat.subtitle')}</AppText>
          </View>
          <IconButton label={t('chat.history')} onPress={() => router.push('/chat/history')}><History color={color.primary} size={22} /></IconButton>
          <IconButton label={t('chat.newChat')} onPress={() => { useChatStore.getState().startNewChat(); setPending(null); send.reset(); }}>
            <SquarePen color={color.primary} size={22} />
          </IconButton>
        </View>

        <FlatList
          ref={list}
          inverted
          data={rows}
          style={styles.listBox}
          contentContainerStyle={styles.list}
          keyboardShouldPersistTaps="handled"
          keyExtractor={(r, i) => (r.kind === 'msg' ? r.msg.id : `${r.kind}-${i}`)}
          onEndReached={() => { if (messages.hasNextPage && !messages.isFetchingNextPage) void messages.fetchNextPage(); }}
          onEndReachedThreshold={0.3}
          renderItem={({ item }) => {
            if (item.kind === 'thinking') return <Thinking />;
            if (item.kind === 'pending') return <MessageBubble role="user" content={item.text} />;
            const m = item.msg;
            return (
              <MessageBubble role={m.role} content={m.content} time={clockTime(m.created_at)} highlights={m.highlighted_terms}
                onTermPress={(slug) => useUiStore.getState().openTerm(slug)}
                onSpeak={m.role === 'assistant' ? () => playback.toggle(m.id, m.content, m.language) : undefined}
                speaking={playback.speakingId === m.id}>
                {m.cards.length ? (
                  <View style={styles.cards}>
                    {m.cards.map((c, i) => <ChatCard key={i} card={c} onOpen={(route) => openCard(c, route)} />)}
                  </View>
                ) : null}
              </MessageBubble>
            );
          }}
          ListFooterComponent={
            <View style={styles.top}>
              {messages.isFetchingNextPage || (activeId && messages.isPending) ? <SkeletonCard lines={2} /> : null}
              {messages.error ? <ErrorBanner error={messages.error} onRetry={() => void messages.refetch()} /> : null}
              {isNew && !pending ? (
                greeting.data ? <MascotBubble pose="greeting" text={greeting.data.text} size={72} />
                  : greeting.isPending ? <SkeletonCard lines={2} /> : <MascotBubble pose="wave" text={t('chat.fallbackGreeting')} size={72} />
              ) : null}
              {isNew ? <AppText variant="caption" muted align="center">{t('chat.disclaimer')}</AppText> : null}
            </View>
          }
          ListHeaderComponent={send.error ? (
            <View style={styles.error}>
              <ErrorBanner error={send.error} onRetry={() => pending && send.mutate(pending)} />
            </View>
          ) : null}
        />
        <TermSheetHost />
      </Screen>
    </KeyboardAvoidingView>
  );
}

function Composer({ value, onChange, onSend, onMic, busy, language }: {
  value: string; onChange: (v: string) => void; onSend: () => void; onMic: () => void; busy: boolean;
  language: ReturnType<typeof useLanguageStore.getState>['language'];
}) {
  const { t } = useTranslation();
  const empty = value.trim().length === 0;
  const canSend = !empty && !busy;
  return (
    <View style={styles.composer}>
      <TextInput value={value} onChangeText={onChange} placeholder={t('chat.placeholder')} placeholderTextColor={color.textMuted}
        multiline maxLength={2000} maxFontSizeMultiplier={MAX_FONT_SCALE} accessibilityLabel={t('chat.placeholder')}
        style={[styles.input, { fontFamily: fontFor(language, 'body') }]}
        onSubmitEditing={onSend} blurOnSubmit={false} submitBehavior="submit" returnKeyType="send" />
      {empty ? (
        <Pressable onPress={onMic} disabled={busy} accessibilityRole="button" accessibilityLabel={t('voice.open')}
          style={[styles.send, busy && styles.sendOff]}>
          <Mic color={color.onPrimary} size={22} />
        </Pressable>
      ) : (
        <Pressable onPress={onSend} disabled={!canSend} accessibilityRole="button" accessibilityLabel={t('chat.send')}
          accessibilityState={{ disabled: !canSend }} style={[styles.send, !canSend && styles.sendOff]}>
          <SendHorizontal color={color.onPrimary} size={22} />
        </Pressable>
      )}
    </View>
  );
}

function IconButton({ label, onPress, children }: { label: string; onPress: () => void; children: React.ReactNode }) {
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={label} hitSlop={6} style={styles.iconBtn}>
      {children}
    </Pressable>
  );
}

function Thinking() {
  const { t } = useTranslation();
  const [dots, setDots] = useState(1);
  useEffect(() => {
    const id = setInterval(() => setDots((d) => (d % 3) + 1), 450);
    return () => clearInterval(id);
  }, []);
  return (
    <View style={styles.thinking} accessibilityLiveRegion="polite" accessibilityLabel={t('chat.typing')}>
      <AppText muted>{'•'.repeat(dots)}</AppText>
    </View>
  );
}

/** Bottom sheet for a tapped glossary term, in the current language. */
function TermSheetHost() {
  const slug = useUiStore((s) => s.termSheetSlug);
  const language = useLanguageStore((s) => s.language);
  const term = useQuery({ queryKey: chatKeys.term(slug ?? '', language), queryFn: () => getTerm(slug!), enabled: !!slug });
  return (
    <TermSheet visible={!!slug} loading={term.isPending} term={term.data?.term} definition={term.data?.definition}
      keyTakeaway={term.data?.key_takeaway} onClose={() => useUiStore.getState().openTerm(null)}
      onMore={slug ? () => { useUiStore.getState().openTerm(null); router.push({ pathname: '/term/[slug]', params: { slug: slug } }); } : undefined} />
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  header: {
    flexDirection: 'row', alignItems: 'center', gap: space.sm, paddingHorizontal: space.xl, paddingVertical: space.sm,
    backgroundColor: color.bg,
  },
  iconBtn: { width: MIN_TOUCH, height: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
  listBox: { flex: 1, minHeight: 0 },
  list: { paddingHorizontal: space.lg, paddingVertical: space.md, gap: space.xs },
  top: { gap: space.md, paddingBottom: space.md },
  cards: { gap: space.sm },
  error: { paddingVertical: space.sm },
  footerWrap: { gap: space.sm },
  chips: { gap: space.sm, paddingRight: space.lg },
  composer: { flexDirection: 'row', alignItems: 'flex-end', gap: space.sm },
  input: {
    flex: 1, minWidth: 0, minHeight: MIN_TOUCH, maxHeight: 120, paddingHorizontal: space.lg, paddingVertical: space.md,
    borderRadius: radius.lg, backgroundColor: color.fill, fontSize: 16, color: color.text,
    outlineWidth: 0,
  } as object,
  send: { width: MIN_TOUCH, height: MIN_TOUCH, borderRadius: MIN_TOUCH / 2, backgroundColor: color.primary, alignItems: 'center', justifyContent: 'center' },
  sendOff: { opacity: 0.4 },
  thinking: {
    alignSelf: 'flex-start', paddingHorizontal: space.lg, paddingVertical: space.sm, borderRadius: radius.md,
    backgroundColor: color.surface, marginVertical: space.xs, ...shadow,
  },
});
