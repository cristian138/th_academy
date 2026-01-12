import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { reportsAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BarChart3, FileText, DollarSign, Download } from 'lucide-react';
import { toast } from 'sonner';

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
  const statusInfo = statusMap[status] || { label: status, class: 'bg-slate-100 text-slate-700' };
  return (
    <Badge className={`${statusInfo.class} px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border`}>
      {statusInfo.label}
    </Badge>
  );
};

export const ReportsPage = () => {
  const [contractsPending, setContractsPending] = useState([]);
  const [contractsActive, setContractsActive] = useState([]);
  const [paymentsPending, setPaymentsPending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const [pendingRes, activeRes, paymentsRes] = await Promise.all([
        reportsAPI.contractsPending(),
        reportsAPI.contractsActive(),
        reportsAPI.paymentsPending()
      ]);
      setContractsPending(pendingRes.data.contracts || []);
      setContractsActive(activeRes.data.contracts || []);
      setPaymentsPending(paymentsRes.data.payments || []);
    } catch (error) {
      console.error('Error loading reports:', error);
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
            <h1 className="text-4xl font-bold text-brand-navy mb-2">Reportes</h1>
            <p className="text-slate-600">Visualice reportes y estadísticas del sistema</p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => {
                try {
                  reportsAPI.exportContracts();
                  toast.success('Descargando reporte de contratos...');
                } catch (error) {
                  toast.error('Error al exportar contratos');
                }
              }}
              variant="outline"
              className="rounded-sm border-brand-navy text-brand-navy hover:bg-brand-navy/10"
              data-testid="export-contracts-btn"
            >
              <Download size={16} className="mr-2" />
              Exportar Contratos
            </Button>
            <Button
              onClick={() => {
                try {
                  reportsAPI.exportPayments();
                  toast.success('Descargando reporte de pagos...');
                } catch (error) {
                  toast.error('Error al exportar pagos');
                }
              }}
              variant="outline"
              className="rounded-sm border-brand-navy text-brand-navy hover:bg-brand-navy/10"
              data-testid="export-payments-btn"
            >
              <Download size={16} className="mr-2" />
              Exportar Pagos
            </Button>
          </div>
        </div>

        <Tabs defaultValue="pending" className="space-y-6">
          <TabsList className="bg-white border border-slate-200 rounded-sm p-1">
            <TabsTrigger value="pending" className="rounded-sm" data-testid="tab-pending">
              <FileText size={16} className="mr-2" />
              Contratos Pendientes ({contractsPending.length})
            </TabsTrigger>
            <TabsTrigger value="active" className="rounded-sm" data-testid="tab-active">
              <BarChart3 size={16} className="mr-2" />
              Contratos Activos ({contractsActive.length})
            </TabsTrigger>
            <TabsTrigger value="payments" className="rounded-sm" data-testid="tab-payments">
              <DollarSign size={16} className="mr-2" />
              Pagos Pendientes ({paymentsPending.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="pending" className="space-y-4">
            <Card className="border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-brand-navy">
                  Contratos Pendientes por Firmar
                </CardTitle>
              </CardHeader>
              <CardContent>
                {contractsPending.length === 0 ? (
                  <p className="text-center text-slate-500 py-8">No hay contratos pendientes</p>
                ) : (
                  <div className="space-y-3">
                    {contractsPending.map((contract) => (
                      <div
                        key={contract.id}
                        className="p-4 border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                        data-testid={`pending-contract-${contract.id}`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="font-semibold text-brand-navy">{contract.title}</p>
                            <p className="text-sm text-slate-600 mt-1">{contract.description}</p>
                          </div>
                          {getStatusBadge(contract.status)}
                        </div>
                        <div className="grid grid-cols-3 gap-4 mt-3">
                          <div>
                            <p className="text-xs uppercase text-slate-500 font-bold">Tipo</p>
                            <p className="text-sm text-brand-navy">
                              {contract.contract_type === 'service' ? 'Servicios' : 'Evento'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs uppercase text-slate-500 font-bold">Inicio</p>
                            <p className="text-sm text-brand-navy">
                              {new Date(contract.start_date).toLocaleDateString('es-CO')}
                            </p>
                          </div>
                          {contract.monthly_payment && (
                            <div>
                              <p className="text-xs uppercase text-slate-500 font-bold">Pago</p>
                              <p className="text-sm text-brand-navy font-semibold">
                                ${contract.monthly_payment.toLocaleString('es-CO')}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="active" className="space-y-4">
            <Card className="border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-brand-navy">Contratos Activos</CardTitle>
              </CardHeader>
              <CardContent>
                {contractsActive.length === 0 ? (
                  <p className="text-center text-slate-500 py-8">No hay contratos activos</p>
                ) : (
                  <div className="space-y-3">
                    {contractsActive.map((contract) => (
                      <div
                        key={contract.id}
                        className="p-4 border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                        data-testid={`active-contract-${contract.id}`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="font-semibold text-brand-navy">{contract.title}</p>
                            <p className="text-sm text-slate-600 mt-1">{contract.description}</p>
                          </div>
                          {getStatusBadge(contract.status)}
                        </div>
                        <div className="grid grid-cols-4 gap-4 mt-3">
                          <div>
                            <p className="text-xs uppercase text-slate-500 font-bold">Tipo</p>
                            <p className="text-sm text-brand-navy">
                              {contract.contract_type === 'service' ? 'Servicios' : 'Evento'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs uppercase text-slate-500 font-bold">Inicio</p>
                            <p className="text-sm text-brand-navy">
                              {new Date(contract.start_date).toLocaleDateString('es-CO')}
                            </p>
                          </div>
                          {contract.end_date && (
                            <div>
                              <p className="text-xs uppercase text-slate-500 font-bold">Fin</p>
                              <p className="text-sm text-brand-navy">
                                {new Date(contract.end_date).toLocaleDateString('es-CO')}
                              </p>
                            </div>
                          )}
                          {contract.monthly_payment && (
                            <div>
                              <p className="text-xs uppercase text-slate-500 font-bold">Pago</p>
                              <p className="text-sm text-brand-navy font-semibold">
                                ${contract.monthly_payment.toLocaleString('es-CO')}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="payments" className="space-y-4">
            <Card className="border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-brand-navy">Pagos Pendientes</CardTitle>
              </CardHeader>
              <CardContent>
                {paymentsPending.length === 0 ? (
                  <p className="text-center text-slate-500 py-8">No hay pagos pendientes</p>
                ) : (
                  <div className="space-y-3">
                    {paymentsPending.map((payment) => (
                      <div
                        key={payment.id}
                        className="p-4 border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                        data-testid={`pending-payment-${payment.id}`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="font-semibold text-brand-navy text-lg">
                              ${payment.amount.toLocaleString('es-CO')}
                            </p>
                            {payment.description && (
                              <p className="text-sm text-slate-600 mt-1">{payment.description}</p>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="text-xs uppercase text-slate-500 font-bold mb-1">Fecha</p>
                            <p className="text-sm text-brand-navy">
                              {new Date(payment.payment_date).toLocaleDateString('es-CO')}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};
