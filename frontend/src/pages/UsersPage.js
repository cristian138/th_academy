import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { usersAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users, Mail, Shield } from 'lucide-react';

const getRoleBadge = (role) => {
  const roleMap = {
    superadmin: { label: 'Superadmin', class: 'bg-purple-100 text-purple-700 border-purple-200' },
    admin: { label: 'Administrador', class: 'bg-brand-navy text-white border-brand-navy' },
    legal_rep: { label: 'Representante Legal', class: 'bg-blue-100 text-blue-700 border-blue-200' },
    accountant: { label: 'Contador', class: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    collaborator: { label: 'Colaborador', class: 'bg-slate-100 text-slate-700 border-slate-200' }
  };
  const roleInfo = roleMap[role] || { label: role, class: 'bg-slate-100 text-slate-700' };
  return (
    <Badge className={`${roleInfo.class} px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border`}>
      {roleInfo.label}
    </Badge>
  );
};

export const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await usersAPI.list();
      setUsers(response.data);
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-navy"></div>
        </div>
      </DashboardLayout>
    );
  }

  const groupedUsers = {
    admin: users.filter(u => ['superadmin', 'admin'].includes(u.role)),
    management: users.filter(u => ['legal_rep', 'accountant'].includes(u.role)),
    collaborators: users.filter(u => u.role === 'collaborator')
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-brand-navy mb-2">Usuarios</h1>
          <p className="text-slate-600">Gestione los usuarios del sistema</p>
        </div>

        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-bold text-brand-navy mb-4 flex items-center gap-2">
              <Shield size={20} />
              Administradores
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groupedUsers.admin.map((user) => (
                <Card
                  key={user.id}
                  className="border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                  data-testid={`user-card-${user.id}`}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg font-bold text-brand-navy mb-1">
                          {user.name}
                        </CardTitle>
                        {getRoleBadge(user.role)}
                      </div>
                      <div className={`w-3 h-3 rounded-full ${
                        user.is_active ? 'bg-emerald-500' : 'bg-slate-300'
                      }`}></div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Mail size={14} strokeWidth={1.5} />
                      <span className="truncate">{user.email}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold text-brand-navy mb-4 flex items-center gap-2">
              <Users size={20} />
              Gestión
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groupedUsers.management.map((user) => (
                <Card
                  key={user.id}
                  className="border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                  data-testid={`user-card-${user.id}`}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg font-bold text-brand-navy mb-1">
                          {user.name}
                        </CardTitle>
                        {getRoleBadge(user.role)}
                      </div>
                      <div className={`w-3 h-3 rounded-full ${
                        user.is_active ? 'bg-emerald-500' : 'bg-slate-300'
                      }`}></div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Mail size={14} strokeWidth={1.5} />
                      <span className="truncate">{user.email}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold text-brand-navy mb-4 flex items-center gap-2">
              <Users size={20} />
              Colaboradores
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groupedUsers.collaborators.map((user) => (
                <Card
                  key={user.id}
                  className="border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                  data-testid={`user-card-${user.id}`}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg font-bold text-brand-navy mb-1">
                          {user.name}
                        </CardTitle>
                        {getRoleBadge(user.role)}
                      </div>
                      <div className={`w-3 h-3 rounded-full ${
                        user.is_active ? 'bg-emerald-500' : 'bg-slate-300'
                      }`}></div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Mail size={14} strokeWidth={1.5} />
                      <span className="truncate">{user.email}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};
