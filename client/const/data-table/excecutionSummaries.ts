import { ColumnDef } from '@tanstack/react-table'

export type Summary = {
  id: string
  failedPortals: number
  partialPortals: number
  successfulPortals: number
  totalErrors: number
  totalPdfsDownloaded: number
  totalPortalsProcessed: number
  createdAt: string
}

export const summaryColumns: ColumnDef<Summary>[] = [
  //   {
  //     accessorKey: 'id',
  //     header: 'ID',
  //   },
  {
    accessorKey: 'failedPortals',
    header: 'Portales Fallidos',
  },
  {
    accessorKey: 'partialPortals',
    header: 'Portales Parciales',
  },
  {
    accessorKey: 'successfulPortals',
    header: 'Portales Exitosos',
  },
  {
    accessorKey: 'totalErrors',
    header: 'Errores Totales',
  },
  {
    accessorKey: 'totalPdfsDownloaded',
    header: 'PDFs Descargados',
  },
  {
    accessorKey: 'totalPortalsProcessed',
    header: 'Portales Procesados',
  },
  {
    accessorKey: 'createdAt',
    header: 'Creado',
  },
]
