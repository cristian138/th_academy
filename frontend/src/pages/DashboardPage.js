import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { dashboardAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  FileText, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  Upload, 
  DollarSign, 
  Users 
} from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await dashboardAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
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

  const statCards = [
    {
      title: 'Total Contratos',
      value: stats?.total_contracts || 0,
      icon: FileText,
      color: 'text-brand-navy',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Contratos Activos',
      value: stats?.active_contracts || 0,
      icon: CheckCircle2,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50'
    },
    {
      title: 'Pendientes',
      value: stats?.pending_contracts || 0,
      icon: Clock,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50'
    },
    {
      title: 'Aprobaciones',
      value: stats?.pending_approvals || 0,
      icon: AlertTriangle,
      color: 'text-brand-red',
      bgColor: 'bg-red-50',
      show: user.role === 'legal_rep' || user.role === 'admin' || user.role === 'superadmin'
    },
    {
      title: 'Documentos Pendientes',
      value: stats?.pending_documents || 0,
      icon: Upload,
      color: 'text-brand-blue',
      bgColor: 'bg-blue-50',
      show: user.role !== 'collaborator'
    },
    {
      title: 'Docs. por Vencer',
      value: stats?.expiring_documents || 0,
      icon: AlertTriangle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    },
    {
      title: 'Pagos Pendientes',
      value: stats?.pending_payments || 0,
      icon: DollarSign,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50'
    },
    {
      title: 'Colaboradores',
      value: stats?.total_collaborators || 0,
      icon: Users,
      color: 'text-brand-navy',
      bgColor: 'bg-blue-50',
      show: user.role !== 'collaborator'
    }
  ];

  const visibleCards = statCards.filter(card => card.show !== false);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-brand-navy mb-2">Dashboard</h1>
          <p className="text-slate-600">Vista general del sistema</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {visibleCards.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} className="border border-slate-200 rounded-sm" data-testid={`stat-card-${index}`}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-xs uppercase font-bold text-slate-500">
                    {stat.title}
                  </CardTitle>
                  <div className={`p-2 rounded-sm ${stat.bgColor}`}>
                    <Icon className={stat.color} size={20} strokeWidth={1.5} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-brand-navy tabular-nums">{stat.value}</div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border border-slate-200 rounded-sm">
            <CardHeader>
              <CardTitle className="text-lg font-bold text-brand-navy">Acción Requerida</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats?.pending_approvals > 0 && user.role === 'legal_rep' && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-sm">
                    <p className="text-sm font-medium text-amber-900">
                      {stats.pending_approvals} contrato(s) esperando su aprobación
                    </p>
                  </div>
                )}
                {stats?.pending_documents > 0 && user.role !== 'collaborator' && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-sm">
                    <p className="text-sm font-medium text-blue-900">
                      {stats.pending_documents} documento(s) por revisar
                    </p>
                  </div>
                )}
                {stats?.pending_payments > 0 && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-sm">
                    <p className="text-sm font-medium text-emerald-900">
                      {stats.pending_payments} pago(s) pendiente(s)
                    </p>
                  </div>
                )}
                {stats?.expiring_documents > 0 && (
                  <div className="p-3 bg-orange-50 border border-orange-200 rounded-sm">
                    <p className="text-sm font-medium text-orange-900">
                      {stats.expiring_documents} documento(s) próximos a vencer
                    </p>
                  </div>
                )}
                {!stats?.pending_approvals && !stats?.pending_documents && !stats?.pending_payments && !stats?.expiring_documents && (
                  <p className="text-sm text-slate-500 text-center py-8">No hay acciones pendientes</p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border border-slate-200 rounded-sm">
            <CardHeader>
              <CardTitle className="text-lg font-bold text-brand-navy">Accesos Rápidos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {user.role === 'legal_rep' && (
                  <a
                    href="/contracts/new"
                    className="p-4 bg-brand-navy text-white rounded-sm text-center hover:bg-brand-navy/90 transition-colors"
                  >
                    <FileText size={24} className="mx-auto mb-2" />
                    <p className="text-xs uppercase font-bold">Nuevo Contrato</p>
                  </a>
                )}
                <a
                  href="/contracts"
                  className="p-4 border border-slate-200 rounded-sm text-center hover:border-brand-blue/50 transition-colors"
                >
                  <FileText size={24} className="mx-auto mb-2 text-brand-navy" />
                  <p className="text-xs uppercase font-bold text-brand-navy">Ver Contratos</p>
                </a>
                {user.role === 'collaborator' && (
                  <a
                    href="/documents"
                    className="p-4 border border-slate-200 rounded-sm text-center hover:border-brand-blue/50 transition-colors"
                  >
                    <Upload size={24} className="mx-auto mb-2 text-brand-navy" />
                    <p className="text-xs uppercase font-bold text-brand-navy">Documentos</p>
                  </a>
                )}
                <a
                  href="/payments"
                  className="p-4 border border-slate-200 rounded-sm text-center hover:border-brand-blue/50 transition-colors"
                >
                  <DollarSign size={24} className="mx-auto mb-2 text-brand-navy" />
                  <p className="text-xs uppercase font-bold text-brand-navy">Pagos</p>
                </a>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};
