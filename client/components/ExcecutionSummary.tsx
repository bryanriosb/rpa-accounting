import { summaryColumns } from '@/const/data-table/excecutionSummaries'
import { DataTable } from './DataTable'
import { getAllItemsOrderedByCreatedAt } from '@/lib/actions/dynamodb'
import { useEffect, useState } from 'react'

export default function ExcecutionSummary({ events }: { events: any[] }) {
  const [summaries, setSummaries] = useState<any[]>([])

  useEffect(() => {
    fetchSummaries()
  }, [events])

  const fetchSummaries = async () => {
    try {
      const response = await getAllItemsOrderedByCreatedAt('ExecutionSummaries')
      setSummaries(response)
    } catch (error) {
      console.warn('DynamoDB table not found or no access:', error)
    }
  }

  return (
    <div className="grid gap-4">
      <div className="grid gap-1">
        <h2 className="subtitle">Resumen de ejecuciones</h2>
        <span className="text-gray-600 text-sm">
          Total de portales procesados por fecha de ejecución con sus
          respectivos estados.
        </span>
      </div>
      <DataTable columns={summaryColumns} data={summaries} />
    </div>
  )
}
