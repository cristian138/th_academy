import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { paymentsAPI, contractsAPI } from '../services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { DollarSign, Upload, CheckCircle2, Clock, Plus, FileText, AlertCircle } from 'lucide-react';

const getStatusBadge = (status) => {
  const statusMap = {
    draft: { label: 'Borrador', class: 'bg-slate-100 text-slate-700 border-slate-200' },
    pending_approval: { label: 'Pendiente Aprobación', class: 'bg-amber-100 text-amber-700 border-amber-200' },
    approved: { label: 'Aprobado', class: 'bg-blue-100 text-blue-700 border-blue-200' },
    paid: { label: 'Pagado', class: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    rejected: { label: 'Rechazado', class: 'bg-red-100 text-red-700 border-red-200' },
    cancelled: { label: 'Cancelado', class: 'bg-red-100 text-red-700 border-red-200' }
  };
  const statusInfo = statusMap[status] || statusMap.draft;
  return (
    <Badge className={`${statusInfo.class} px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border`}>
      {statusInfo.label}
    </Badge>
  );
};

export const PaymentsPage = () => {
  const { user, hasRole } = useAuth();
  const [payments, setPayments] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadingBill, setUploadingBill] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [approvingPayment, setApprovingPayment] = useState(null);
  const [confirmingPayment, setConfirmingPayment] = useState(null);
  const [rejectingPayment, setRejectingPayment] = useState(null);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  
  // Form state for creating payment (cuenta de cobro)
  const [formData, setFormData] = useState({
    contract_id: '',
    amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    description: ''
  });

  useEffect(() => {
    loadPayments();
    if (user.role === 'collaborator') {
      loadContracts();
    }
  }, []);

  const loadPayments = async () => {
    try {
      const response = await paymentsAPI.list();
      setPayments(response.data);
    } catch (error) {
      console.error('Error loading payments:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadContracts = async () => {
    try {
      const response = await contractsAPI.list({ status: 'active' });
      setContracts(response.data);
    } catch (error) {
      console.error('Error loading contracts:', error);
    }
  };

  const handleCreatePayment = async () => {
    if (!formData.contract_id || !formData.amount) {
      toast.error('Por favor complete los campos obligatorios');
      return;
    }

    setCreating(true);
    try {
      const paymentData = {
        ...formData,
        amount: parseFloat(formData.amount),
        payment_date: new Date(formData.payment_date).toISOString()
      };

      await paymentsAPI.create(paymentData);
      toast.success('Cuenta de cobro creada exitosamente');
      setShowCreateDialog(false);
      setFormData({
        contract_id: '',
        amount: '',
        payment_date: new Date().toISOString().split('T')[0],
        description: ''
      });
      loadPayments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear cuenta de cobro');
    } finally {
      setCreating(false);
    }
  };

  const handleUploadBill = async (paymentId, file) => {
    setUploadingBill(paymentId);
    try {
      await paymentsAPI.uploadBill(paymentId, file);
      toast.success('Cuenta de cobro cargada exitosamente - enviada para aprobación');
      loadPayments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al cargar cuenta de cobro');
    } finally {
      setUploadingBill(null);
    }
  };

  const handleApprovePayment = async (paymentId) => {
    setApprovingPayment(paymentId);
    try {
      await paymentsAPI.approve(paymentId);
      toast.success('Cuenta de cobro aprobada exitosamente');
      loadPayments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al aprobar cuenta de cobro');
    } finally {
      setApprovingPayment(null);
    }
  };

  const handleRejectPayment = async () => {
    if (!rejectionReason.trim()) {
      toast.error('Por favor ingrese el motivo del rechazo');
      return;
    }

    try {
      await paymentsAPI.reject(rejectingPayment, rejectionReason);
      toast.success('Cuenta de cobro rechazada');
      setShowRejectDialog(false);
      setRejectionReason('');
      setRejectingPayment(null);
      loadPayments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al rechazar cuenta de cobro');
    }
  };

  const handleConfirmPayment = async (paymentId, file) => {
    setConfirmingPayment(paymentId);
    try {
      await paymentsAPI.confirm(paymentId, file);
      toast.success('Pago confirmado y comprobante generado');
      loadPayments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al confirmar pago');
    } finally {
      setConfirmingPayment(null);
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
            <h1 className="text-4xl font-bold text-brand-navy mb-2">Cuentas de Cobro y Pagos</h1>
            <p className="text-slate-600">
              {user.role === 'collaborator' 
                ? 'Cree y gestione sus cuentas de cobro' 
                : 'Apruebe cuentas de cobro y genere comprobantes de pago'}
            </p>
          </div>
          
          {user.role === 'collaborator' && (
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button
                  data-testid="create-payment-button"
                  className="bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm font-medium px-6 py-2.5 uppercase tracking-wide text-xs"
                >
                  <Plus size={18} className="mr-2" />
                  Nueva Cuenta de Cobro
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle className="text-brand-navy">Nueva Cuenta de Cobro</DialogTitle>
                  <DialogDescription>
                    Cree una cuenta de cobro para uno de sus contratos activos.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label className="text-xs uppercase text-slate-500 font-bold">Contrato</Label>
                    <Select
                      value={formData.contract_id}
                      onValueChange={(value) => setFormData({ ...formData, contract_id: value })}
                    >
                      <SelectTrigger data-testid="contract-select" className="rounded-sm">
                        <SelectValue placeholder="Seleccione un contrato" />
                      </SelectTrigger>
                      <SelectContent>
                        {contracts.map((contract) => (
                          <SelectItem key={contract.id} value={contract.id}>
                            {contract.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs uppercase text-slate-500 font-bold">Monto (COP)</Label>
                    <Input
                      type="number"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                      placeholder="3500000"
                      data-testid="amount-input"
                      className="rounded-sm"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs uppercase text-slate-500 font-bold">Fecha</Label>
                    <Input
                      type="date"
                      value={formData.payment_date}
                      onChange={(e) => setFormData({ ...formData, payment_date: e.target.value })}
                      data-testid="payment-date-input"
                      className="rounded-sm"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs uppercase text-slate-500 font-bold">Descripción (Opcional)</Label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Ej: Pago mes de enero 2025"
                      data-testid="description-input"
                      className="rounded-sm"
                      rows={3}
                    />
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => setShowCreateDialog(false)}
                    className="flex-1 rounded-sm"
                  >
                    Cancelar
                  </Button>
                  <Button
                    onClick={handleCreatePayment}
                    disabled={creating || !formData.contract_id || !formData.amount}
                    data-testid="submit-payment-button"
                    className="flex-1 bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
                  >
                    {creating ? 'Creando...' : 'Crear'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {payments.length === 0 ? (
          <Card className="border border-slate-200 rounded-sm">
            <CardContent className="py-12 text-center">
              <DollarSign size={48} className="mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500">No hay cuentas de cobro registradas</p>
              {user.role === 'collaborator' && (
                <Button
                  onClick={() => setShowCreateDialog(true)}
                  className="mt-4 bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
                >
                  Crear Primera Cuenta de Cobro
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {payments.map((payment) => (
              <Card
                key={payment.id}
                className="border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                data-testid={`payment-card-${payment.id}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg font-bold text-brand-navy mb-2">
                        ${payment.amount.toLocaleString('es-CO')}
                      </CardTitle>
                      {payment.description && (
                        <p className="text-sm text-slate-600">{payment.description}</p>
                      )}
                    </div>
                    <div>{getStatusBadge(payment.status)}</div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs uppercase text-slate-500 font-bold mb-1">Fecha</p>
                      <p className="text-sm text-brand-navy">
                        {new Date(payment.payment_date).toLocaleDateString('es-CO')}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase text-slate-500 font-bold mb-1">Monto</p>
                      <p className="text-sm text-brand-navy font-semibold tabular-nums">
                        ${payment.amount.toLocaleString('es-CO')}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase text-slate-500 font-bold mb-1">Estado</p>
                      <p className="text-sm text-brand-navy capitalize">{payment.status.replace('_', ' ')}</p>
                    </div>
                  </div>

                  {/* Colaborador - Cargar cuenta de cobro (status: draft) */}
                  {payment.status === 'draft' && user.role === 'collaborator' && (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-sm">
                      <p className="text-sm font-medium text-amber-900 mb-3 flex items-center gap-2">
                        <AlertCircle size={18} />
                        Por favor cargue su cuenta de cobro en PDF
                      </p>
                      <Input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) {
                            handleUploadBill(payment.id, file);
                          }
                        }}
                        disabled={uploadingBill === payment.id}
                        data-testid={`bill-upload-${payment.id}`}
                        className="rounded-sm"
                      />
                    </div>
                  )}

                  {/* Pendiente aprobación - Contador puede ver, aprobar o rechazar */}
                  {payment.status === 'pending_approval' && (
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-sm space-y-3">
                      <div className="flex items-center gap-2">
                        <Clock size={18} className="text-blue-700" />
                        <p className="text-sm font-medium text-blue-900">
                          Cuenta de cobro en revisión
                        </p>
                      </div>
                      
                      {payment.bill_file_id && (
                        <div className="pt-2">
                          <a
                            href={paymentsAPI.downloadFile(payment.bill_file_id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-sm hover:bg-blue-50 transition-colors text-sm font-medium"
                          >
                            <FileText size={16} />
                            Ver Cuenta de Cobro (PDF)
                          </a>
                        </div>
                      )}
                      
                      {hasRole('accountant') && (
                        <div className="flex gap-2 pt-2">
                          <Button
                            onClick={() => handleApprovePayment(payment.id)}
                            disabled={approvingPayment === payment.id}
                            size="sm"
                            data-testid={`approve-payment-${payment.id}`}
                            className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-sm"
                          >
                            {approvingPayment === payment.id ? 'Aprobando...' : '✓ Aprobar'}
                          </Button>
                          <Button
                            onClick={() => {
                              setRejectingPayment(payment.id);
                              setShowRejectDialog(true);
                            }}
                            disabled={approvingPayment === payment.id}
                            size="sm"
                            variant="outline"
                            data-testid={`reject-payment-${payment.id}`}
                            className="flex-1 border-red-300 text-red-700 hover:bg-red-50 rounded-sm"
                          >
                            ✗ Rechazar
                          </Button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Aprobado - Contador genera comprobante */}
                  {payment.status === 'approved' && hasRole('accountant') && (
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-sm">
                      <p className="text-sm font-medium text-emerald-900 mb-3">
                        Cuenta de cobro aprobada. Genere el comprobante de pago:
                      </p>
                      <Input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) {
                            handleConfirmPayment(payment.id, file);
                          }
                        }}
                        disabled={confirmingPayment === payment.id}
                        data-testid={`confirm-payment-${payment.id}`}
                        className="rounded-sm"
                      />
                    </div>
                  )}

                  {/* Aprobado - Vista colaborador */}
                  {payment.status === 'approved' && user.role === 'collaborator' && (
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-sm">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 size={18} className="text-emerald-700" />
                        <p className="text-sm font-medium text-emerald-900">
                          Cuenta de cobro aprobada. Pago en proceso.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Pagado */}
                  {payment.status === 'paid' && (
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-sm">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 size={18} className="text-emerald-700" />
                          <p className="text-sm font-medium text-emerald-900">Pago procesado exitosamente</p>
                        </div>
                        {payment.voucher_file_id && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-sm text-xs"
                            data-testid={`download-voucher-${payment.id}`}
                          >
                            <FileText size={14} className="mr-1" />
                            Descargar Comprobante
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Dialog para rechazar cuenta de cobro */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-brand-navy">Rechazar Cuenta de Cobro</DialogTitle>
            <DialogDescription>
              Por favor indique el motivo del rechazo. El colaborador será notificado.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">Motivo del Rechazo</Label>
              <Textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Ej: La cuenta de cobro no incluye el IVA, por favor corregir..."
                data-testid="rejection-reason-input"
                className="rounded-sm"
                rows={4}
              />
            </div>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setShowRejectDialog(false);
                setRejectionReason('');
                setRejectingPayment(null);
              }}
              className="flex-1 rounded-sm"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleRejectPayment}
              disabled={!rejectionReason.trim()}
              data-testid="confirm-reject-button"
              className="flex-1 bg-red-600 hover:bg-red-700 text-white rounded-sm"
            >
              Rechazar Cuenta
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
};
