import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login({ email, password });
      login(response.data.access_token, response.data.user);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div
        className="hidden lg:flex lg:w-1/2 bg-cover bg-center relative"
        style={{
          backgroundImage: 'url(https://images.unsplash.com/photo-1761449779811-33f7c48ed367?crop=entropy&cs=srgb&fm=jpg&q=85)'
        }}
      >
        <div className="absolute inset-0 bg-brand-navy/90"></div>
        <div className="relative z-10 p-12 flex flex-col justify-center text-white">
          <div className="mb-8">
            <img 
              src="https://customer-assets.emergentagent.com/job_coach-contracts/artifacts/mw84sg36_ICONO-NEGATIVO--SIN-FONDO.png" 
              alt="Jotuns Club Logo" 
              className="w-32 h-32 object-contain mb-4"
            />
          </div>
          <h1 className="text-5xl font-bold mb-4">Academia Jotuns Club SAS</h1>
          <p className="text-xl text-white/80">Sistema de Gestión de Talento Humano</p>
          <p className="mt-4 text-white/60">Administre contratos, documentos y pagos de colaboradores</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-brand-navy">Iniciar Sesión</h2>
            <p className="mt-2 text-slate-600">Acceda a su cuenta</p>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-xs uppercase text-slate-500 font-bold">
                Correo Electrónico
              </Label>
              <Input
                id="email"
                data-testid="email-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-10 rounded-sm border-slate-300 focus-visible:ring-brand-navy"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-xs uppercase text-slate-500 font-bold">
                Contraseña
              </Label>
              <Input
                id="password"
                data-testid="password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-10 rounded-sm border-slate-300 focus-visible:ring-brand-navy"
              />
            </div>

            <Button
              type="submit"
              data-testid="login-button"
              disabled={loading}
              className="w-full bg-brand-navy hover:bg-brand-navy/90 text-white rounded-sm font-medium px-6 py-2.5 uppercase tracking-wide text-xs"
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>
          </form>

          <div className="mt-6 p-4 bg-slate-50 rounded-sm border border-slate-200">
            <p className="text-xs uppercase text-slate-500 font-bold mb-2">Usuarios de Prueba</p>
            <div className="space-y-1 text-xs text-slate-600">
              <p>Admin: admin@sportsadmin.com / admin123</p>
              <p>Legal: legal@sportsadmin.com / legal123</p>
              <p>Contador: contador@sportsadmin.com / contador123</p>
              <p>Colaborador: carlos.rodriguez@coach.com / carlos123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
