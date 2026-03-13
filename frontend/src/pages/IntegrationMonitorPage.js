import { useEffect, useState, useCallback } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { integrationAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { 
  ArrowRightLeft, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Activity,
  ExternalLink,
  AlertTriangle
} from 'lucide-react';

const StatusBadge = ({ synced, error }) => {
  if (synced) {
    return (
      <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200 px-2.5 py-0.5 rounded-full text-xs font-bold border" data-testid="badge-synced">
        Sincronizado
      </Badge>
    );
  }
  if (error) {
    return (
      <Badge className="bg-red-100 text-red-700 border-red-200 px-2.5 py-0.5 rounded-full text-xs font-bold border" data-testid="badge-failed">
        Error
      </Badge>
    );
  }
  return (
    <Badge className="bg-amber-100 text-amber-700 border-amber-200 px-2.5 py-0.5 rounded-full text-xs font-bold border" data-testid="badge-pending">
      Pendiente
    </Badge>
  );
};

const HealthIndicator = ({ health }) => {
  if (!health) return null;
  
  const statusColors = {
    online: 'bg-emerald-500',
    degraded: 'bg-amber-500',
    timeout: 'bg-red-500',
    error: 'bg-red-500'
  };

  return (
    <div className="flex items-center gap-2" data-testid="health-indicator">
      <div className={`w-3 h-3 rounded-full ${statusColors[health.status] || 'bg-slate-400'} animate-pulse`} />
      <span className="text-sm font-medium text-slate-700">
        {health.status === 'online' ? 'Sistema conectado' : health.message}
      </span>
      {health.response_time_ms && (
        <span className="text-xs text-slate-500">({Math.round(health.response_time_ms)}ms)</span>
      )}
    </div>
  );
};

export default function IntegrationMonitorPage() {
  const [status, setStatus] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [statusRes, healthRes] = await Promise.all([
        integrationAPI.getStatus(),
        integrationAPI.getHealth()
      ]);
      setStatus(statusRes.data);
      setHealth(healthRes.data);
    } catch (error) {
      console.error('Error loading integration data:', error);
      toast.error('Error al cargar datos de integración');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRetry = async (paymentId) => {
    setRetrying(paymentId);
    try {
      await integrationAPI.retry(paymentId);
      toast.success('Pago sincronizado exitosamente');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al reintentar sincronización');
    } finally {
      setRetrying(null);
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

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="integration-monitor-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-brand-navy mb-2">Integración</h1>
            <p className="text-slate-600">
              Monitor de sincronización con el sistema de presupuesto
            </p>
          </div>
          <div className="flex items-center gap-3">
            <HealthIndicator health={health} />
            <Button
              onClick={loadData}
              variant="outline"
              data-testid="refresh-integration"
              className="border-slate-300 rounded-sm"
            >
              <RefreshCw size={16} className="mr-2" />
              Actualizar
            </Button>
            {status?.presupuesto_url && (
              <a
                href={status.presupuesto_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white text-sm font-medium rounded-sm hover:bg-brand-navy/90 transition-colors"
                data-testid="presupuesto-link"
              >
                <ExternalLink size={16} />
                Ir a Presupuesto
              </a>
            )}
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border border-slate-200 rounded-sm" data-testid="card-total">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase text-slate-500 font-bold">Total Aprobados</p>
                  <p className="text-3xl font-bold text-brand-navy mt-1">{status?.total_approved || 0}</p>
                </div>
                <Activity size={28} className="text-brand-blue" />
              </div>
            </CardContent>
          </Card>
          <Card className="border border-emerald-200 rounded-sm" data-testid="card-synced">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase text-emerald-600 font-bold">Sincronizados</p>
                  <p className="text-3xl font-bold text-emerald-700 mt-1">{status?.synced_count || 0}</p>
                </div>
                <CheckCircle2 size={28} className="text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border border-amber-200 rounded-sm" data-testid="card-pending">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase text-amber-600 font-bold">Pendientes</p>
                  <p className="text-3xl font-bold text-amber-700 mt-1">{status?.pending_count || 0}</p>
                </div>
                <Clock size={28} className="text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border border-red-200 rounded-sm" data-testid="card-failed">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase text-red-600 font-bold">Con Error</p>
                  <p className="text-3xl font-bold text-red-700 mt-1">{status?.failed_count || 0}</p>
                </div>
                <XCircle size={28} className="text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Failed Payments - Priority */}
        {status?.failed?.length > 0 && (
          <Card className="border border-red-200 rounded-sm" data-testid="failed-section">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-bold text-red-700 flex items-center gap-2">
                <AlertTriangle size={20} />
                Pagos con Error de Sincronización
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {status.failed.map((payment) => (
                  <div
                    key={payment.id}
                    className="flex items-center justify-between p-4 bg-red-50 border border-red-100 rounded-sm"
                    data-testid={`failed-payment-${payment.id}`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <p className="font-semibold text-brand-navy">
                          ${payment.amount?.toLocaleString('es-CO')}
                        </p>
                        <StatusBadge synced={false} error={true} />
                      </div>
                      <p className="text-sm text-slate-600">
                        {payment.collaborator_name} - {payment.contract_title}
                      </p>
                      {payment.presupuesto_sync_error && (
                        <p className="text-xs text-red-600 mt-1">{payment.presupuesto_sync_error}</p>
                      )}
                    </div>
                    <Button
                      onClick={() => handleRetry(payment.id)}
                      disabled={retrying === payment.id}
                      size="sm"
                      data-testid={`retry-${payment.id}`}
                      className="bg-red-600 hover:bg-red-700 text-white rounded-sm"
                    >
                      {retrying === payment.id ? (
                        <RefreshCw size={14} className="animate-spin mr-1" />
                      ) : (
                        <RefreshCw size={14} className="mr-1" />
                      )}
                      Reintentar
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Pending Payments */}
        {status?.pending?.length > 0 && (
          <Card className="border border-amber-200 rounded-sm" data-testid="pending-section">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-bold text-amber-700 flex items-center gap-2">
                <Clock size={20} />
                Pagos Pendientes de Sincronización
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {status.pending.map((payment) => (
                  <div
                    key={payment.id}
                    className="flex items-center justify-between p-4 bg-amber-50 border border-amber-100 rounded-sm"
                    data-testid={`pending-payment-${payment.id}`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <p className="font-semibold text-brand-navy">
                          ${payment.amount?.toLocaleString('es-CO')}
                        </p>
                        <StatusBadge synced={false} error={false} />
                      </div>
                      <p className="text-sm text-slate-600">
                        {payment.collaborator_name} - {payment.contract_title}
                      </p>
                    </div>
                    <Button
                      onClick={() => handleRetry(payment.id)}
                      disabled={retrying === payment.id}
                      size="sm"
                      variant="outline"
                      data-testid={`sync-${payment.id}`}
                      className="border-amber-300 text-amber-700 hover:bg-amber-50 rounded-sm"
                    >
                      {retrying === payment.id ? (
                        <RefreshCw size={14} className="animate-spin mr-1" />
                      ) : (
                        <ArrowRightLeft size={14} className="mr-1" />
                      )}
                      Sincronizar
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Synced Payments */}
        <Card className="border border-slate-200 rounded-sm" data-testid="synced-section">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-bold text-brand-navy flex items-center gap-2">
              <CheckCircle2 size={20} className="text-emerald-600" />
              Pagos Sincronizados
            </CardTitle>
          </CardHeader>
          <CardContent>
            {status?.synced?.length > 0 ? (
              <div className="space-y-3">
                {status.synced.map((payment) => (
                  <div
                    key={payment.id}
                    className="flex items-center justify-between p-4 bg-emerald-50/50 border border-emerald-100 rounded-sm"
                    data-testid={`synced-payment-${payment.id}`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <p className="font-semibold text-brand-navy">
                          ${payment.amount?.toLocaleString('es-CO')}
                        </p>
                        <StatusBadge synced={true} />
                      </div>
                      <p className="text-sm text-slate-600">
                        {payment.collaborator_name} - {payment.contract_title}
                      </p>
                      {payment.presupuesto_budget_id && (
                        <p className="text-xs text-emerald-600 mt-1">
                          ID Presupuesto: {payment.presupuesto_budget_id}
                        </p>
                      )}
                    </div>
                    <CheckCircle2 size={20} className="text-emerald-500" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                <ArrowRightLeft size={40} className="mx-auto mb-3 text-slate-300" />
                <p>No hay pagos sincronizados aún</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
