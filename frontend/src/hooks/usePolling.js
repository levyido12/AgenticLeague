import { useState, useEffect, useRef, useCallback } from "react";

export function usePolling(fetchFn, interval = 60000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const timerRef = useRef(null);
  const fetchRef = useRef(fetchFn);

  fetchRef.current = fetchFn;

  const doFetch = useCallback(async () => {
    try {
      const result = await fetchRef.current();
      setData(result);
      setLastUpdated(new Date());
    } catch {
      // keep previous data on error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    doFetch();

    function startPolling() {
      timerRef.current = setInterval(doFetch, interval);
    }

    function stopPolling() {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    function handleVisibility() {
      if (document.hidden) {
        stopPolling();
      } else {
        doFetch();
        startPolling();
      }
    }

    startPolling();
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [doFetch, interval]);

  return { data, loading, lastUpdated };
}
