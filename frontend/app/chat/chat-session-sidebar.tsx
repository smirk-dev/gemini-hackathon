import * as React from 'react';
import { FolderIcon, MessageSquare, MoreHorizontalIcon, ShareIcon } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar';
import { DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { DropdownMenuContent } from '@/components/ui/dropdown-menu';
import { DropdownMenu } from '@/components/ui/dropdown-menu';
import { DropdownMenuTrigger } from '@radix-ui/react-dropdown-menu';

const apiBase = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');

interface Session {
  id?: string;
  session_id?: string;
  status?: string;
  contract_id?: string | null;
  last_activity?: string | { seconds?: number; nanoseconds?: number } | null;
  created_at?: string | { seconds?: number; nanoseconds?: number } | null;
}

interface ChatSessionSidebarProps {
  variant?: 'inset' | 'sidebar' | 'floating';
  onSessionSelect: (sessionId: string) => void;
}

export function ChatSessionSidebar({ variant, onSessionSelect }: ChatSessionSidebarProps) {
  const [sessions, setSessions] = React.useState<Session[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  const formatTimestamp = (value?: Session['last_activity'] | Session['created_at']) => {
    if (!value) return 'Unknown date';
    if (typeof value === 'string') {
      const parsed = new Date(value);
      return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
    }
    if (typeof value === 'object' && value.seconds) {
      return new Date(value.seconds * 1000).toLocaleString();
    }
    return 'Unknown date';
  };

  React.useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await fetch(`${apiBase}/chat/sessions`);
        const data = await response.json();
        if (data.success && Array.isArray(data.sessions)) {
          setSessions(data.sessions);
        } else {
          setSessions([]); // Ensure sessions is an array even if API response is unexpected
          console.log('Invalid sessions data received:', data);
        }
      } catch (error) {
        console.error('Failed to fetch sessions:', error);
        setSessions([]); // Reset to empty array on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
  }, []);

  const handleSessionClick = (sessionId: string) => {
    onSessionSelect(sessionId);
  };

  return (
    <Sidebar {...{ variant }}>
      <SidebarContent>
        <SidebarGroup className="mt-16">
          <SidebarGroupLabel>Sessions</SidebarGroupLabel>
          <SidebarMenu>
            {isLoading ? (
              <div className="space-y-2 px-2 py-2">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
              </div>
            ) : sessions.length === 0 ? (
              <div className="px-4 py-2 text-sm text-muted-foreground">No sessions found</div>
            ) : (
              sessions.map((session) => {
                const sessionId = session.session_id || session.id;
                if (!sessionId) return null;
                return (
                <SidebarMenuItem key={sessionId} className="mb-2">
                  <SidebarMenuButton onClick={() => handleSessionClick(sessionId)}>
                    <div className="flex flex-col my-2 !py-2 cursor-pointer">
                      <p className="text-sm font-medium">Session {sessionId.slice(0, 8)}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatTimestamp(session.last_activity || session.created_at)}
                      </p>
                    </div>
                  </SidebarMenuButton>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <SidebarMenuAction showOnHover className="rounded-sm data-[state=open]:bg-accent">
                        <MoreHorizontalIcon />
                        <span className="sr-only">More</span>
                      </SidebarMenuAction>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-24 rounded-lg" side="right" align="start">
                      <DropdownMenuItem>
                        <FolderIcon />
                        <span>Open</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <ShareIcon />
                        <span>Share</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </SidebarMenuItem>
                );
              })
            )}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
