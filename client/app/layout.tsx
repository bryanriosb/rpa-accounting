import './globals.css'

import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/AppSidebar'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html className="h-screen w-full">
      <body>
        <SidebarProvider>
          <AppSidebar />
          <SidebarTrigger />
          <main className="py-8 px-6 h-full w-full overflow-y-auto">
            {children}
          </main>
        </SidebarProvider>
      </body>
    </html>
  )
}
