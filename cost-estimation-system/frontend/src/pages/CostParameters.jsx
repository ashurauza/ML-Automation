import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Alert,
  Box,
  Grid,
  InputAdornment,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import { parametersAPI } from '../services/api';

export default function CostParameters() {
  const [settings, setSettings] = useState({
    material_cost_multiplier: 1.2,
    machining_rate: 50.0,
    labor_rate: 25.0,
    overhead_percentage: 15.0,
    profit_margin: 20.0,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await parametersAPI.getSettings();
      setSettings(response.data);
    } catch (err) {
      setError('Error loading shop-floor settings');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: parseFloat(value) || 0
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      await parametersAPI.updateSettings(settings);
      setSuccess('Shop-floor rates updated successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Shop-Floor Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Tune the ML model's estimation parameters to match your specific factory's rates and margins.
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}

      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={4}>
            
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Material Cost Multiplier
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Factor applied to raw material base cost to account for waste, scrap, and purchasing overhead.
              </Typography>
              <TextField
                fullWidth
                name="material_cost_multiplier"
                type="number"
                inputProps={{ step: "0.1", min: "1" }}
                value={settings.material_cost_multiplier}
                onChange={handleChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">x</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Machining Rate
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Average cost per hour for machine time (spindle running time, tool wear, power).
              </Typography>
              <TextField
                fullWidth
                name="machining_rate"
                type="number"
                inputProps={{ step: "1", min: "0" }}
                value={settings.machining_rate}
                onChange={handleChange}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  endAdornment: <InputAdornment position="end">/ hr</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Labor Rate
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Average hourly wage for operators, including benefits and direct supervisor overhead.
              </Typography>
              <TextField
                fullWidth
                name="labor_rate"
                type="number"
                inputProps={{ step: "1", min: "0" }}
                value={settings.labor_rate}
                onChange={handleChange}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  endAdornment: <InputAdornment position="end">/ hr</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Overhead Percentage
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                General factory overhead (rent, utilities, administration) added as a % of manufacturing cost.
              </Typography>
              <TextField
                fullWidth
                name="overhead_percentage"
                type="number"
                inputProps={{ step: "1", min: "0", max: "100" }}
                value={settings.overhead_percentage}
                onChange={handleChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Profit Margin
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Target profit margin applied to the total cost to calculate the final quoted price.
              </Typography>
              <TextField
                fullWidth
                name="profit_margin"
                type="number"
                inputProps={{ step: "1", min: "0", max: "100" }}
                value={settings.profit_margin}
                onChange={handleChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  size="large"
                  disabled={saving}
                  startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                >
                  {saving ? 'Saving...' : 'Save Settings'}
                </Button>
              </Box>
            </Grid>

          </Grid>
        </form>
      </Paper>
    </Container>
  );
}
