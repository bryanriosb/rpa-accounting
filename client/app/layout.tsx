import './globals.css'

import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/AppSidebar'
import { Toaster } from '@/components/ui/sonner'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html className="h-screen w-full">
      <body>
        <SidebarProvider>
          <AppSidebar />
          <SidebarTrigger />
          <main className="p-8  h-full w-full overflow-y-auto">{children}</main>
          <Toaster />
        </SidebarProvider>
      </body>
    </html>
  )
}
