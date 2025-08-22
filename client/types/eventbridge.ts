export interface EventBridgeEvent {
  type: string
  timestamp: string
  source: string
  detail_type: string
  detail: Record<string, any>
  event_id: string
}

export type ConnectionStatus =
  | 'connected'
  | 'disconnected'
  | 'reconnecting'
  | 'error'

export interface UseEventBridgeWebSocketReturn {
  events: EventBridgeEvent[]
  isConnected: boolean
  connectionStatus: ConnectionStatus
  reconnect: () => void
  disconnect: () => void
  setEvents: Function
}
