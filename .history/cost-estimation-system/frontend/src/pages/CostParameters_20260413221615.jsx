import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  CircularProgress,
  Alert,
  Box,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { parametersAPI } from '../services/api';

export default function CostParameters() {
  const [parameters, setParameters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingParam, setEditingParam] = useState(null);
  const [formData, setFormData] = useState({
    parameter_name: '',
    parameter_value: '',
    description: '',
  });

  useEffect(() => {
    fetchParameters();
  }, []);

  const fetchParameters = async () => {
    try {
      const response = await parametersAPI.getAll();
      setParameters(response.data.parameters);
    } catch (err) {
      setError('Error loading parameters');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (param = null) => {
    if (param) {
      setEditingParam(param.parameter_name);
      setFormData({
        parameter_name: param.parameter_name,
        parameter_value: param.parameter_value.toString(),
        description: param.description || '',
      });
    } else {
      setEditingParam(null);
      setFormData({
        parameter_name: '',
        parameter_value: '',
        description: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleSubmit = async () => {
    try {
      if (editingParam) {
        await parametersAPI.update(editingParam, {
          parameter_name: formData.parameter_name,
          parameter_value: parseFloat(formData.parameter_value),
          description: formData.description,
        });
        setSuccess('Parameter updated successfully');
      } else {
        await parametersAPI.create({
          parameter_name: formData.parameter_name,
          parameter_value: parseFloat(formData.parameter_value),
          description: formData.description,
        });
        setSuccess('Parameter created successfully');
      }
      setOpenDialog(false);
      fetchParameters();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving parameter');
    }
  };

  const handleDelete = async (paramName) => {
    if (window.confirm(`Delete parameter "${paramName}"?`)) {
      try {
        await parametersAPI.delete(paramName);
        setSuccess('Parameter deleted successfully');
        fetchParameters();
      } catch (err) {
        setError('Error deleting parameter');
      }
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
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4">
          Cost Parameters
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => handleOpenDialog()}
        >
          Add Parameter
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell>Parameter Name</TableCell>
              <TableCell align="right">Value</TableCell>
              <TableCell>Description</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {parameters.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                  <Typography color="textSecondary">
                    No parameters configured. Click "Add Parameter" to create one.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              parameters.map((param) => (
                <TableRow key={param.id || param.parameter_name}>
                  <TableCell>{param.parameter_name || 'N/A'}</TableCell>
                  <TableCell align="right">{param.parameter_value || 'N/A'}</TableCell>
                  <TableCell>{param.description || '-'}</TableCell>
                  <TableCell align="center">
                    <Button
                      size="small"
                      startIcon={<EditIcon />}
                      onClick={() => handleOpenDialog(param)}
                      disabled={param.is_editable === false}
                    >
                      Edit
                    </Button>
                    <Button
                      size="small"
                      startIcon={<DeleteIcon />}
                      color="error"
                      onClick={() => handleDelete(param.parameter_name)}
                      disabled={param.is_editable === false}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit/Create Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingParam ? 'Edit Parameter' : 'Add New Parameter'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Parameter Name"
              value={formData.parameter_name}
              onChange={(e) => setFormData({ ...formData, parameter_name: e.target.value })}
              disabled={!!editingParam}
            />
            <TextField
              label="Value"
              type="number"
              value={formData.parameter_value}
              onChange={(e) => setFormData({ ...formData, parameter_value: e.target.value })}
            />
            <TextField
              label="Description"
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
