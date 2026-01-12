import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { usersAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Users, Mail, Phone, CreditCard, Plus, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

export const CollaboratorsPage = () => {
  const { user: currentUser } = useAuth();
  const [collaborators, setCollaborators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    password: '',
    phone: '',
    identification: ''
  });
  const [actionLoading, setActionLoading] = useState(false);

  const isSuperAdmin = currentUser?.role === 'superadmin';

  useEffect(() => {
    loadCollaborators();
  }, []);

  const loadCollaborators = async () => {
    try {
      const response = await usersAPI.list('collaborator');
      setCollaborators(response.data);
    } catch (error) {
      console.error('Error loading collaborators:', error);
      toast.error('Error al cargar colaboradores');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      email: '',
      name: '',
      password: '',
      phone: '',
      identification: ''
    });
  };

  const handleCreate = async () => {
    if (!formData.email || !formData.name || !formData.password) {
      toast.error('Complete los campos obligatorios');
      return;
    }

    setActionLoading(true);
    try {
      await usersAPI.create({
        ...formData,
        role: 'collaborator'
      });
      toast.success('Colaborador creado exitosamente. Se envió un correo con las credenciales.');
      setShowCreateDialog(false);
      resetForm();
      loadCollaborators();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear colaborador');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEdit = async () => {
    if (!formData.name) {
      toast.error('El nombre es obligatorio');
      return;
    }

    setActionLoading(true);
    try {
      await usersAPI.update(selectedUser.id, {
        name: formData.name,
        phone: formData.phone || null,
        is_active: formData.is_active
      });
      toast.success('Colaborador actualizado exitosamente');
      setShowEditDialog(false);
      setSelectedUser(null);
      resetForm();
      loadCollaborators();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar colaborador');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    setActionLoading(true);
    try {
      await usersAPI.delete(selectedUser.id);
      toast.success('Colaborador eliminado exitosamente');
      setShowDeleteDialog(false);
      setSelectedUser(null);
      loadCollaborators();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar colaborador');
    } finally {
      setActionLoading(false);
    }
  };

  const openEditDialog = (user) => {
    setSelectedUser(user);
    setFormData({
      name: user.name,
      phone: user.phone || '',
      is_active: user.is_active
    });
    setShowEditDialog(true);
  };

  const openDeleteDialog = (user) => {
    setSelectedUser(user);
    setShowDeleteDialog(true);
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
            <h1 className="text-4xl font-bold text-brand-navy mb-2">Colaboradores</h1>
            <p className="text-slate-600">Gestione los colaboradores de la academia</p>
          </div>
          <Button
            onClick={() => {
              resetForm();
              setShowCreateDialog(true);
            }}
            className="bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
            data-testid="create-collaborator-btn"
          >
            <Plus size={18} className="mr-2" />
            Nuevo Colaborador
          </Button>
        </div>

        {collaborators.length === 0 ? (
          <Card className="border border-slate-200 rounded-sm">
            <CardContent className="py-12 text-center">
              <Users size={48} className="mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500 mb-4">No hay colaboradores registrados</p>
              <Button
                onClick={() => {
                  resetForm();
                  setShowCreateDialog(true);
                }}
                className="bg-brand-navy hover:bg-brand-navy/90"
              >
                <Plus size={18} className="mr-2" />
                Crear Primer Colaborador
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {collaborators.map((collaborator) => (
              <Card
                key={collaborator.id}
                className={`border rounded-sm transition-colors ${
                  collaborator.is_active 
                    ? 'border-slate-200 hover:border-brand-blue/50' 
                    : 'border-red-200 bg-red-50/30'
                }`}
                data-testid={`collaborator-card-${collaborator.id}`}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg font-bold text-brand-navy mb-1">
                        {collaborator.name}
                      </CardTitle>
                      <Badge className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border ${
                        collaborator.is_active 
                          ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
                          : 'bg-red-100 text-red-700 border-red-200'
                      }`}>
                        {collaborator.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${
                      collaborator.is_active ? 'bg-emerald-500' : 'bg-red-500'
                    }`}></div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <Mail size={16} strokeWidth={1.5} />
                    <span className="truncate">{collaborator.email}</span>
                  </div>
                  {collaborator.phone && (
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Phone size={16} strokeWidth={1.5} />
                      <span>{collaborator.phone}</span>
                    </div>
                  )}
                  {collaborator.identification && (
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <CreditCard size={16} strokeWidth={1.5} />
                      <span>CC: {collaborator.identification}</span>
                    </div>
                  )}
                  <div className="flex gap-2 pt-3 border-t border-slate-100">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openEditDialog(collaborator)}
                      className="flex-1 rounded-sm text-xs"
                    >
                      <Pencil size={14} className="mr-1" />
                      Editar
                    </Button>
                    {isSuperAdmin && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openDeleteDialog(collaborator)}
                        className="rounded-sm text-xs text-red-600 border-red-200 hover:bg-red-50"
                      >
                        <Trash2 size={14} />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Dialog: Crear Colaborador */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-brand-navy">Nuevo Colaborador</DialogTitle>
            <DialogDescription>
              Complete los datos para registrar un nuevo colaborador. Se enviará un correo con las credenciales de acceso.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Nombre Completo *
              </Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Juan Pérez"
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Correo Electrónico *
              </Label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="colaborador@ejemplo.com"
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Contraseña Inicial *
              </Label>
              <Input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="Mínimo 6 caracteres"
                className="rounded-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-xs uppercase text-slate-500 font-bold">
                  Cédula
                </Label>
                <Input
                  value={formData.identification}
                  onChange={(e) => setFormData({...formData, identification: e.target.value})}
                  placeholder="123456789"
                  className="rounded-sm"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs uppercase text-slate-500 font-bold">
                  Teléfono
                </Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  placeholder="300 123 4567"
                  className="rounded-sm"
                />
              </div>
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
              onClick={handleCreate}
              disabled={actionLoading}
              className="flex-1 bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
            >
              {actionLoading ? 'Creando...' : 'Crear Colaborador'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Editar Colaborador */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="text-brand-navy">Editar Colaborador</DialogTitle>
            <DialogDescription>
              Modifique los datos del colaborador.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Nombre Completo *
              </Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Teléfono
              </Label>
              <Input
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="rounded-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="is_active" className="text-sm">
                Colaborador activo
              </Label>
            </div>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setShowEditDialog(false)}
              className="flex-1 rounded-sm"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleEdit}
              disabled={actionLoading}
              className="flex-1 bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
            >
              {actionLoading ? 'Guardando...' : 'Guardar Cambios'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Alert Dialog: Eliminar Colaborador */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar colaborador?</AlertDialogTitle>
            <AlertDialogDescription>
              ¿Está seguro que desea eliminar a <strong>{selectedUser?.name}</strong>? 
              Esta acción desactivará el colaborador y no podrá acceder al sistema.
              Si tiene contratos activos, deberá finalizarlos primero.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              {actionLoading ? 'Eliminando...' : 'Eliminar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DashboardLayout>
  );
};
