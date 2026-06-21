import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Container,
  Button,
  Box,
} from '@mui/material';
import ErrorBoundary from './components/ErrorBoundary';
import UploadDrawing from './pages/UploadDrawing';
import EstimationDetail from './pages/EstimationDetail';
import History from './pages/History';
import CostParameters from './pages/CostParameters';

function App() {
  return (
    <Router>
      <AppBar position="static">
        <Toolbar>
          <Box sx={{ flexGrow: 1 }}>
            <Link to="/" style={{ textDecoration: 'none', color: 'white' }}>
              <Button color="inherit" sx={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                Cost Estimation System
              </Button>
            </Link>
          </Box>
          <Link to="/" style={{ textDecoration: 'none' }}>
            <Button color="inherit">Upload</Button>
          </Link>
          <Link to="/history" style={{ textDecoration: 'none' }}>
            <Button color="inherit">History</Button>
          </Link>
          <Link to="/parameters" style={{ textDecoration: 'none' }}>
            <Button color="inherit">Parameters</Button>
          </Link>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Routes>
          <Route path="/" element={<UploadDrawing />} />
          <Route path="/estimate/:estimationId" element={<EstimationDetail />} />
          <Route path="/history" element={<History />} />
          <Route path="/parameters" element={<CostParameters />} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
