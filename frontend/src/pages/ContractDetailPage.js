import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { contractsAPI, documentsAPI } from '../services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ArrowLeft, CheckCircle2, Upload, FileText, Download, XCircle, Clock, AlertCircle } from 'lucide-react';
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

const getDocStatusIcon = (status) => {
  if (status === 'approved') return <CheckCircle2 size={18} className="text-emerald-600" />;
  if (status === 'rejected') return <XCircle size={18} className="text-red-600" />;
  if (status === 'uploaded') return <Clock size={18} className="text-amber-600" />;
  return <AlertCircle size={18} className="text-slate-400" />;
};

export const ContractDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const [contract, setContract] = useState(null);
  const [documents, setDocuments] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(null);
  const [signedFile, setSignedFile] = useState(null);
  
  // State for approve dialog
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [approveFile, setApproveFile] = useState(null);
  
  // State for document review
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewingDoc, setReviewingDoc] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');

  const loadContract = async () => {
    try {
      const response = await contractsAPI.get(id);
      setContract(response.data);
    } catch (error) {
      console.error('Error loading contract:', error);
      toast.error('Error al cargar el contrato');
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.getContractDocuments(id);
      setDocuments(response.data);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContract();
    loadDocuments();
  }, [id]);

  const handleUploadDocument = async (docType, file) => {
    setUploadingDoc(docType);
    try {
      await documentsAPI.uploadContractDocument(id, docType, file);
      toast.success('Documento cargado exitosamente');
      loadDocuments();
      loadContract();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al cargar documento');
    } finally {
      setUploadingDoc(null);
    }
  };

  const handleReviewDocument = async (status) => {
    if (!reviewingDoc) return;
    
    setActionLoading(true);
    try {
      await documentsAPI.review(reviewingDoc.document.id, {
        status: status,
        review_notes: reviewNotes || null
      });
      toast.success(status === 'approved' ? 'Documento aprobado' : 'Documento rechazado');
      setShowReviewDialog(false);
      setReviewingDoc(null);
      setReviewNotes('');
      loadDocuments();
      loadContract();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al revisar documento');
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

  const canUploadDocuments = user.role === 'collaborator' && 
    ['pending_documents', 'under_review'].includes(contract.status);
  
  const canReviewDocuments = hasRole('admin') && 
    ['under_review', 'pending_approval'].includes(contract.status);

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
            {/* Detalles del Contrato */}
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
                </div>
              </CardContent>
            </Card>

            {/* Documentos del Contrato */}
            {documents && (
              <Card className="border border-slate-200 rounded-sm">
                <CardHeader>
                  <CardTitle className="text-lg font-bold text-brand-navy">
                    Documentos Requeridos
                    {documents.all_required_approved && (
                      <Badge className="ml-2 bg-emerald-100 text-emerald-700 border-emerald-200">
                        Completos
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {documents.required_documents.map((doc) => (
                    <div 
                      key={doc.type}
                      className={`p-4 border rounded-sm ${
                        doc.status === 'approved' ? 'bg-emerald-50 border-emerald-200' :
                        doc.status === 'rejected' ? 'bg-red-50 border-red-200' :
                        doc.uploaded ? 'bg-amber-50 border-amber-200' :
                        'bg-slate-50 border-slate-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getDocStatusIcon(doc.status)}
                          <div>
                            <p className="font-medium text-brand-navy">{doc.label}</p>
                            <p className="text-xs text-slate-500">
                              {doc.status === 'approved' ? 'Aprobado' :
                               doc.status === 'rejected' ? 'Rechazado - debe corregir' :
                               doc.uploaded ? 'Pendiente de revisión' :
                               'No cargado'}
                            </p>
                            {doc.document?.review_notes && doc.status === 'rejected' && (
                              <p className="text-xs text-red-600 mt-1">
                                Motivo: {doc.document.review_notes}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {doc.uploaded && doc.document?.file_id && (
                            <a
                              href={documentsAPI.downloadFile(doc.document.file_id)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded-sm"
                              title="Ver documento"
                            >
                              <FileText size={18} />
                            </a>
                          )}
                          
                          {/* Colaborador: Cargar documento */}
                          {canUploadDocuments && (!doc.uploaded || doc.status === 'rejected') && (
                            <div>
                              <Input
                                type="file"
                                accept=".pdf,.jpg,.jpeg,.png"
                                onChange={(e) => {
                                  const file = e.target.files[0];
                                  if (file) handleUploadDocument(doc.type, file);
                                }}
                                disabled={uploadingDoc === doc.type}
                                className="hidden"
                                id={`upload-${doc.type}`}
                              />
                              <label htmlFor={`upload-${doc.type}`}>
                                <Button
                                  asChild
                                  size="sm"
                                  variant={doc.status === 'rejected' ? 'destructive' : 'default'}
                                  className="cursor-pointer rounded-sm"
                                  disabled={uploadingDoc === doc.type}
                                >
                                  <span>
                                    <Upload size={14} className="mr-1" />
                                    {uploadingDoc === doc.type ? 'Cargando...' : 'Cargar'}
                                  </span>
                                </Button>
                              </label>
                            </div>
                          )}
                          
                          {/* Admin: Revisar documento */}
                          {canReviewDocuments && doc.uploaded && doc.status === 'uploaded' && (
                            <Button
                              size="sm"
                              onClick={() => {
                                setReviewingDoc(doc);
                                setShowReviewDialog(true);
                              }}
                              className="rounded-sm bg-brand-navy"
                            >
                              Revisar
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* Documentos Opcionales */}
                  {documents.optional_documents.length > 0 && (
                    <>
                      <div className="border-t pt-4 mt-4">
                        <p className="text-sm font-bold text-slate-500 uppercase mb-3">Documentos Opcionales</p>
                      </div>
                      {documents.optional_documents.map((doc) => (
                        <div 
                          key={doc.type}
                          className={`p-4 border rounded-sm ${
                            doc.status === 'approved' ? 'bg-emerald-50 border-emerald-200' :
                            doc.status === 'rejected' ? 'bg-red-50 border-red-200' :
                            doc.uploaded ? 'bg-amber-50 border-amber-200' :
                            'bg-slate-50 border-slate-200'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              {getDocStatusIcon(doc.status)}
                              <div>
                                <p className="font-medium text-brand-navy">{doc.label}</p>
                                <p className="text-xs text-slate-500">
                                  {doc.uploaded ? (doc.status === 'approved' ? 'Aprobado' : 'Pendiente') : 'Opcional'}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {doc.uploaded && doc.document?.file_id && (
                                <a
                                  href={documentsAPI.downloadFile(doc.document.file_id)}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-sm"
                                >
                                  <FileText size={18} />
                                </a>
                              )}
                              {canUploadDocuments && !doc.uploaded && (
                                <div>
                                  <Input
                                    type="file"
                                    accept=".pdf,.jpg,.jpeg,.png"
                                    onChange={(e) => {
                                      const file = e.target.files[0];
                                      if (file) handleUploadDocument(doc.type, file);
                                    }}
                                    disabled={uploadingDoc === doc.type}
                                    className="hidden"
                                    id={`upload-${doc.type}`}
                                  />
                                  <label htmlFor={`upload-${doc.type}`}>
                                    <Button asChild size="sm" variant="outline" className="cursor-pointer rounded-sm">
                                      <span>
                                        <Upload size={14} className="mr-1" />
                                        Cargar
                                      </span>
                                    </Button>
                                  </label>
                                </div>
                              )}
                              {canReviewDocuments && doc.uploaded && doc.status === 'uploaded' && (
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    setReviewingDoc(doc);
                                    setShowReviewDialog(true);
                                  }}
                                  className="rounded-sm bg-brand-navy"
                                >
                                  Revisar
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Documentos del Contrato (Original y Firmado) */}
            {(contract.contract_file_id || contract.signed_file_id) && (
              <Card className="border border-slate-200 rounded-sm">
                <CardHeader>
                  <CardTitle className="text-lg font-bold text-brand-navy">Archivo del Contrato</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {contract.contract_file_id && (
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-sm">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FileText size={24} className="text-blue-700" />
                          <div>
                            <p className="font-semibold text-blue-900">Contrato Original</p>
                            <p className="text-sm text-blue-700">Documento para firmar</p>
                          </div>
                        </div>
                        <a
                          href={contractsAPI.downloadFile(contract.contract_file_id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-sm hover:bg-blue-700"
                        >
                          <Download size={16} />
                          Descargar
                        </a>
                      </div>
                    </div>
                  )}
                  {contract.signed_file_id && (
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-sm">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <CheckCircle2 size={24} className="text-emerald-700" />
                          <div>
                            <p className="font-semibold text-emerald-900">Contrato Firmado</p>
                            <p className="text-sm text-emerald-700">Documento firmado</p>
                          </div>
                        </div>
                        <a
                          href={contractsAPI.downloadFile(contract.signed_file_id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-sm hover:bg-emerald-700"
                        >
                          <Download size={16} />
                          Descargar
                        </a>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Colaborador: Cargar contrato firmado */}
            {contract.status === 'approved' && user.role === 'collaborator' && contract.contract_file_id && (
              <Card className="border border-slate-200 rounded-sm">
                <CardHeader>
                  <CardTitle className="text-lg font-bold text-brand-navy">Cargar Contrato Firmado</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Alert>
                    <AlertDescription>
                      Descargue el contrato original, fírmelo y cárguelo nuevamente.
                    </AlertDescription>
                  </Alert>
                  <Input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setSignedFile(e.target.files[0])}
                  />
                  <Button
                    onClick={handleUploadSigned}
                    disabled={!signedFile || actionLoading}
                    className="w-full bg-brand-navy hover:bg-brand-navy/90 rounded-sm"
                  >
                    <Upload size={18} className="mr-2" />
                    {actionLoading ? 'Cargando...' : 'Cargar Contrato Firmado'}
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar - Acciones */}
          <div className="space-y-6">
            <Card className="border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-brand-navy">Acciones</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Admin: Enviar a aprobación cuando todos los docs estén aprobados */}
                {contract.status === 'under_review' && hasRole('admin') && documents?.all_required_approved && (
                  <Button
                    onClick={handleReview}
                    disabled={actionLoading}
                    className="w-full bg-brand-blue hover:bg-brand-blue/90 text-white rounded-sm"
                  >
                    <CheckCircle2 size={18} className="mr-2" />
                    Enviar para Aprobación
                  </Button>
                )}
                
                {/* Mensaje si faltan documentos */}
                {contract.status === 'under_review' && hasRole('admin') && !documents?.all_required_approved && (
                  <Alert className="border-amber-200 bg-amber-50">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    <AlertDescription className="text-amber-800">
                      Debe aprobar todos los documentos obligatorios antes de enviar a aprobación.
                    </AlertDescription>
                  </Alert>
                )}

                {/* Legal Rep: Aprobar contrato */}
                {contract.status === 'pending_approval' && hasRole('legal_rep') && (
                  <Button
                    onClick={() => setShowApproveDialog(true)}
                    disabled={actionLoading}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-sm"
                  >
                    <CheckCircle2 size={18} className="mr-2" />
                    Aprobar Contrato
                  </Button>
                )}
                
                {/* Estados informativos */}
                {contract.status === 'pending_documents' && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-sm text-sm text-amber-800">
                    Esperando que el colaborador cargue los documentos requeridos
                  </div>
                )}
                {contract.status === 'approved' && !contract.signed_file_id && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-sm text-sm text-amber-800">
                    Esperando que el colaborador firme y cargue el contrato
                  </div>
                )}
                {contract.status === 'active' && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-sm text-sm text-emerald-800">
                    <CheckCircle2 size={16} className="inline mr-2" />
                    Contrato activo
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Dialog: Aprobar contrato con documento */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-brand-navy">Aprobar Contrato</DialogTitle>
            <DialogDescription>
              Cargue el documento del contrato que el colaborador descargará, firmará y volverá a subir.
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
                className="rounded-sm"
              />
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
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-sm"
            >
              {actionLoading ? 'Aprobando...' : 'Aprobar y Cargar'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Revisar documento */}
      <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-brand-navy">
              Revisar: {reviewingDoc?.label}
            </DialogTitle>
            <DialogDescription>
              Revise el documento y apruebe o rechace según corresponda.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {reviewingDoc?.document?.file_id && (
              <a
                href={documentsAPI.downloadFile(reviewingDoc.document.file_id)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-sm text-blue-700 hover:bg-blue-100"
              >
                <FileText size={20} />
                <span>Ver documento</span>
              </a>
            )}
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Notas (opcional, requerido si rechaza)
              </Label>
              <Textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Motivo del rechazo o comentarios..."
                className="rounded-sm"
                rows={3}
              />
            </div>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => handleReviewDocument('rejected')}
              disabled={actionLoading}
              className="flex-1 border-red-300 text-red-700 hover:bg-red-50 rounded-sm"
            >
              <XCircle size={16} className="mr-2" />
              Rechazar
            </Button>
            <Button
              onClick={() => handleReviewDocument('approved')}
              disabled={actionLoading}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-sm"
            >
              <CheckCircle2 size={16} className="mr-2" />
              Aprobar
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
};
