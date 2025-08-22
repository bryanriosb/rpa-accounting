'use client'

import EventBridgeMonitor from '@/components/EventBridgeMonitor'
import { useState } from 'react'
import PortalReports from '@/components/PortalReports'
import ExcecutionSummary from '@/components/ExcecutionSummary'
import CreateExecutionQueue from '@/components/CreateExecutionQueue'

export default function Home() {
  const [events, setEvents] = useState<any[]>([])

  return (
    <div className="grid gap-6 w-full h-full">
      <div className="flex justify-between w-full mb-4">
        <h1 className="text-2xl font-bold">Notas de Crédito</h1>
        <EventBridgeMonitor setEvents={setEvents} />
      </div>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-7 min-h-screen">
        <div className="col-span-7 md:col-span-5 md:border-r md:pr-4">
          <div className="grid gap-4">
            <PortalReports events={events} />
            <ExcecutionSummary events={events} />
          </div>
        </div>

        <div className="col-span-7 md:col-span-2">
          <CreateExecutionQueue />
        </div>
      </div>
    </div>
  )
}
