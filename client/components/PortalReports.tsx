import { portalReportsColumns } from '@/const/data-table/portalReportsColumns'
import { DataTable } from './DataTable'
import { useEffect, useState } from 'react'
import { getAllItemsOrderedByCreatedAt } from '@/lib/actions/dynamodb'

export default function PortalReports({ events }: { events: any[] }) {
  const [reports, setReports] = useState<any[]>([])

  useEffect(() => {
    fetchReports()
  }, [events])

  const fetchReports = async () => {
    try {
      const response = await getAllItemsOrderedByCreatedAt('PortalReports')
      setReports(response)
    } catch (error) {
      console.warn(
        'DynamoDB table not found or no access, using mock data:',
        error
      )
    }
  }

  return (
    <div className="grid gap-4">
      <div className="grid gap-1">
        <h2 className="subtitle">Reporte de portales procesados</h2>
        <span className="text-gray-600 text-sm">
          Detalles de los portales procesados.
        </span>
      </div>
      <DataTable columns={portalReportsColumns} data={reports} />
    </div>
  )
}
