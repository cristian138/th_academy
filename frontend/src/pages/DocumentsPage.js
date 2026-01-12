import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { documentsAPI } from '../services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Upload, FileText, CheckCircle2, XCircle, Clock, AlertTriangle } from 'lucide-react';

const documentTypes = {
  cedula: 'Cédula de Ciudadanía',
  rut: 'RUT',
  cert_laboral: 'Certificación Laboral',
  cert_educativa: 'Certificación Educativa',
  cuenta_bancaria: 'Cuenta Bancaria',
  antecedentes: 'Antecedentes',
  licencia: 'Licencia de Trabajo'
};

const getStatusBadge = (status) => {
  const statusMap = {
    pending: { label: 'Pendiente', class: 'bg-slate-100 text-slate-700 border-slate-200', icon: Clock },
    uploaded: { label: 'Cargado', class: 'bg-blue-100 text-blue-700 border-blue-200', icon: Upload },
    under_review: { label: 'En Revisión', class: 'bg-amber-100 text-amber-700 border-amber-200', icon: Clock },
    approved: { label: 'Aprobado', class: 'bg-emerald-100 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
    rejected: { label: 'Rechazado', class: 'bg-red-100 text-red-700 border-red-200', icon: XCircle },
    expired: { label: 'Vencido', class: 'bg-red-100 text-red-700 border-red-200', icon: AlertTriangle }
  };
  const statusInfo = statusMap[status] || statusMap.pending;
  const Icon = statusInfo.icon;
  return (
    <Badge className={`${statusInfo.class} px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border flex items-center gap-1`}>
      <Icon size={12} />
      {statusInfo.label}
    </Badge>
  );
};

export const DocumentsPage = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedType, setSelectedType] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [expiryDate, setExpiryDate] = useState('');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.list();
      setDocuments(response.data);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedType || !selectedFile) {
      toast.error('Por favor seleccione tipo de documento y archivo');
      return;
    }

    setUploading(true);
    try {
      await documentsAPI.upload(selectedType, selectedFile, expiryDate || null);
      toast.success('Documento cargado exitosamente');
      setSelectedType('');
      setSelectedFile(null);
      setExpiryDate('');
      loadDocuments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al cargar documento');
    } finally {
      setUploading(false);
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
        <div>
          <h1 className="text-4xl font-bold text-brand-navy mb-2">Documentos</h1>
          <p className="text-slate-600">Gestione sus documentos requeridos</p>
        </div>

        {user.role === 'collaborator' && (
          <Card className="border border-slate-200 rounded-sm">
            <CardHeader>
              <CardTitle className="text-lg font-bold text-brand-navy">Cargar Nuevo Documento</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs uppercase text-slate-500 font-bold">Tipo de Documento</Label>
                  <Select value={selectedType} onValueChange={setSelectedType}>
                    <SelectTrigger data-testid="document-type-select" className="rounded-sm">
                      <SelectValue placeholder="Seleccione tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(documentTypes).map(([key, label]) => (
                        <SelectItem key={key} value={key}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {(selectedType === 'cuenta_bancaria' || selectedType === 'antecedentes') && (
                  <div className="space-y-2">
                    <Label className="text-xs uppercase text-slate-500 font-bold">Fecha de Vencimiento</Label>
                    <Input
                      type="date"
                      value={expiryDate}
                      onChange={(e) => setExpiryDate(e.target.value)}
                      data-testid="expiry-date-input"
                      className="rounded-sm"
                    />
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label className="text-xs uppercase text-slate-500 font-bold">Archivo</Label>
                <Input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                  data-testid="file-input"
                  className="rounded-sm"
                />
                <p className="text-xs text-slate-500">Formatos: PDF, JPG, PNG. Máximo 10MB</p>
              </div>

              <Button
                onClick={handleUpload}
                disabled={uploading || !selectedType || !selectedFile}
                data-testid="upload-button"
                className="w-full bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
              >
                <Upload size={18} className="mr-2" />
                {uploading ? 'Cargando...' : 'Cargar Documento'}
              </Button>
            </CardContent>
          </Card>
        )}

        <div>
          <h2 className="text-xl font-bold text-brand-navy mb-4">Documentos Cargados</h2>
          {documents.length === 0 ? (
            <Card className="border border-slate-200 rounded-sm">
              <CardContent className="py-12 text-center">
                <FileText size={48} className="mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500">No hay documentos cargados</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {documents.map((doc) => (
                <Card
                  key={doc.id}
                  className="border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                  data-testid={`document-card-${doc.id}`}
                >
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 flex-1">
                        <div className="p-3 bg-slate-50 rounded-sm">
                          <FileText size={24} className="text-brand-navy" />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-brand-navy">{documentTypes[doc.document_type]}</p>
                          <p className="text-sm text-slate-600">{doc.file_name}</p>
                          {doc.expiry_date && (
                            <p className="text-xs text-slate-500 mt-1">
                              Vence: {new Date(doc.expiry_date).toLocaleDateString('es-CO')}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        {getStatusBadge(doc.status)}
                        {doc.file_url && doc.file_url !== '#' && (
                          <a
                            href={doc.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-brand-blue hover:text-brand-blue/80 text-sm font-medium"
                          >
                            Ver
                          </a>
                        )}
                      </div>
                    </div>
                    {doc.review_notes && (
                      <div className="mt-3 p-3 bg-amber-50 rounded-sm border border-amber-200">
                        <p className="text-xs uppercase text-amber-700 font-bold mb-1">Nota de Revisión</p>
                        <p className="text-sm text-amber-900">{doc.review_notes}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};
