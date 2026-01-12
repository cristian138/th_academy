import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { contractsAPI } from '../services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ArrowLeft, CheckCircle2, Upload, FileText, Download } from 'lucide-react';
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

export const ContractDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [signedFile, setSignedFile] = useState(null);
  
  // State for approve dialog
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [approveFile, setApproveFile] = useState(null);

  const loadContract = async () => {
    try {
      const response = await contractsAPI.get(id);
      setContract(response.data);
    } catch (error) {
      console.error('Error loading contract:', error);
      toast.error('Error al cargar el contrato');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContract();
  }, [id]);

  const handleReview = async () => {
    setActionLoading(true);
    try {
      await contractsAPI.review(id);
      toast.success('Contrato enviado para aprobación');
      loadContract();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al revisar contrato');
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!approveFile) {
      toast.error('Por favor seleccione el documento del contrato');
      return;
    }

    setActionLoading(true);
    try {
      await contractsAPI.approve(id, approveFile);
      toast.success('Contrato aprobado y documento cargado exitosamente');
      setShowApproveDialog(false);
      setApproveFile(null);
      loadContract();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al aprobar contrato');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUploadSigned = async () => {
    if (!signedFile) {
      toast.error('Por favor seleccione un archivo');
      return;
    }

    setActionLoading(true);
    try {
      await contractsAPI.uploadSigned(id, signedFile);
      toast.success('Contrato firmado cargado exitosamente');
      setSignedFile(null);
      loadContract();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al cargar contrato firmado');
    } finally {
      setActionLoading(false);
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

  if (!contract) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-slate-500">Contrato no encontrado</p>
          <Button onClick={() => navigate('/contracts')} className="mt-4">
            Volver a Contratos
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/contracts')}
            className="rounded-sm"
            data-testid="back-button"
          >
            <ArrowLeft size={18} className="mr-2" />
            Volver
          </Button>
        </div>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold text-brand-navy mb-2">{contract.title}</h1>
            <p className="text-slate-600">{contract.description}</p>
          </div>
          {getStatusBadge(contract.status)}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-brand-navy">Detalles del Contrato</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs uppercase text-slate-500 font-bold mb-1">Tipo de Contrato</p>
                    <p className="text-sm text-brand-navy">
                      {contract.contract_type === 'service' ? 'Prestación de Servicios' : 'Por Evento'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase text-slate-500 font-bold mb-1">Fecha de Inicio</p>
                    <p className="text-sm text-brand-navy">
                      {new Date(contract.start_date).toLocaleDateString('es-CO')}
                    </p>
                  </div>
                  {contract.end_date && (
                    <div>
                      <p className="text-xs uppercase text-slate-500 font-bold mb-1">Fecha de Fin</p>
                      <p className="text-sm text-brand-navy">
                        {new Date(contract.end_date).toLocaleDateString('es-CO')}
                      </p>
                    </div>
                  )}
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
                      <p className="text-xs uppercase text-slate-500 font-bold mb-1">Pago Por Sesión</p>
                      <p className="text-sm text-brand-navy font-semibold tabular-nums">
                        ${contract.payment_per_session.toLocaleString('es-CO')}
                      </p>
                    </div>
                  )}
                </div>
                {contract.notes && (
                  <div>
                    <p className="text-xs uppercase text-slate-500 font-bold mb-1">Notas</p>
                    <p className="text-sm text-slate-600">{contract.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Documentos del Contrato */}
            <Card className="border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-brand-navy">Documentos del Contrato</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Documento Original (para firmar) */}
                {contract.contract_file_id && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileText size={24} className="text-blue-700" />
                        <div>
                          <p className="font-semibold text-blue-900">Contrato Original</p>
                          <p className="text-sm text-blue-700">Documento para descargar y firmar</p>
                        </div>
                      </div>
                      <a
                        href={contractsAPI.downloadFile(contract.contract_file_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-sm hover:bg-blue-700 transition-colors text-sm font-medium"
                        data-testid="download-contract-btn"
                      >
                        <Download size={16} />
                        Descargar
                      </a>
                    </div>
                  </div>
                )}

                {/* Documento Firmado */}
                {contract.signed_file_id && (
                  <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 size={24} className="text-emerald-700" />
                        <div>
                          <p className="font-semibold text-emerald-900">Contrato Firmado</p>
                          <p className="text-sm text-emerald-700">Documento firmado por el colaborador</p>
                        </div>
                      </div>
                      <a
                        href={contractsAPI.downloadFile(contract.signed_file_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-sm hover:bg-emerald-700 transition-colors text-sm font-medium"
                        data-testid="download-signed-btn"
                      >
                        <Download size={16} />
                        Descargar
                      </a>
                    </div>
                  </div>
                )}

                {/* Sin documentos */}
                {!contract.contract_file_id && !contract.signed_file_id && (
                  <div className="text-center py-6 text-slate-500">
                    <FileText size={32} className="mx-auto mb-2 opacity-50" />
                    <p>No hay documentos disponibles aún</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Colaborador: Cargar contrato firmado */}
            {contract.status === 'approved' && user.role === 'collaborator' && contract.contract_file_id && (
              <Card className="border border-slate-200 rounded-sm">
                <CardHeader>
                  <CardTitle className="text-lg font-bold text-brand-navy">Cargar Contrato Firmado</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Alert>
                    <AlertDescription>
                      El contrato ha sido aprobado. Por favor descargue el documento original, fírmelo y cárguelo nuevamente.
                    </AlertDescription>
                  </Alert>
                  <div>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setSignedFile(e.target.files[0])}
                      data-testid="contract-file-input"
                      className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-sm file:border-0 file:text-xs file:font-bold file:uppercase file:bg-brand-navy file:text-white hover:file:bg-brand-navy/90"
                    />
                  </div>
                  <Button
                    onClick={handleUploadSigned}
                    disabled={!signedFile || actionLoading}
                    data-testid="upload-signed-button"
                    className="w-full bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
                  >
                    <Upload size={18} className="mr-2" />
                    {actionLoading ? 'Cargando...' : 'Cargar Contrato Firmado'}
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <Card className="border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-brand-navy">Acciones</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {contract.status === 'under_review' && hasRole('admin') && (
                  <Button
                    onClick={handleReview}
                    disabled={actionLoading}
                    data-testid="review-contract-button"
                    className="w-full bg-brand-blue hover:bg-brand-blue/90 text-white rounded-sm"
                  >
                    <CheckCircle2 size={18} className="mr-2" />
                    Enviar para Aprobación
                  </Button>
                )}
                {contract.status === 'pending_approval' && hasRole('legal_rep') && (
                  <Button
                    onClick={() => setShowApproveDialog(true)}
                    disabled={actionLoading}
                    data-testid="approve-contract-button"
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-sm"
                  >
                    <CheckCircle2 size={18} className="mr-2" />
                    Aprobar Contrato
                  </Button>
                )}
                
                {/* Estado del contrato */}
                {contract.status === 'approved' && !contract.signed_file_id && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-sm text-sm text-amber-800">
                    Esperando que el colaborador firme y cargue el contrato
                  </div>
                )}
                {contract.status === 'active' && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-sm text-sm text-emerald-800">
                    Contrato activo y firmado
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Dialog para aprobar y subir documento */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-brand-navy">Aprobar Contrato</DialogTitle>
            <DialogDescription>
              Para aprobar el contrato, debe cargar el documento que el colaborador descargará, firmará y volverá a subir.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Documento del Contrato (PDF)
              </Label>
              <Input
                type="file"
                accept=".pdf"
                onChange={(e) => setApproveFile(e.target.files[0])}
                data-testid="approve-file-input"
                className="rounded-sm"
              />
              <p className="text-xs text-slate-500">
                Este documento será enviado al colaborador para que lo firme
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setShowApproveDialog(false);
                setApproveFile(null);
              }}
              className="flex-1 rounded-sm"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleApprove}
              disabled={!approveFile || actionLoading}
              data-testid="confirm-approve-button"
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-sm"
            >
              {actionLoading ? 'Aprobando...' : 'Aprobar y Cargar'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
};
