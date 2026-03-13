import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import api from '../services/api';

export const VerifyCertificatePage = () => {
  const { code } = useParams();
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState(null);

  useEffect(() => {
    verifyCertificate();
  }, [code]);

  const verifyCertificate = async () => {
    try {
      const response = await api.get(`/certificates/verify/${code}`);
      setResult(response.data);
    } catch (error) {
      setResult({
        valid: false,
        message: 'Error al verificar el certificado'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md border border-slate-200 rounded-sm shadow-lg">
        <CardHeader className="text-center bg-[#002d54] text-white rounded-t-sm">
          <CardTitle className="text-xl font-bold">
            Verificación de Certificado
          </CardTitle>
          <p className="text-sm text-blue-100">Academia Jotuns Club SAS</p>
        </CardHeader>
        <CardContent className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <Loader2 size={48} className="animate-spin mx-auto text-[#002d54] mb-4" />
              <p className="text-slate-600">Verificando certificado...</p>
            </div>
          ) : result?.valid ? (
            <div className="text-center">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 size={48} className="text-emerald-600" />
              </div>
              <h2 className="text-xl font-bold text-emerald-700 mb-2">
                Certificado Válido
              </h2>
              <p className="text-slate-600 mb-4">
                Este certificado ha sido verificado y es auténtico.
              </p>
              
              <div className="bg-slate-50 border border-slate-200 rounded-sm p-4 text-left mt-4">
                <p className="text-sm text-slate-500 mb-1">Colaborador:</p>
                <p className="font-semibold text-slate-800 mb-3">
                  {result.data?.collaborator_name}
                </p>
                
                <p className="text-sm text-slate-500 mb-1">Contrato:</p>
                <p className="font-semibold text-slate-800 mb-3">
                  {result.data?.contract_title}
                </p>
                
                <p className="text-sm text-slate-500 mb-1">Fecha de generación:</p>
                <p className="font-semibold text-slate-800">
                  {result.data?.generated_at || 'N/A'}
                </p>
              </div>
              
              <p className="text-xs text-slate-400 mt-4">
                Código de verificación: {code}
              </p>
            </div>
          ) : (
            <div className="text-center">
              <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <XCircle size={48} className="text-red-600" />
              </div>
              <h2 className="text-xl font-bold text-red-700 mb-2">
                Certificado No Válido
              </h2>
              <p className="text-slate-600 mb-4">
                {result?.message || 'No se pudo verificar este certificado.'}
              </p>
              <p className="text-xs text-slate-400 mt-4">
                Código consultado: {code}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
