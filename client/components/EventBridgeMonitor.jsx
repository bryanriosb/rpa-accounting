'use client'

import { useEventBridgeWebSocket } from '@/hooks/useEventBridgeWebSocket';

export default function EventBridgeMonitor() {
  const { events, isConnected, connectionStatus, reconnect } = useEventBridgeWebSocket();

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 'disconnected': return 'text-red-600';
      case 'reconnecting': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="p-2">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Monitor de eventos</h1>
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 ${getStatusColor(connectionStatus)}`}>
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="font-medium capitalize">{connectionStatus}</span>
          </div>
          {!isConnected && (
            <button
              onClick={reconnect}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Reconectar
            </button>
          )}
        </div>
      </div>

      <div className="space-y-1 max-h-[100px] overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center py-0 text-gray-500">
            <p>Esperando eventos de EventBridge...</p>
            <p className="text-sm mt-2">Los eventos aparecerán aquí en tiempo real</p>
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={`${event.event_id}-${index}`}
              className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm"
            >
              <div className="flex justify-between gap-4 items-center items-start mb-2">
                <div>
                  <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                    {event.source}
                  </span>
                  <span className="ml-2 text-sm font-medium text-gray-900">
                    {event.detail_type}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(event.timestamp).toLocaleString()}
                </span>
              </div>
              
              <div className="mt-3">
                <details className="cursor-pointer">
                  <summary className="text-sm font-medium text-gray-700 hover:text-gray-900">
                    Ver detalles del evento
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                    {JSON.stringify(event.detail, null, 2)}
                  </pre>
                </details>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}