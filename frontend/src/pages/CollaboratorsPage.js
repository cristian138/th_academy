import { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { usersAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users, Mail, Phone, FileText } from 'lucide-react';

export const CollaboratorsPage = () => {
  const [collaborators, setCollaborators] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCollaborators();
  }, []);

  const loadCollaborators = async () => {
    try {
      const response = await usersAPI.list('collaborator');
      setCollaborators(response.data);
    } catch (error) {
      console.error('Error loading collaborators:', error);
    } finally {
      setLoading(false);
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
          <h1 className="text-4xl font-bold text-brand-navy mb-2">Colaboradores</h1>
          <p className="text-slate-600">Gestione los colaboradores de la academia</p>
        </div>

        {collaborators.length === 0 ? (
          <Card className="border border-slate-200 rounded-sm">
            <CardContent className="py-12 text-center">
              <Users size={48} className="mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500">No hay colaboradores registrados</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {collaborators.map((collaborator) => (
              <Card
                key={collaborator.id}
                className="border border-slate-200 rounded-sm hover:border-brand-blue/50 transition-colors"
                data-testid={`collaborator-card-${collaborator.id}`}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg font-bold text-brand-navy mb-1">
                        {collaborator.name}
                      </CardTitle>
                      <Badge className="bg-brand-navy text-white px-2.5 py-0.5 rounded-full text-xs font-bold uppercase">
                        Colaborador
                      </Badge>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${
                      collaborator.is_active ? 'bg-emerald-500' : 'bg-slate-300'
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
                      <FileText size={16} strokeWidth={1.5} />
                      <span>CC: {collaborator.identification}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
