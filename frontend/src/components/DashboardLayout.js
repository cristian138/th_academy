import { Sidebar } from './Sidebar';
import { Bell } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';
import { notificationsAPI } from '../services/api';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

export const DashboardLayout = ({ children }) => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const loadNotifications = async () => {
    try {
      const response = await notificationsAPI.list(10);
      setNotifications(response.data);
      setUnreadCount(response.data.filter(n => !n.read).length);
    } catch (error) {
      console.error('Error loading notifications:', error);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  return (
    <div className="flex min-h-screen bg-brand-bg">
      <Sidebar />
      <div className="flex-1 ml-72">
        <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200/50">
          <div className="px-8 py-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-brand-navy">Bienvenido, {user.name}</h2>
              <p className="text-sm text-slate-500">Gestione sus contratos y documentos</p>
            </div>
            <div className="flex items-center gap-4">
              <Popover>
                <PopoverTrigger data-testid="notifications-button" className="relative">
                  <button className="p-2 hover:bg-slate-100 rounded-sm transition-colors">
                    <Bell size={20} strokeWidth={1.5} />
                    {unreadCount > 0 && (
                      <span className="absolute top-1 right-1 w-2 h-2 bg-brand-red rounded-full"></span>
                    )}
                  </button>
                </PopoverTrigger>
                <PopoverContent className="w-80" align="end">
                  <div className="space-y-2">
                    <h3 className="font-semibold text-sm uppercase text-slate-500">Notificaciones</h3>
                    {notifications.length === 0 ? (
                      <p className="text-sm text-slate-500 py-4 text-center">No hay notificaciones</p>
                    ) : (
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {notifications.map((notification) => (
                          <div
                            key={notification.id}
                            className={`p-3 rounded-sm border ${
                              notification.read ? 'bg-white' : 'bg-blue-50 border-brand-blue/20'
                            }`}
                          >
                            <p className="text-sm font-medium text-brand-navy">{notification.title}</p>
                            <p className="text-xs text-slate-600 mt-1">{notification.message}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          </div>
        </header>
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
};
