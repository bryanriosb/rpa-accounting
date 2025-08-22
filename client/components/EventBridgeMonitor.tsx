'use client'

import { useEventBridgeWebSocket } from '@/hooks/useEventBridgeWebSocket'
import { Button } from './ui/button'
import { ConnectionStatus } from '@/types/eventbridge'
import { useEffect } from 'react'

export default function EventBridgeMonitor({
  setEvents,
}: {
  setEvents: Function
}) {
  const {
    events,
    isConnected,
    connectionStatus,
    reconnect,
    setEvents: set,
  } = useEventBridgeWebSocket()

  useEffect(() => {
    setEvents(events)
  }, [events])

  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case 'connected':
        return 'text-green-600'
      case 'disconnected':
        return 'text-red-600'
      case 'reconnecting':
        return 'text-yellow-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="grid gap-2">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          {!isConnected ? (
            <Button size={'sm'} onClick={reconnect}>
              Reconectar
            </Button>
          ) : (
            <>
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              ></div>
              <div
                className={`flex items-center space-x-1 ${getStatusColor(
                  connectionStatus
                )}`}
              >
                <span className="font-medium capitalize text-sm">
                  {connectionStatus === 'connected'
                    ? 'Conectado'
                    : 'Desconectado'}
                </span>
              </div>
            </>
          )}
        </div>
        <h1 className="text-2xl font-bold">Monitor de eventos</h1>
      </div>

      <div className="max-h-[7rem] w-full overflow-y-auto">
        {events.length === 0 ? (
          <div className="flex gap-6 text-end justify-end text-xs py-0 text-gray-500">
            <div>
              <p>... Esperando eventos de descarga</p>
              <p>Los eventos aparecerán aquí en tiempo real</p>
            </div>
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={`${event.event_id}-${index}`}
              className="border rounded p-4 mb-2"
            >
              <div className="grid gap-2 items-center">
                <span className="text-center bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                  {event.detail.portalName}
                  {event.detail.portalName === 'client' && set([])}
                </span>
                <div className="grid gap-2 items-center justify-end">
                  <span className="ml-2 text-xs text-gray-900">
                    {event.detail.message}
                  </span>
                  <span className="text-xs text-end text-gray-500">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
