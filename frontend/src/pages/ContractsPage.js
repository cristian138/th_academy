import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { contractsAPI } from '../services/api';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Plus, FileText, Clock, CheckCircle2 } from 'lucide-react';

const getStatusBadge = (status) => {
  const statusMap = {
    draft: { label: 'Borrador', class: 'bg-slate-100 text-slate-700 border-slate-200' },
    pending_documents: { label: 'Docs Pendientes', class: 'bg-amber-100 text-amber-700 border-amber-200' },
    under_review: { label: 'En Revisión', class: 'bg-blue-100 text-blue-700 border-blue-200' },
    pending_approval: { label: 'Pendiente Aprobación', class: 'bg-orange-100 text-orange-700 border-orange-200' },
    approved: { label: 'Aprobado', class: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    pending_signature: { label: 'Por Firmar', class: 'bg-amber-100 text-amber-700 border-amber-200' },
    signed: { label: 'Firmado', class: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    active: { label: 'Activo', class: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    completed: { label: 'Completado', class: 'bg-slate-100 text-slate-700 border-slate-200' },
    cancelled: { label: 'Cancelado', class: 'bg-red-100 text-red-700 border-red-200' }
  };
  const status Info = statusMap[status] || { label: status, class: 'bg-slate-100 text-slate-700' };
  return (
    <Badge className={`${statusInfo.class} px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border`}>
      {statusInfo.label}
    </Badge>
  );
};

export const ContractsPage = () => {
  const { hasRole } = useAuth();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadContracts();
  }, []);

  const loadContracts = async () => {
    try {
      const response = await contractsAPI.list();
      setContracts(response.data);
    } catch (error) {
      console.error('Error loading contracts:', error);
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

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-brand-navy mb-2">Contratos</h1>
            <p className="text-slate-600">Gestione los contratos de colaboradores</p>
          </div>
          {hasRole('legal_rep') && (
            <Link to="/contracts/new">
              <Button
                data-testid="new-contract-button"
                className="bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm font-medium px-6 py-2.5 uppercase tracking-wide text-xs"
              >
                <Plus size={18} className="mr-2" />
                Nuevo Contrato
              </Button>
            </Link>
          )}
        </div>

        {contracts.length === 0 ? (
          <Card className="border border-slate-200 rounded-sm">
            <CardContent className="py-12 text-center">
              <FileText size={48} className="mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500">No hay contratos registrados</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {contracts.map((contract) => (
              <Card
                key={contract.id}
                className="border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                data-testid={`contract-card-${contract.id}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg font-bold text-brand-navy mb-2">
                        {contract.title}
                      </CardTitle>
                      <p className="text-sm text-slate-600 line-clamp-2">{contract.description}</p>
                    </div>
                    <div>{getStatusBadge(contract.status)}</div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs uppercase text-slate-500 font-bold mb-1">Tipo</p>
                      <p className="text-sm text-brand-navy">
                        {contract.contract_type === 'service' ? 'Prestación de Servicios' : 'Por Evento'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase text-slate-500 font-bold mb-1">Fecha Inicio</p>
                      <p className="text-sm text-brand-navy">
                        {new Date(contract.start_date).toLocaleDateString('es-CO')}
                      </p>
                    </div>
                    {contract.monthly_payment && (
                      <div>
                        <p className="text-xs uppercase text-slate-500 font-bold mb-1">Pago Mensual</p>
                        <p className="text-sm text-brand-navy font-semibold tabular-nums">
                          ${contract.monthly_payment.toLocaleString('es-CO')}
                        </p>
                      </div>
                    )}
                    {contract.payment_per_session && (
                      <div>
                        <p className="text-xs uppercase text-slate-500 font-bold mb-1">Por Sesión</p>
                        <p className="text-sm text-brand-navy font-semibold tabular-nums">
                          ${contract.payment_per_session.toLocaleString('es-CO')}
                        </p>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/contracts/${contract.id}`} className="flex-1">
                      <Button
                        data-testid={`view-contract-${contract.id}`}
                        variant="outline"
                        className="w-full border-slate-200 hover:bg-slate-50 rounded-sm font-medium uppercase tracking-wide text-xs"
                      >
                        Ver Detalles
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
