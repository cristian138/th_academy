import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { contractsAPI, usersAPI } from '../services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import { useEffect } from 'react';

export const NewContractPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [collaborators, setCollaborators] = useState([]);
  const [formData, setFormData] = useState({
    contract_type: 'service',
    collaborator_id: '',
    title: '',
    description: '',
    start_date: '',
    end_date: '',
    monthly_payment: '',
    payment_per_session: '',
    notes: ''
  });

  useEffect(() => {
    loadCollaborators();
  }, []);

  const loadCollaborators = async () => {
    try {
      const response = await usersAPI.list('collaborator');
      setCollaborators(response.data);
    } catch (error) {
      toast.error('Error al cargar colaboradores');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const contractData = {
        ...formData,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: formData.end_date ? new Date(formData.end_date).toISOString() : null,
        monthly_payment: formData.monthly_payment ? parseFloat(formData.monthly_payment) : null,
        payment_per_session: formData.payment_per_session ? parseFloat(formData.payment_per_session) : null
      };

      await contractsAPI.create(contractData);
      toast.success('Contrato creado exitosamente');
      navigate('/contracts');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear contrato');
    } finally {
      setLoading(false);
    }
  };

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

        <div>
          <h1 className="text-4xl font-bold text-brand-navy mb-2">Nuevo Contrato</h1>
          <p className="text-slate-600">Crear un nuevo contrato para un colaborador</p>
        </div>

        <Card className="border border-slate-200 rounded-sm max-w-3xl">
          <CardHeader>
            <CardTitle className="text-lg font-bold text-brand-navy">Información del Contrato</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label className="text-xs uppercase text-slate-500 font-bold">Tipo de Contrato</Label>
                  <Select
                    value={formData.contract_type}
                    onValueChange={(value) => setFormData({ ...formData, contract_type: value })}
                  >
                    <SelectTrigger data-testid="contract-type-select" className="rounded-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="service">Prestación de Servicios</SelectItem>
                      <SelectItem value="event">Por Sesión o Evento</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-xs uppercase text-slate-500 font-bold">Colaborador</Label>
                  <Select
                    value={formData.collaborator_id}
                    onValueChange={(value) => setFormData({ ...formData, collaborator_id: value })}
                  >
                    <SelectTrigger data-testid="collaborator-select" className="rounded-sm">
                      <SelectValue placeholder="Seleccione colaborador" />
                    </SelectTrigger>
                    <SelectContent>
                      {collaborators.map((collab) => (
                        <SelectItem key={collab.id} value={collab.id}>
                          {collab.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-xs uppercase text-slate-500 font-bold">Título del Contrato</Label>
                <Input
                  data-testid="title-input"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  className="rounded-sm"
                  placeholder="Ej: Contrato Entrenador de Fútbol"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs uppercase text-slate-500 font-bold">Descripción</Label>
                <Textarea
                  data-testid="description-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  className="rounded-sm"
                  rows={4}
                  placeholder="Descripción detallada del contrato"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label className="text-xs uppercase text-slate-500 font-bold">Fecha de Inicio</Label>
                  <Input
                    data-testid="start-date-input"
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    required
                    className="rounded-sm"
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-xs uppercase text-slate-500 font-bold">Fecha de Fin (Opcional)</Label>
                  <Input
                    data-testid="end-date-input"
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    className="rounded-sm"
                  />
                </div>
              </div>

              {formData.contract_type === 'service' ? (
                <div className="space-y-2">
                  <Label className="text-xs uppercase text-slate-500 font-bold">Pago Mensual (COP)</Label>
                  <Input
                    data-testid="monthly-payment-input"
                    type="number"
                    value={formData.monthly_payment}
                    onChange={(e) => setFormData({ ...formData, monthly_payment: e.target.value })}
                    required
                    className="rounded-sm"
                    placeholder="3500000"
                  />
                </div>
              ) : (
                <div className="space-y-2">
                  <Label className="text-xs uppercase text-slate-500 font-bold">Pago por Sesión (COP)</Label>
                  <Input
                    data-testid="session-payment-input"
                    type="number"
                    value={formData.payment_per_session}
                    onChange={(e) => setFormData({ ...formData, payment_per_session: e.target.value })}
                    required
                    className="rounded-sm"
                    placeholder="150000"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label className="text-xs uppercase text-slate-500 font-bold">Notas (Opcional)</Label>
                <Textarea
                  data-testid="notes-input"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="rounded-sm"
                  rows={3}
                  placeholder="Notas adicionales sobre el contrato"
                />
              </div>

              <Alert>
                <AlertDescription>
                  El sistema verificará automáticamente que el colaborador tenga todos los documentos obligatorios
                  antes de activar el contrato.
                </AlertDescription>
              </Alert>

              <div className="flex gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/contracts')}
                  className="flex-1 rounded-sm"
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={loading}
                  data-testid="submit-button"
                  className="flex-1 bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
                >
                  {loading ? 'Creando...' : 'Crear Contrato'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};
