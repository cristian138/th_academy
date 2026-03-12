import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, Trash2, CheckCircle2, AlertCircle, PenTool } from 'lucide-react';
import { toast } from 'sonner';
import api from '../services/api';

export const SettingsPage = () => {
  const { user, hasRole } = useAuth();
  const [signatureExists, setSignatureExists] = useState(false);
  const [signatureUrl, setSignatureUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const canManageSignature = hasRole('superadmin') || hasRole('legal_rep');

  useEffect(() => {
    checkSignature();
  }, []);

  const checkSignature = async () => {
    try {
      const response = await api.get('/settings/signature/exists');
      setSignatureExists(response.data.exists);
      if (response.data.exists) {
        // Get the signature image URL with token
        const token = localStorage.getItem('token');
        setSignatureUrl(`${process.env.REACT_APP_BACKEND_URL}/api/settings/signature?token=${token}&t=${Date.now()}`);
      }
    } catch (error) {
      console.error('Error checking signature:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
        toast.error('Solo se permiten imágenes PNG o JPG');
        return;
      }
      
      // Validate file size (max 2MB)
      if (file.size > 2 * 1024 * 1024) {
        toast.error('La imagen no debe superar 2MB');
        return;
      }
      
      setSelectedFile(file);
      // Create preview URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      await api.post('/settings/signature', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast.success('Firma cargada exitosamente');
      setSelectedFile(null);
      setPreviewUrl(null);
      checkSignature();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al cargar la firma');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('¿Está seguro de eliminar la firma? Los certificados se generarán sin firma.')) {
      return;
    }
    
    try {
      await api.delete('/settings/signature');
      toast.success('Firma eliminada');
      setSignatureExists(false);
      setSignatureUrl(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar la firma');
    }
  };

  const cancelSelection = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
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
      <div className="space-y-6 max-w-4xl">
        <div>
          <h1 className="text-4xl font-bold text-brand-navy mb-2">Configuración</h1>
          <p className="text-slate-600">Administre la configuración del sistema</p>
        </div>

        {/* Firma Digital */}
        <Card className="border border-slate-200 rounded-sm">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-brand-navy/10 rounded-sm">
                <PenTool size={24} className="text-brand-navy" />
              </div>
              <div>
                <CardTitle className="text-lg font-bold text-brand-navy">Firma para Documentos</CardTitle>
                <CardDescription>
                  Esta firma se insertará automáticamente en todos los certificados laborales generados
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {!canManageSignature ? (
              <Alert className="border-amber-200 bg-amber-50">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  Solo el Superadministrador o Representante Legal pueden gestionar la firma.
                </AlertDescription>
              </Alert>
            ) : (
              <>
                {/* Current Signature */}
                {signatureExists && (
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-slate-700">Firma actual:</p>
                    <div className="flex items-center gap-4">
                      <div className="p-4 bg-slate-50 border border-slate-200 rounded-sm">
                        <img 
                          src={signatureUrl} 
                          alt="Firma actual" 
                          className="max-h-24 object-contain"
                        />
                      </div>
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-2 text-emerald-700">
                          <CheckCircle2 size={16} />
                          <span className="text-sm font-medium">Firma configurada</span>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleDelete}
                          className="text-red-600 border-red-200 hover:bg-red-50 rounded-sm"
                          data-testid="delete-signature-btn"
                        >
                          <Trash2 size={14} className="mr-1" />
                          Eliminar firma
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Upload New Signature */}
                <div className="space-y-3">
                  <p className="text-sm font-medium text-slate-700">
                    {signatureExists ? 'Cambiar firma:' : 'Cargar firma:'}
                  </p>
                  
                  {!selectedFile ? (
                    <div className="border-2 border-dashed border-slate-300 rounded-sm p-8 text-center hover:border-brand-navy/50 transition-colors">
                      <Input
                        type="file"
                        accept="image/png,image/jpeg,image/jpg"
                        onChange={handleFileSelect}
                        className="hidden"
                        id="signature-upload"
                      />
                      <label htmlFor="signature-upload" className="cursor-pointer">
                        <Upload size={32} className="mx-auto mb-3 text-slate-400" />
                        <p className="text-sm text-slate-600 mb-1">
                          Haga clic para seleccionar una imagen
                        </p>
                        <p className="text-xs text-slate-400">
                          PNG o JPG, máximo 2MB. Se recomienda fondo transparente.
                        </p>
                      </label>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="p-4 bg-slate-50 border border-slate-200 rounded-sm">
                        <p className="text-sm font-medium text-slate-700 mb-2">Vista previa:</p>
                        <img 
                          src={previewUrl} 
                          alt="Vista previa" 
                          className="max-h-32 object-contain mx-auto"
                        />
                      </div>
                      <div className="flex gap-3">
                        <Button
                          variant="outline"
                          onClick={cancelSelection}
                          className="flex-1 rounded-sm"
                        >
                          Cancelar
                        </Button>
                        <Button
                          onClick={handleUpload}
                          disabled={uploading}
                          className="flex-1 bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
                          data-testid="upload-signature-btn"
                        >
                          <Upload size={16} className="mr-2" />
                          {uploading ? 'Cargando...' : 'Guardar Firma'}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

                <Alert className="border-blue-200 bg-blue-50">
                  <AlertCircle className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-blue-800">
                    <strong>Recomendación:</strong> Use una imagen con fondo transparente (PNG) para mejores resultados en los documentos.
                  </AlertDescription>
                </Alert>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};
