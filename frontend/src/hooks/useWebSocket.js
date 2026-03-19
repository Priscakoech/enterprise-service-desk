import { useEffect, useRef, useCallback, useState } from 'react';

export default function useWebSocket(url, options = {}) {
  const { onMessage, onOpen, onClose, onError, autoReconnect = true, reconnectInterval = 3000 } = options;
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!url) return;

    try {
      // Build WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}${url}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (mountedRef.current) {
          setIsConnected(true);
          onOpen?.();
        }
      };

      ws.onmessage = (event) => {
        if (mountedRef.current) {
          try {
            const data = JSON.parse(event.data);
            onMessage?.(data);
          } catch {
            onMessage?.(event.data);
          }
        }
      };

      ws.onclose = (event) => {
        if (mountedRef.current) {
          setIsConnected(false);
          onClose?.(event);

          if (autoReconnect && mountedRef.current) {
            reconnectTimerRef.current = setTimeout(() => {
              if (mountedRef.current) connect();
            }, reconnectInterval);
          }
        }
      };

      ws.onerror = (error) => {
        if (mountedRef.current) {
          onError?.(error);
        }
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  }, [url, onMessage, onOpen, onClose, onError, autoReconnect, reconnectInterval]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [url]);

  return { isConnected, send, disconnect };
}
