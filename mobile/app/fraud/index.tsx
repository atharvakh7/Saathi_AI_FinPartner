/**
 * S28 Fraud Shield (wireframe "Fraud Detection Hub"): paste a message (10–5000 characters) or pick a
 * screenshot, say where it came from (WhatsApp / SMS / Other), Check -> S30 result. While checking
 * (S29) the shield mascot says so. Recent checks below, History (S31) in the header. Sharing straight
 * from WhatsApp (share intent) needs a development build and is deferred.
 */
import { useState } from 'react';
import { Platform, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { useMutation, useQuery } from '@tanstack/react-query';
import { History, ImageUp, ShieldCheck } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { analyzeImage, analyzeText, listFraudChecks, type FraudCheckDTO, type PickedImage, type SourceApp } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, Card, Chip, ErrorBanner, MascotBubble, PageHeader, Screen, SectionHeader, TextField } from '@/components';
import { FraudRow } from '@/features/fraud/parts';
import { fraudKeys, imageMeta, MAX_IMAGE_BYTES, MAX_TEXT, textProblem } from '@/features/fraud/fraud';
import { useLanguageStore } from '@/stores/language';
import { color, MIN_TOUCH, space } from '@/theme';

const SOURCES: SourceApp[] = ['whatsapp', 'sms', 'other'];

export default function FraudShield() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const [text, setText] = useState('');
  const [source, setSource] = useState<SourceApp>('whatsapp');
  const [showErr, setShowErr] = useState(false);
  const [imageNote, setImageNote] = useState<string | null>(null);
  const recent = useQuery({ queryKey: fraudKeys.checks, queryFn: () => listFraudChecks() });
  const done = (res: FraudCheckDTO) => {
    queryClient.setQueryData(fraudKeys.check(res.id), res);
    void queryClient.invalidateQueries({ queryKey: fraudKeys.checks });
    setText('');
    setShowErr(false);
    router.push({ pathname: '/fraud/result/[id]', params: { id: res.id } });
  };
  const checkText = useMutation({ mutationFn: () => analyzeText(text.trim(), source, language), onSuccess: done });
  const checkImage = useMutation({ mutationFn: (img: PickedImage) => analyzeImage(img, source, language), onSuccess: done });
  const busy = checkText.isPending || checkImage.isPending;
  const problem = textProblem(text);
  const error = checkText.error ?? checkImage.error;

  const pick = async () => {
    setImageNote(null);
    const res = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.9, allowsEditing: false });
    if (res.canceled || !res.assets[0]) return;
    const a = res.assets[0];
    if (a.fileSize && a.fileSize > MAX_IMAGE_BYTES) { setImageNote(t('fraud.imageTooBig')); return; }
    const meta = imageMeta(a.fileName ?? a.uri, a.mimeType);
    if (Platform.OS === 'web') {
      const blob = await (await fetch(a.uri)).blob();
      if (blob.size > MAX_IMAGE_BYTES) { setImageNote(t('fraud.imageTooBig')); return; }
      checkImage.mutate({ blob, name: meta.name });
    } else {
      checkImage.mutate({ uri: a.uri, ...meta });
    }
  };
  const submit = () => {
    setShowErr(true);
    if (!problem) checkText.mutate();
  };
  const errorMessage = error instanceof ApiError
    ? error.code === 'OCR_NO_TEXT' ? t('errors.OCR_NO_TEXT')
      : error.code === 'UPSTREAM_AI_UNAVAILABLE' && checkImage.error ? t('fraud.ocrUnavailable') : undefined
    : undefined;

  return (
    <Screen back right={
      <Button label={t('fraud.history')} variant="ghost" size="sm" fullWidth={false} icon={<History color={color.primary} size={18} />}
        onPress={() => router.push('/fraud/history')} />
    }>
      <PageHeader title={t('fraud.title')} subtitle={t('fraud.subtitle')} pose="shield" />
      {busy ? (
        <Card style={styles.checking}>
          <MascotBubble pose="shield" size={80} text={checkImage.isPending ? t('fraud.readingImage') : t('fraud.checking')} />
        </Card>
      ) : (
        <>
          <AppText muted>{t('fraud.intro')}</AppText>
          <TextField label={t('fraud.pasteLabel')} value={text} onChangeText={setText} multiline maxLength={MAX_TEXT}
            placeholder={t('fraud.pastePlaceholder')}
            error={showErr && problem ? t(problem === 'tooShort' ? 'fraud.tooShort' : 'fraud.tooLong') : null} />
          <View style={styles.chips}>
            <AppText variant="small" muted>{t('fraud.from')}</AppText>
            {SOURCES.map((s) => <Chip key={s} label={t(`fraud.source.${s}`)} selected={source === s} onPress={() => setSource(s)} />)}
          </View>
          <Button label={t('fraud.check')} icon={<ShieldCheck color={color.onPrimary} size={20} />} onPress={submit} />
          <Button label={t('fraud.uploadScreenshot')} variant="secondary" icon={<ImageUp color={color.primary} size={20} />} onPress={() => void pick()} />
          {imageNote ? <AppText variant="small" tint={color.danger}>{imageNote}</AppText> : null}
        </>
      )}
      {error && !busy ? <ErrorBanner error={error} message={errorMessage} /> : null}

      {recent.data?.items.length ? (
        <>
          <SectionHeader title={t('fraud.recent')} action={t('home.viewAll')} onAction={() => router.push('/fraud/history')} />
          {recent.data.items.slice(0, 3).map((c) => <FraudRow key={c.id} check={c} />)}
        </>
      ) : null}
      <AppText variant="caption" muted align="center" style={styles.help}>{t('verdict.helpline')}</AppText>
    </Screen>
  );
}

const styles = StyleSheet.create({
  checking: { minHeight: MIN_TOUCH * 3, justifyContent: 'center' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space.sm },
  help: { marginTop: space.sm },
});
