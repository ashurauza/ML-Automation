import React, { useState, useRef } from 'react';
import {
  Container,
  Paper,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Grid,
  Fade
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ArchitectureIcon from '@mui/icons-material/Architecture';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import { estimationAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function UploadDrawing() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleFileChange = (selectedFiles) => {
    if (selectedFiles && selectedFiles.length > 0) {
      const validFiles = Array.from(selectedFiles).filter(file => file.type === 'application/pdf');
      
      if (validFiles.length > 0) {
        setFiles(validFiles);
        setError('');
      } else {
        setError('Invalid format. Please select valid PDF engineering drawings.');
        setFiles([]);
      }
    }
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setLoading(true);
    try {
      // In the estimationAPI.uploadDrawing, it needs to be updated to accept multiple files.
      // Assuming api.js uses FormData, we pass the array of files.
      const response = await estimationAPI.uploadDrawing(files);
      const estimationId = response.data.estimation_id || response.data.id;
      
      // Simulate a bit of processing time for the "scanning" animation effect
      setTimeout(() => {
        navigate(`/estimate/${estimationId}`);
      }, 1500);

    } catch (err) {
      setError(err.response?.data?.detail || 'Error processing the drawings. Please try again.');
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h3" sx={{ fontWeight: 800, mb: 2, background: 'linear-gradient(90deg, #60A5FA, #34D399)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          AI Cost Estimator
        </Typography>
        <Typography variant="h6" color="textSecondary" sx={{ fontWeight: 400, maxWidth: '600px', mx: 'auto' }}>
          Upload your engineering drawings and let our AI analyze geometry, materials, and operations to generate a highly accurate manufacturing cost.
        </Typography>
      </Box>

      <Fade in={true} timeout={800}>
        <Paper 
          className="glass-panel"
          sx={{ 
            p: { xs: 3, md: 6 }, 
            borderRadius: 4,
            transition: 'transform 0.3s ease',
            transform: isDragging ? 'scale(1.02)' : 'scale(1)',
            borderColor: isDragging ? 'primary.main' : 'rgba(255, 255, 255, 0.08)'
          }}
        >
          <Box 
            className={`blueprint-bg ${loading ? 'scanning' : ''}`}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => !loading && fileInputRef.current?.click()}
            sx={{
              border: '2px dashed',
              borderColor: isDragging ? 'primary.main' : 'rgba(148, 163, 184, 0.3)',
              borderRadius: 3,
              p: 6,
              textAlign: 'center',
              cursor: loading ? 'wait' : 'pointer',
              minHeight: '300px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}
          >
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={(e) => handleFileChange(e.target.files)}
              style={{ display: 'none' }}
              ref={fileInputRef}
            />

            {files.length === 0 && !loading && (
              <>
                <ArchitectureIcon sx={{ fontSize: 80, color: 'primary.light', mb: 3, opacity: 0.8 }} />
                <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                  Drag & Drop Blueprints
                </Typography>
                <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
                  or click to browse your folders (Upload multiple PDFs to quote as an Assembly)
                </Typography>
              </>
            )}

            {files.length > 0 && !loading && (
              <>
                <CheckCircleOutlineIcon sx={{ fontSize: 80, color: 'success.main', mb: 3 }} />
                <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                  Ready to Analyze Assembly
                </Typography>
                <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
                  {files.length} file(s) selected
                </Typography>
                <Button 
                  variant="contained" 
                  size="large"
                  color="primary"
                  onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                  sx={{ px: 6, py: 1.5, borderRadius: 8, fontSize: '1.1rem' }}
                >
                  Start Assembly Extraction
                </Button>
              </>
            )}

            {loading && (
              <>
                <CircularProgress size={60} thickness={4} sx={{ mb: 3, color: 'primary.light' }} />
                <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                  Extracting Features...
                </Typography>
                <Typography variant="body2" color="primary.light">
                  Running OpenCV structural analysis & OCR parameter detection
                </Typography>
              </>
            )}
          </Box>

          {error && (
            <Alert severity="error" sx={{ mt: 4, borderRadius: 2 }}>
              {error}
            </Alert>
          )}
        </Paper>
      </Fade>

      <Grid container spacing={4} sx={{ mt: 6, textAlign: 'center' }}>
        <Grid item xs={12} md={4}>
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ color: 'primary.light', mb: 1 }}>1. Extract</Typography>
            <Typography variant="body2" color="textSecondary">Automatically detects holes, slots, and contours via OpenCV.</Typography>
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ color: 'secondary.light', mb: 1 }}>2. Analyze</Typography>
            <Typography variant="body2" color="textSecondary">Extracts dimensions, materials, and tolerances using OCR.</Typography>
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ color: 'success.light', mb: 1 }}>3. Predict</Typography>
            <Typography variant="body2" color="textSecondary">Runs XGBoost models to predict manufacturing costs in INR.</Typography>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
}
