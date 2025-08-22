import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from './ui/button'
import { useState } from 'react'
import { DownloadCloud } from 'lucide-react'

interface FilesProps {
  files?: any[]
}

export function Files({ files = [] }: FilesProps) {
  const [open, setOpen] = useState(false)

  const handleOpenDialog = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setOpen(true)
  }

  return (
    <>
      <Button
        variant="ghost"
        onClick={handleOpenDialog}
        className="w-full justify-start"
      >
        Ver Archivos
      </Button>

      <AlertDialog open={open} onOpenChange={setOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Documentos descargados</AlertDialogTitle>
            <AlertDialogDescription>
              <div className="flex gap-4 flex-col w-full">
                {files.length > 0
                  ? files.map((file, i) => (
                      <div
                        className="text-primary flex justify-between"
                        key={`file-${i + 1}`}
                        title={file.name || `Documento_${i + 1}.pdf`}
                      >
                        <p>Documento-{i + 1}.pdf</p>
                        <Button variant="ghost" className="w-10">
                          <DownloadCloud size={24} />
                        </Button>
                      </div>
                    ))
                  : new Array(6).fill(0).map((_, i) => (
                      <div
                        className="text-primary flex justify-between w-full"
                        key={`file-${i + 1}`}
                      >
                        <p>Documento-{i + 1}.pdf</p>
                        <Button variant="ghost" className="w-10">
                          <DownloadCloud size={24} />
                        </Button>
                      </div>
                    ))}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction>Continuar</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
