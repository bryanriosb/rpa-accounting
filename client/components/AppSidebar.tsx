import { CircleGauge, FileDown, Home } from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'

const items = [
  {
    title: 'Notas Disponibles',
    url: '#',
    icon: FileDown,
  },
]

export function AppSidebar() {
  return (
    <Sidebar>
      <div className="h-8 w-full p-2 mb-10">
        <div className="font-bold text-2xl h-full border p-6 flex items-center justify-center">
          Logo
        </div>
      </div>
      <SidebarContent>
        <SidebarGroup>
          {/* <SidebarGroupLabel>Aplicaci</SidebarGroupLabel> */}
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
