type CacheEntry<T> = {
  data: T;
  timestamp: number;
};

const cache = new Map<string, CacheEntry<unknown>>();
const pendingRequests = new Map<string, Promise<unknown>>();

/**
 * Fetch data with in-memory caching and request deduplication.
 * @param key Unique key for the resource
 * @param fetcher Function returning the promise for the request
 * @param ttlMs Time-to-live in milliseconds (default 15,000ms = 15s)
 */
export async function fetchWithCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlMs = 15000
): Promise<T> {
  const cached = cache.get(key);
  const now = Date.now();

  if (cached && now - cached.timestamp < ttlMs) {
    return cached.data as T;
  }

  if (pendingRequests.has(key)) {
    return pendingRequests.get(key) as Promise<T>;
  }

  const promise = (async () => {
    try {
      const data = await fetcher();
      cache.set(key, { data, timestamp: Date.now() });
      return data;
    } finally {
      pendingRequests.delete(key);
    }
  })();

  pendingRequests.set(key, promise);
  return promise;
}

/**
 * Invalidate cached entries matching key or prefix
 */
export function invalidateCache(keyPrefix?: string): void {
  if (!keyPrefix) {
    cache.clear();
    return;
  }
  for (const k of cache.keys()) {
    if (k.startsWith(keyPrefix)) {
      cache.delete(k);
    }
  }
}
