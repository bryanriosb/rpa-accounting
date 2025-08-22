'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import type {
  EventBridgeEvent,
  ConnectionStatus,
  UseEventBridgeWebSocketReturn,
} from '../types/eventbridge'
import { getEnv } from '@/lib/actions/getenv'

export function useEventBridgeWebSocket(): UseEventBridgeWebSocketReturn {
  const [events, setEvents] = useState<EventBridgeEvent[]>([])
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(async () => {
    const url = await getEnv('WEBSOCKET_URL')
    const apiKey = await getEnv('WEBSOCKET_API_KEY')
    const wsUrl = `${url}?x-api-key=${apiKey}`
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    if (!wsUrl) {
      console.error('WEBSOCKET_URL no está configurado')
      return
    }

    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      setIsConnected(true)
      setConnectionStatus('connected')

      // Limpiar timeout de reconexión
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }

    wsRef.current.onmessage = (event: MessageEvent) => {
      try {
        const eventData: EventBridgeEvent = JSON.parse(event.data)
        console.log('Evento recibido:', eventData)

        setEvents((prev) => [eventData, ...prev.slice(0, 99)]) // Mantener últimos 100
      } catch (error) {
        console.error('Error parsing message:', error)
      }
    }

    wsRef.current.onclose = () => {
      setIsConnected(false)
      setConnectionStatus('disconnected')

      // Reconectar automáticamente después de 3 segundos
      reconnectTimeoutRef.current = setTimeout(() => {
        setConnectionStatus('reconnecting')
        connect()
      }, 3000)
    }

    wsRef.current.onerror = (error: Event) => {
      console.error('WebSocket error:', error)
      setConnectionStatus('error')
    }
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    events,
    isConnected,
    connectionStatus,
    reconnect: connect,
    disconnect,
    setEvents,
  }
}
