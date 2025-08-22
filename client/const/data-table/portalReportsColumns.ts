import { Files } from '@/components/Files'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ColumnDef } from '@tanstack/react-table'
import { MoreHorizontal } from 'lucide-react'

export type Report = {
  id: string
  portalName: string
  status: 'FALLIDO' | 'EXITOSO'
  files: any[]
  pdfsDownloaded: number
  targetDate: string
  url: string
  createdAt: string
}

export const portalReportsColumns: ColumnDef<Report>[] = [
  // {
  //   accessorKey: 'id',
  //   header: 'ID',
  // },
  {
    accessorKey: 'portalName',
    header: 'Portal',
  },
  {
    accessorKey: 'status',
    header: 'Estado',
  },
  {
    accessorKey: 'pdfsDownloaded',
    header: 'Descargados',
  },
  {
    accessorKey: 'targetDate',
    header: 'Fecha Objetivo',
  },
  {
    accessorKey: 'url',
    header: 'URL',
  },
  {
    accessorKey: 'createdAt',
    header: 'Creado',
  },
  // {
  //   id: 'actions',
  //   cell: ({ row }) => {
  //     const note = row.original

  //     return (
  //       <DropdownMenu>
  //         <DropdownMenuTrigger asChild>
  //           <Button variant="ghost" className="h-8 w-8 p-0">
  //             <span className="sr-only">Abrir</span>
  //             <MoreHorizontal className="h-4 w-4" />
  //           </Button>
  //         </DropdownMenuTrigger>
  //         <DropdownMenuContent align="end">
  //           <DropdownMenuLabel>Acciones</DropdownMenuLabel>
  //           <DropdownMenuItem
  //             onClick={() => navigator.clipboard.writeText(note.id)}
  //           >
  //             Copiar ID de nota
  //           </DropdownMenuItem>
  //           <DropdownMenuSeparator />
  //           <DropdownMenuItem>
  //             <Files />
  //           </DropdownMenuItem>
  //         </DropdownMenuContent>
  //       </DropdownMenu>
  //     )
  //   },
  // },
]
