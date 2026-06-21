import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Container,
  Button,
  Box,
  Typography,
  CircularProgress
} from '@mui/material';
import ErrorBoundary from './components/ErrorBoundary';
import UploadDrawing from './pages/UploadDrawing';
import EstimationDetail from './pages/EstimationDetail';
import History from './pages/History';
import CostParameters from './pages/CostParameters'; // Re-used for settings dashboard
import Login from './pages/Login';
import Signup from './pages/Signup';
import { AuthProvider, AuthContext } from './context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

const Navigation = () => {
  const { user, logout } = useContext(AuthContext);
  return (
    <AppBar position="static">
      <Toolbar>
        <Box sx={{ flexGrow: 1 }}>
          <Link to="/" style={{ textDecoration: 'none', color: 'white' }}>
            <Button color="inherit" sx={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
              Cost Estimation System
            </Button>
          </Link>
        </Box>
        {user ? (
          <>
            <Link to="/" style={{ textDecoration: 'none' }}>
              <Button color="inherit">Upload</Button>
            </Link>
            <Link to="/history" style={{ textDecoration: 'none' }}>
              <Button color="inherit">History</Button>
            </Link>
            <Link to="/settings" style={{ textDecoration: 'none' }}>
              <Button color="inherit">Settings</Button>
            </Link>
            <Button color="inherit" onClick={logout} sx={{ ml: 2, border: '1px solid rgba(255,255,255,0.5)' }}>
              Logout
            </Button>
          </>
        ) : (
          <>
            <Link to="/login" style={{ textDecoration: 'none' }}>
              <Button color="inherit">Log In</Button>
            </Link>
            <Link to="/signup" style={{ textDecoration: 'none' }}>
              <Button color="inherit">Sign Up</Button>
            </Link>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Navigation />
          <Container maxWidth="lg" sx={{ mt: 4 }}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/" element={<ProtectedRoute><UploadDrawing /></ProtectedRoute>} />
              <Route path="/estimate/:estimationId" element={<ProtectedRoute><EstimationDetail /></ProtectedRoute>} />
              <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><CostParameters /></ProtectedRoute>} />
            </Routes>
          </Container>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
