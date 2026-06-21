import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { estimationAPI } from '../services/api';

export default function UploadDrawing() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [estimationId, setEstimationId] = useState(null);
  const [extractedData, setExtractedData] = useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please select a PDF file');
        setFile(null);
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    try {
      const response = await estimationAPI.uploadDrawing(file);
      const estimation_id = response.data.estimation_id || response.data.id;
      setSuccess('Drawing uploaded successfully! Parameters extracted.');
      setEstimationId(estimation_id);
      setExtractedData(response.data.extracted_parameters || {});
      setFile(null);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading file');
      setSuccess('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Upload Engineering Drawing
      </Typography>

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <CloudUploadIcon sx={{ fontSize: 60, mb: 2, color: 'primary.main' }} />
            <Typography variant="h6" gutterBottom>
              Upload PDF Drawing
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Select an engineering drawing in PDF format
            </Typography>

            <Box component="form" onSubmit={handleUpload}>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                style={{ display: 'none' }}
                id="file-input"
              />
              <label htmlFor="file-input">
                <Button
                  variant="outlined"
                  component="span"
                  sx={{ mb: 2 }}
                >
                  Select File
                </Button>
              </label>

              {file && (
                <Typography variant="body2" sx={{ mb: 2 }}>
                  Selected: {file.name}
                </Typography>
              )}

              <Button
                type="submit"
                variant="contained"
                color="primary"
                fullWidth
                disabled={!file || loading}
                sx={{ mt: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Upload & Extract'}
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ mt: 2 }}>
                {success}
              </Alert>
            )}
          </Paper>
        </Grid>

        {/* Extracted Data Section */}
        {extractedData && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Extracted Parameters
              </Typography>
              
              <Card variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Extracted Information
                  </Typography>
                  {extractedData && extractedData.dimensions ? (
                    <>
                      <Typography variant="body2">
                        Length: {extractedData.dimensions.length} {extractedData.dimensions.unit || 'mm'}
                      </Typography>
                      <Typography variant="body2">
                        Material: {extractedData.material_type || 'Unknown'}
                      </Typography>
                    </>
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      Parameters extracted successfully
                    </Typography>
                  )}
                </CardContent>
              </Card>

              <Button
                variant="contained"
                color="success"
                fullWidth
                href={`/estimate/${estimationId}`}
              >
                Generate Cost Estimate
              </Button>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
}
