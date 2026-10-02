/**
 * Insights and notifications carry the API's route names (spec §4.6 / backend: "/transactions",
 * "/plan/emergency-fund", "/schemes/results", …). Map them to this app's screens; unknown -> null.
 */
const STATIC: Record<string, string> = {
  '/home': '/home',
  '/plan': '/plan',
  '/learn': '/learn',
  '/goals': '/goals',
  '/insights': '/insights',
  '/notifications': '/notifications',
  '/transactions': '/finance/transactions',
  '/transactions/new': '/finance/transaction?type=income',
  '/debts': '/finance/debts',
  '/plan/emergency-fund': '/emergency-fund',
  '/risk': '/risk',
  '/schemes': '/schemes',
  '/schemes/results': '/schemes/matches',
  '/fraud': '/fraud',
  '/chat': '/saathi',
  '/saathi': '/saathi',
};

const DYNAMIC: [RegExp, (m: RegExpExecArray) => string][] = [
  [/^\/goals\/([0-9a-f-]{36})$/i, (m) => `/goals/${m[1]}`],
  [/^\/schemes\/([0-9a-f-]{36})$/i, (m) => `/schemes/${m[1]}`],
  [/^\/fraud\/result\/([0-9a-f-]{36})$/i, (m) => `/fraud/result/${m[1]}`],
  [/^\/learn\/term\/([a-z0-9-]+)$/i, (m) => `/term/${m[1]}`],
  [/^\/learn\/lesson\/([0-9a-f-]{36})$/i, (m) => `/lesson/${m[1]}`],
];

export function appRoute(apiRoute: string | null | undefined): string | null {
  if (!apiRoute) return null;
  const path = apiRoute.split('?')[0]!.replace(/\/+$/, '') || '/';
  if (STATIC[path]) return STATIC[path]!;
  for (const [re, to] of DYNAMIC) {
    const m = re.exec(path);
    if (m) return to(m);
  }
  return null;
}
