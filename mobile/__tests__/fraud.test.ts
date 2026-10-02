import { imageMeta, textProblem, VERDICT_TONE } from '@/features/fraud/fraud';

test('message length rules match the API (10–5000)', () => {
  expect(textProblem('short')).toBe('tooShort');
  expect(textProblem('          ab        ')).toBe('tooShort'); // trimmed
  expect(textProblem('Your KYC is pending, click here')).toBeNull();
  expect(textProblem('x'.repeat(5001))).toBe('tooLong');
});

test('screenshot upload names and types', () => {
  expect(imageMeta('file:///a/b/shot.PNG')).toEqual({ name: 'screenshot.png', type: 'image/png' });
  expect(imageMeta('blob:http://x', 'image/webp')).toEqual({ name: 'screenshot.webp', type: 'image/webp' });
  expect(imageMeta('content://media/123')).toEqual({ name: 'screenshot.jpg', type: 'image/jpeg' });
  expect(imageMeta('x.gif', 'image/gif').type).toBe('image/jpeg'); // the API checks the bytes
});

test('verdict colours: icon + text carry the meaning, colour supports it', () => {
  expect(VERDICT_TONE).toEqual({ safe: 'positive', suspicious: 'warning', dangerous: 'danger' });
});
