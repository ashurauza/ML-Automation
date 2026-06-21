import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import { estimationAPI } from '../services/api';

export default function EstimationHistory() {
  const [estimations, setEstimations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await estimationAPI.getHistory();
        setEstimations(response.data.estimations);
      } catch (err) {
        setError(err.response?.data?.detail || 'Error loading history');
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Estimation History
      </Typography>

      {error && <Alert severity="error">{error}</Alert>}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell>Filename</TableCell>
              <TableCell>Material</TableCell>
              <TableCell align="right">Total Cost ($)</TableCell>
              <TableCell align="right">Cycle Time (hrs)</TableCell>
              <TableCell>Upload Date</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {estimations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography color="textSecondary">No estimations found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              estimations.map((est) => (
                <TableRow key={est.id}>
                  <TableCell>{est.filename}</TableCell>
                  <TableCell>{est.material_type || 'N/A'}</TableCell>
                  <TableCell align="right">
                    ${est.total_cost ? est.total_cost.toFixed(2) : 'N/A'}
                  </TableCell>
                  <TableCell align="right">
                    {est.estimated_cycle_time ? est.estimated_cycle_time.toFixed(2) : 'N/A'}
                  </TableCell>
                  <TableCell>{new Date(est.upload_date).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <Button
                      variant="outlined"
                      size="small"
                      href={`/estimate/${est.id}`}
                    >
                      View
                    </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {estimations.length === 0 && (
        <Typography sx={{ mt: 4, textAlign: 'center', color: 'textSecondary' }}>
          No estimations yet. Start by uploading a drawing!
        </Typography>
      )}
    </Container>
  );
}
