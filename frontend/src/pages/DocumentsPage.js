import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FileText, ArrowRight } from 'lucide-react';

export const DocumentsPage = () => {
  const navigate = useNavigate();

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-4xl font-bold text-brand-navy mb-2">Documentos</h1>
          <p className="text-slate-600">Los documentos se gestionan desde cada contrato</p>
        </div>

        <Card className="border border-slate-200 rounded-sm">
          <CardContent className="py-12 text-center">
            <FileText size={48} className="mx-auto mb-4 text-slate-300" />
            <h2 className="text-xl font-bold text-brand-navy mb-2">
              Documentos Asociados a Contratos
            </h2>
            <p className="text-slate-600 mb-6 max-w-md mx-auto">
              Los documentos (cédula, RUT, certificaciones, etc.) ahora se cargan y gestionan 
              directamente desde cada contrato. Vaya a la sección de contratos para cargar 
              sus documentos.
            </p>
            <Button
              onClick={() => navigate('/contracts')}
              className="bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
            >
              Ir a Contratos
              <ArrowRight size={18} className="ml-2" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};
