import { clock, MAX_RECORDING_SEC, speechLanguage, uploadMeta } from '@/features/voice/voice';

test('voice helpers', () => {
  expect(MAX_RECORDING_SEC).toBeLessThan(60); // the API rejects > 60 s
  expect(uploadMeta('web')).toEqual({ name: 'voice.webm', type: 'audio/webm' });
  expect(uploadMeta('android')).toEqual({ name: 'voice.m4a', type: 'audio/m4a' });
  expect(speechLanguage('ta')).toBe('ta-IN');
  expect(speechLanguage('hi')).toBe('hi-IN');
  expect(speechLanguage(null)).toBe('en-IN');
  expect(clock(7.9)).toBe('0:07');
  expect(clock(59)).toBe('0:59');
  expect(clock(-1)).toBe('0:00');
});
