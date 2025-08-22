import { Loader2 } from 'lucide-react'

export default function Loading({
  className = 'w-4 h-4',
}: {
  className?: string
}) {
  return <Loader2 className={`${className} animate-spin`} />
}
