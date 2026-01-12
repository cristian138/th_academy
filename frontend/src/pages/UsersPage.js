import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { usersAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
import { Users, Mail, Shield, Plus, Pencil, Trash2, Phone, CreditCard } from 'lucide-react';
import { toast } from 'sonner';

const getRoleBadge = (role) => {
  const roleMap = {
    superadmin: { label: 'Superadmin', class: 'bg-purple-100 text-purple-700 border-purple-200' },
    admin: { label: 'Administrador', class: 'bg-brand-navy text-white border-brand-navy' },
    legal_rep: { label: 'Rep. Legal', class: 'bg-blue-100 text-blue-700 border-blue-200' },
    accountant: { label: 'Contador', class: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    collaborator: { label: 'Colaborador', class: 'bg-slate-100 text-slate-700 border-slate-200' }
  };
  const roleInfo = roleMap[role] || { label: role, class: 'bg-slate-100 text-slate-700' };
  return (
    <Badge className={`${roleInfo.class} px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border`}>
      {roleInfo.label}
    </Badge>
  );
};

const roleOptions = [
  { value: 'collaborator', label: 'Colaborador' },
  { value: 'accountant', label: 'Contador' },
  { value: 'admin', label: 'Administrador' },
  { value: 'legal_rep', label: 'Representante Legal' }
];

export const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    password: '',
    role: 'collaborator',
    phone: '',
    identification: ''
  });
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await usersAPI.list();
      setUsers(response.data);
    } catch (error) {
      console.error('Error loading users:', error);
      toast.error('Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      email: '',
      name: '',
      password: '',
      role: 'collaborator',
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
      await usersAPI.create(formData);
      toast.success('Usuario creado exitosamente');
      setShowCreateDialog(false);
      resetForm();
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear usuario');
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
      toast.success('Usuario actualizado exitosamente');
      setShowEditDialog(false);
      setSelectedUser(null);
      resetForm();
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar usuario');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    setActionLoading(true);
    try {
      await usersAPI.delete(selectedUser.id);
      toast.success('Usuario eliminado exitosamente');
      setShowDeleteDialog(false);
      setSelectedUser(null);
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar usuario');
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

  const groupedUsers = {
    admin: users.filter(u => ['superadmin', 'admin'].includes(u.role)),
    management: users.filter(u => ['legal_rep', 'accountant'].includes(u.role)),
    collaborators: users.filter(u => u.role === 'collaborator')
  };

  const UserCard = ({ user }) => (
    <Card
      className={`border rounded-sm transition-colors ${
        user.is_active 
          ? 'border-slate-200 hover:border-brand-blue/50' 
          : 'border-red-200 bg-red-50/30'
      }`}
      data-testid={`user-card-${user.id}`}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg font-bold text-brand-navy mb-1">
              {user.name}
            </CardTitle>
            {getRoleBadge(user.role)}
          </div>
          <div className="flex items-center gap-1">
            <div className={`w-2.5 h-2.5 rounded-full ${
              user.is_active ? 'bg-emerald-500' : 'bg-red-500'
            }`} title={user.is_active ? 'Activo' : 'Inactivo'}></div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <Mail size={14} strokeWidth={1.5} />
          <span className="truncate">{user.email}</span>
        </div>
        {user.phone && (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Phone size={14} strokeWidth={1.5} />
            <span>{user.phone}</span>
          </div>
        )}
        {user.identification && (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <CreditCard size={14} strokeWidth={1.5} />
            <span>CC: {user.identification}</span>
          </div>
        )}
        {user.role !== 'superadmin' && (
          <div className="flex gap-2 pt-2 border-t border-slate-100">
            <Button
              size="sm"
              variant="outline"
              onClick={() => openEditDialog(user)}
              className="flex-1 rounded-sm text-xs"
            >
              <Pencil size={14} className="mr-1" />
              Editar
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => openDeleteDialog(user)}
              className="rounded-sm text-xs text-red-600 border-red-200 hover:bg-red-50"
            >
              <Trash2 size={14} />
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-brand-navy mb-2">Usuarios</h1>
            <p className="text-slate-600">Gestione los usuarios del sistema</p>
          </div>
          <Button
            onClick={() => {
              resetForm();
              setShowCreateDialog(true);
            }}
            className="bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm"
            data-testid="create-user-btn"
          >
            <Plus size={18} className="mr-2" />
            Nuevo Usuario
          </Button>
        </div>

        <div className="space-y-6">
          {/* Administradores */}
          <div>
            <h2 className="text-xl font-bold text-brand-navy mb-4 flex items-center gap-2">
              <Shield size={20} />
              Administradores ({groupedUsers.admin.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groupedUsers.admin.map((user) => (
                <UserCard key={user.id} user={user} />
              ))}
            </div>
          </div>

          {/* Gestión */}
          {groupedUsers.management.length > 0 && (
            <div>
              <h2 className="text-xl font-bold text-brand-navy mb-4 flex items-center gap-2">
                <Users size={20} />
                Gestión ({groupedUsers.management.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {groupedUsers.management.map((user) => (
                  <UserCard key={user.id} user={user} />
                ))}
              </div>
            </div>
          )}

          {/* Colaboradores */}
          <div>
            <h2 className="text-xl font-bold text-brand-navy mb-4 flex items-center gap-2">
              <Users size={20} />
              Colaboradores ({groupedUsers.collaborators.length})
            </h2>
            {groupedUsers.collaborators.length === 0 ? (
              <Card className="border border-slate-200 rounded-sm">
                <CardContent className="py-8 text-center">
                  <Users size={40} className="mx-auto mb-3 text-slate-300" />
                  <p className="text-slate-500">No hay colaboradores registrados</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {groupedUsers.collaborators.map((user) => (
                  <UserCard key={user.id} user={user} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dialog: Crear Usuario */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-brand-navy">Nuevo Usuario</DialogTitle>
            <DialogDescription>
              Complete los datos para crear un nuevo usuario en el sistema.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
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
                  Rol *
                </Label>
                <Select
                  value={formData.role}
                  onValueChange={(value) => setFormData({...formData, role: value})}
                >
                  <SelectTrigger className="rounded-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {roleOptions.map((role) => (
                      <SelectItem key={role.value} value={role.value}>
                        {role.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Correo Electrónico *
              </Label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="usuario@ejemplo.com"
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase text-slate-500 font-bold">
                Contraseña *
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
              {actionLoading ? 'Creando...' : 'Crear Usuario'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Editar Usuario */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="text-brand-navy">Editar Usuario</DialogTitle>
            <DialogDescription>
              Modifique los datos del usuario.
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
                Usuario activo
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

      {/* Alert Dialog: Eliminar Usuario */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar usuario?</AlertDialogTitle>
            <AlertDialogDescription>
              ¿Está seguro que desea eliminar a <strong>{selectedUser?.name}</strong>? 
              Esta acción desactivará el usuario y no podrá acceder al sistema.
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
