import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  FileText, 
  Users, 
  Upload, 
  DollarSign, 
  BarChart3,
  Settings,
  LogOut
} from 'lucide-react';

export const Sidebar = () => {
  const { user, logout, hasRole } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['collaborator', 'accountant', 'admin', 'legal_rep', 'superadmin'] },
    { path: '/contracts', label: 'Contratos', icon: FileText, roles: ['collaborator', 'admin', 'legal_rep', 'superadmin'] },
    { path: '/collaborators', label: 'Colaboradores', icon: Users, roles: ['admin', 'legal_rep', 'superadmin'] },
    { path: '/payments', label: 'Pagos', icon: DollarSign, roles: ['collaborator', 'accountant', 'superadmin'] },
    { path: '/reports', label: 'Reportes', icon: BarChart3, roles: ['accountant', 'admin', 'legal_rep', 'superadmin'] },
    { path: '/users', label: 'Usuarios', icon: Settings, roles: ['admin', 'superadmin'] }
  ];

  const visibleItems = menuItems.filter(item => 
    item.roles.includes(user.role)
  );

  return (
    <aside className="w-72 bg-brand-navy min-h-screen text-white fixed left-0 top-0 flex flex-col">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3 mb-2">
          <img 
            src="https://customer-assets.emergentagent.com/job_coach-contracts/artifacts/mw84sg36_ICONO-NEGATIVO--SIN-FONDO.png" 
            alt="Jotuns Club Logo" 
            className="w-14 h-14 object-contain"
          />
          <div>
            <h1 className="text-lg font-bold tracking-tight">Jotuns Club SAS</h1>
            <p className="text-xs text-white/60">Talento Humano</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              data-testid={`nav-${item.label.toLowerCase()}`}
              className={`flex items-center gap-3 px-4 py-3 rounded-sm transition-colors ${
                isActive(item.path)
                  ? 'bg-brand-blue text-white font-medium'
                  : 'text-white/80 hover:bg-white/10'
              }`}
            >
              <Icon size={20} strokeWidth={1.5} />
              <span className="text-sm uppercase tracking-wide">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/10">
        <div className="px-4 py-3 mb-2 rounded-sm bg-white/5">
          <p className="text-xs uppercase text-white/40 mb-1">Usuario</p>
          <p className="text-sm font-medium">{user.name}</p>
          <p className="text-xs text-white/60">{user.email}</p>
          <p className="text-xs uppercase text-brand-blue mt-1">{user.role}</p>
        </div>
        <button
          onClick={logout}
          data-testid="logout-button"
          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-white/80 hover:bg-white/10 rounded-sm transition-colors"
        >
          <LogOut size={18} strokeWidth={1.5} />
          <span>Cerrar Sesión</span>
        </button>
      </div>
    </aside>
  );
};
