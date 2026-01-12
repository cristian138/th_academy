import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ContractsPage } from './pages/ContractsPage';
import { ContractDetailPage } from './pages/ContractDetailPage';
import { NewContractPage } from './pages/NewContractPage';
import { CollaboratorsPage } from './pages/CollaboratorsPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { PaymentsPage } from './pages/PaymentsPage';
import { ReportsPage } from './pages/ReportsPage';
import { UsersPage } from './pages/UsersPage';
import { Toaster } from '@/components/ui/sonner';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/contracts"
            element={
              <ProtectedRoute>
                <ContractsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/contracts/new"
            element={
              <ProtectedRoute requiredRole="legal_rep">
                <NewContractPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/contracts/:id"
            element={
              <ProtectedRoute>
                <ContractDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/collaborators"
            element={
              <ProtectedRoute requiredRole="admin">
                <CollaboratorsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <DocumentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/payments"
            element={
              <ProtectedRoute>
                <PaymentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute requiredRole="accountant">
                <ReportsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute requiredRole="admin">
                <UsersPage />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </AuthProvider>
  );
}

export default App;
