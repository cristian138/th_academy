import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children, requiredRole }) => {
  const { isAuthenticated, user, loading, hasRole } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-navy"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-brand-bg">
        <div className="text-center p-8 bg-white border border-slate-200 rounded-sm max-w-md">
          <div className="mb-4 p-4 bg-red-50 rounded-sm">
            <svg
              className="w-16 h-16 mx-auto text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-brand-navy mb-2">Acceso Denegado</h2>
          <p className="text-slate-600 mb-4">No tiene permisos suficientes para acceder a esta página.</p>
          <p className="text-sm text-slate-500 mb-6">Rol requerido: {requiredRole}</p>
          <a
            href="/dashboard"
            className="inline-block bg-brand-navy hover:bg-brand-navy/90 text-white px-6 py-2 rounded-sm font-medium text-sm uppercase tracking-wide transition-colors"
          >
            Volver al Dashboard
          </a>
        </div>
      </div>
    );
  }

  return children;
};
