// expo-secure-store has no native module under Jest: an in-memory stand-in.
const mockStore = new Map();
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(async (k) => (mockStore.has(k) ? mockStore.get(k) : null)),
  setItemAsync: jest.fn(async (k, v) => { mockStore.set(k, v); }),
  deleteItemAsync: jest.fn(async (k) => { mockStore.delete(k); }),
}));
