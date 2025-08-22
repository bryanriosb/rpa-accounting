import EventBridgeMonitor from '@/components/EventBridgeMonitor'

import { DataTable } from '@/components/DataTable'
import { columns, Payment } from './columns'

async function getData(): Promise<Payment[]> {
  // Fetch data from your API here.
  return [
    {
      id: '8fcfeb91a1b14bfc850a2482d5d15ade',
      portalName: 'La Montaña',
      files: [
        {
          S: 'https://credit-notes-files.s3.us-west-1.amazonaws.com/2025-08-20/006_VALLEREAL/documento_NA-10006_NAVA10006.pdf',
        },
      ],
      pdfsDownloaded: 5,
      status: 'EXITOSO',
      targetDate: '2025/04/25',
      url: 'https://proveedores.lamontana.co',
      createdAt: '2025-08-20 01:40:35',
    },
    {
      id: '8fcfeb91a1b14bfc850a2482d5d15adf',
      portalName: 'Surtifamiliar',
      files: [
        {
          S: 'https://credit-notes-files.s3.us-west-1.amazonaws.com/2025-08-20/006_VALLEREAL/documento_NA-10006_NAVA10006.pdf',
        },
      ],
      pdfsDownloaded: 5,
      status: 'EXITOSO',
      targetDate: '2025/04/25',
      url: 'https://portalproveedores.surtifamiliar.com',
      createdAt: '2025-08-20 01:40:35',
    },
    {
      id: '8fcfeb91a1b14bfc850a2482d5d15adg',
      portalName: 'Megatiendas',
      files: [],
      pdfsDownloaded: 0,
      status: 'FALLIDO',
      targetDate: '2025/04/25',
      url: 'https://proveedores.megatiendas.co/megatiendas',
      createdAt: '2025-08-20 01:40:35',
    },
    {
      id: '8fcfeb91a1b14bfc850a2482d5d15adh',
      portalName: 'La Montaña',
      files: [
        {
          S: 'https://credit-notes-files.s3.us-west-1.amazonaws.com/2025-08-20/006_VALLEREAL/documento_NA-10006_NAVA10006.pdf',
        },
      ],
      pdfsDownloaded: 1,
      status: 'EXITOSO',
      targetDate: '2025/04/25',
      url: 'http://190.85.196.187',
      createdAt: '2025-08-20 01:40:35',
    },
  ]
}
export default async function Home() {
  const data = await getData()

  return (
    <div className="grid gap-6 w-full">
      <div className="flex justify-between w-full">
        <h1 className="text-2xl font-bold">Notas de Crédito</h1>
        <EventBridgeMonitor />
      </div>

      <DataTable columns={columns} data={data} />
    </div>
  )
}
