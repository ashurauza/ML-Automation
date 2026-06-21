import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useParams } from 'react-router-dom';
import { estimationAPI } from '../services/api';

export default function EstimationDetail() {
  const { estimationId } = useParams();
  const [estimation, setEstimation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchEstimation = async () => {
      try {
        const response = await estimationAPI.getEstimation(estimationId);
        setEstimation(response.data.estimation);
      } catch (err) {
        setError(err.response?.data?.detail || 'Error loading estimation');
      } finally {
        setLoading(false);
      }
    };
    fetchEstimation();
  }, [estimationId]);

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!estimation) {
    return <Typography>Estimation not found</Typography>;
  }

  // Ensure cost_breakdown exists with default values
  const costBreakdown = estimation.cost_breakdown || {
    raw_material_cost: 0,
    machining_cost: 0,
    manpower_cost: 0,
    overhead_cost: 0,
    logistics_cost: 0,
    subtotal: 0,
    total_cost: 0,
  };

  const costData = [
    { name: 'Raw Material', value: costBreakdown.raw_material_cost || 0 },
    { name: 'Machining', value: costBreakdown.machining_cost || 0 },
    { name: 'Manpower', value: costBreakdown.manpower_cost || 0 },
    { name: 'Overhead', value: costBreakdown.overhead_cost || 0 },
    { name: 'Logistics', value: costBreakdown.logistics_cost || 0 },
  ];

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Cost Estimation - {estimation.filename}
      </Typography>

      <Grid container spacing={3}>
        {/* Cost Summary */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Cost Summary
            </Typography>
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Raw Material Cost
                </Typography>
                <Typography variant="h6">
                  ${estimation.cost_breakdown.raw_material_cost.toFixed(2)}
                </Typography>
              </CardContent>
            </Card>

            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Machining Cost
                </Typography>
                <Typography variant="h6">
                  ${estimation.cost_breakdown.machining_cost.toFixed(2)}
                </Typography>
              </CardContent>
            </Card>

            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Cost
                </Typography>
                <Typography variant="h5" sx={{ color: 'primary.main', fontWeight: 'bold' }}>
                  ${estimation.cost_breakdown.total_cost.toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Paper>
        </Grid>

        {/* Cost Distribution Pie Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Cost Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={costData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: $${value.toFixed(2)}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {costData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Parameters */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Part Parameters
            </Typography>
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography color="textSecondary">Material Type</Typography>
                <Typography>{estimation.extracted_parameters.material_type}</Typography>
              </CardContent>
            </Card>

            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography color="textSecondary">Cycle Time</Typography>
                <Typography>{estimation.estimated_cycle_time.toFixed(2)} hours</Typography>
              </CardContent>
            </Card>
          </Paper>
        </Grid>

        {/* Operations */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Manufacturing Operations
            </Typography>
            {estimation.manufacturing_operations.map((op, idx) => (
              <Card key={idx} variant="outlined" sx={{ mb: 1 }}>
                <CardContent sx={{ py: 1 }}>
                  <Typography>{op}</Typography>
                </CardContent>
              </Card>
            ))}
          </Paper>
        </Grid>

        {/* Actions */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button variant="contained" color="primary">
              Export as PDF
            </Button>
            <Button variant="contained" color="secondary">
              Export as Excel
            </Button>
            <Button variant="outlined">
              Modify Parameters
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
}
