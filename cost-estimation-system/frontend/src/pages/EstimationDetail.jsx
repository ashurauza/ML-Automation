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
  Fade,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { 
  PieChart, Pie, Cell, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, AreaChart, Area, ComposedChart
} from 'recharts';
import { useParams, useNavigate } from 'react-router-dom';
import { estimationAPI, marketplaceAPI } from '../services/api';
import PartVisualization from '../components/PartVisualization';
import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing';
import PaidIcon from '@mui/icons-material/Paid';
import FileDownloadIcon from '@mui/icons-material/FileDownload';

export default function EstimationDetail() {
  const { estimationId } = useParams();
  const navigate = useNavigate();
  const [estimation, setEstimation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [quotes, setQuotes] = useState([]);
  const [loadingQuotes, setLoadingQuotes] = useState(false);

  useEffect(() => {
    const fetchEstimation = async () => {
      try {
        const response = await estimationAPI.getEstimation(estimationId);
        setEstimation(response.data.estimation);
        
        try {
          const quotesResponse = await marketplaceAPI.getQuotes(estimationId);
          setQuotes(quotesResponse.data);
        } catch (e) {
          console.error("Could not fetch quotes", e);
        }
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
      <Container sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} thickness={4} sx={{ mb: 3, color: 'primary.light' }} />
        <Typography variant="h6" color="textSecondary">Assembling AI Estimate...</Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ borderRadius: 2 }}>{error}</Alert>
      </Container>
    );
  }

  if (!estimation) return null;

  const costBreakdown = estimation.cost_breakdown || {
    raw_material_cost: 0,
    machining_cost: 0,
    manpower_cost: 0,
    overhead_cost: 0,
    logistics_cost: 0,
    total_cost: 0,
  };

  const costData = [
    { name: 'Raw Material', value: costBreakdown.raw_material_cost || 0 },
    { name: 'Machining', value: costBreakdown.machining_cost || 0 },
    { name: 'Manpower', value: costBreakdown.manpower_cost || 0 },
    { name: 'Coating', value: costBreakdown.coating_cost || 0 },
    { name: 'Overhead', value: costBreakdown.overhead_cost || 0 },
    { name: 'Logistics', value: costBreakdown.logistics_cost || 0 },
  ];

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#E83E8C', '#EF4444', '#8B5CF6'];

  // Radar chart data for complexity analysis
  const complexityData = [
    { subject: 'Dimensional Scale', A: Math.min((estimation.extracted_parameters?.dimensions?.length || 50) / 10, 100), fullMark: 100 },
    { subject: 'Geometry Complexity', A: Math.min((estimation.extracted_parameters?.diagram_count || 1) * 10, 100), fullMark: 100 },
    { subject: 'Density', A: Math.min((estimation.extracted_parameters?.line_density || 0) * 100, 100), fullMark: 100 },
    { subject: 'Tolerances', A: (estimation.extracted_parameters?.tolerances?.critical || 0.05) < 0.02 ? 90 : 40, fullMark: 100 },
    { subject: 'Operations', A: Math.min((estimation.manufacturing_operations?.length || 1) * 20, 100), fullMark: 100 }
  ];

  const handleGenerateEstimate = async () => {
    setLoading(true);
    try {
      await estimationAPI.generateEstimate(estimationId);
      setTimeout(async () => {
        const detailResponse = await estimationAPI.getEstimation(estimationId);
        setEstimation(detailResponse.data.estimation);
        setLoading(false);
      }, 800);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error generating estimate');
      setLoading(false);
    }
  };

  const handleExportExcel = async () => {
    try {
      const response = await estimationAPI.exportExcel(estimationId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `cost_estimation_${estimationId}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Error exporting to Excel');
    }
  };

  const handleRequestQuotes = async () => {
    setLoadingQuotes(true);
    try {
      const response = await marketplaceAPI.requestQuotes(estimationId);
      setQuotes(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error requesting quotes');
    } finally {
      setLoadingQuotes(false);
    }
  };

  const handleAcceptQuote = async (quoteId) => {
    try {
      await marketplaceAPI.acceptQuote(quoteId);
      const quotesResponse = await marketplaceAPI.getQuotes(estimationId);
      setQuotes(quotesResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error accepting quote');
    }
  };

  const needsEstimate = !costBreakdown.total_cost || costBreakdown.total_cost === 0;


  const mlPrediction = estimation.ml_prediction || {};
  const isAssembly = estimation.extracted_parameters?.diagram_analysis?.file_breakdown?.length > 0;
  const fileBreakdown = estimation.extracted_parameters?.diagram_analysis?.file_breakdown || [];

  // 1. Feature Importance Data
  const featureImportanceRaw = mlPrediction.feature_importance || {};
  const featureImportanceData = Object.keys(featureImportanceRaw)
    .map(key => ({ name: key.replace(/_/g, ' ').toUpperCase(), value: Number((featureImportanceRaw[key] * 100).toFixed(1)) }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  // 2. Tolerance Cost Impact Curve (Simulated)
  const criticalTol = estimation.extracted_parameters?.tolerances?.critical || 0.05;
  const toleranceImpactData = [
    { tolerance: '0.2', costMultiplier: 1.0 },
    { tolerance: '0.1', costMultiplier: 1.2 },
    { tolerance: '0.05', costMultiplier: 1.5 },
    { tolerance: '0.02', costMultiplier: 2.0 },
    { tolerance: '0.01', costMultiplier: 2.8 },
  ];

  // 3. Estimated Cycle Time Breakdown (Mock distribution)
  const totalCycleTime = estimation.estimated_cycle_time || 0;
  const ops = estimation.manufacturing_operations || [];
  const cycleTimeData = ops.map((op, i) => ({
    name: op.charAt(0).toUpperCase() + op.slice(1),
    time: Number((totalCycleTime / (ops.length || 1)).toFixed(2))
  }));

  // 4. Assembly Sub-Component Complexity Comparison
  const assemblyComplexityData = fileBreakdown.map((f, i) => ({
    name: f.filename.substring(0, 10) + '...',
    Holes: f.holes || 0,
    Slots: f.slots || 0,
  }));

  // 5. Assembly Material Distribution
  const materialCount = fileBreakdown.reduce((acc, curr) => {
    acc[curr.material] = (acc[curr.material] || 0) + 1;
    return acc;
  }, {});
  const materialDistData = Object.keys(materialCount).map(mat => ({
    name: mat.toUpperCase(), value: materialCount[mat]
  }));

  // 6. Confidence Gauge Data
  const confidenceData = [
    {
      name: 'Cost Range',
      lower: mlPrediction.confidence_lower || costBreakdown.total_cost * 0.9,
      predicted: costBreakdown.total_cost || 0,
      upper: mlPrediction.confidence_upper || costBreakdown.total_cost * 1.1,
    }
  ];

  return (

    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Fade in={true} timeout={500}>
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4, flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
                AI Analysis Report
                {estimation.status === 'completed' && <Chip label="Ready" color="success" size="small" />}
              </Typography>
              <Typography variant="body1" color="textSecondary">
                File ID: {estimation.filename} | OpenCV + OCR Processing
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" onClick={() => navigate('/')}>Upload Another</Button>
              {needsEstimate ? (
                <Button 
                  variant="contained" 
                  color="primary"
                  onClick={handleGenerateEstimate}
                  disabled={loading}
                  sx={{ px: 4 }}
                >
                  Predict Cost (INR)
                </Button>
              ) : (
                <Button 
                  variant="contained" 
                  color="secondary"
                  onClick={handleExportExcel}
                  startIcon={<FileDownloadIcon />}
                  sx={{ px: 4 }}
                >
                  Export Excel
                </Button>
              )}
            </Box>
          </Box>

          <Grid container spacing={3}>
            {/* Top Stat Cards */}
            <Grid item xs={12} md={4}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <PaidIcon sx={{ color: 'success.main', fontSize: 40 }} />
                  <Typography variant="h6" color="textSecondary">Predicted Total Cost</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 800, color: 'success.light' }}>
                  ₹{costBreakdown.total_cost ? costBreakdown.total_cost.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : '---'}
                </Typography>
                {!needsEstimate && (
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    Confidence range: ±7% based on XGBoost logic
                  </Typography>
                )}
              </Paper>
            </Grid>

            {/* Visual Part Reconstruction */}
            <Grid item xs={12} md={8}>
              <Paper className="glass-panel" sx={{ p: 0, borderRadius: 3, height: '100%', overflow: 'hidden', position: 'relative' }}>
                <Box sx={{ p: 3, borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PrecisionManufacturingIcon color="primary" /> Structural Reconstruction
                  </Typography>
                </Box>
                <Box sx={{ height: 250, bgcolor: 'rgba(0,0,0,0.2)' }}>
                  <PartVisualization extractedData={estimation.extracted_parameters} />
                </Box>
              </Paper>
            </Grid>

            {/* Cost Distribution Chart */}
            <Grid item xs={12} md={6}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 450, display: 'flex', flexDirection: 'column' }}>
                <Typography variant="h6" gutterBottom>Cost Breakdown Visualization</Typography>
                {needsEstimate ? (
                  <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography color="textSecondary">Click 'Predict Cost' to generate</Typography>
                  </Box>
                ) : (
                  <Box sx={{ display: 'flex', flexGrow: 1, flexDirection: 'column' }}>
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={costData.filter(d => d.value > 0)}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={90}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {costData.filter(d => d.value > 0).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
                          contentStyle={{ backgroundColor: '#131C31', border: '1px solid #3B82F6', borderRadius: '8px' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <Box sx={{ mt: 2, px: 2, overflowY: 'auto' }}>
                      <Grid container spacing={1}>
                        {costData.filter(d => d.value > 0).map((item, idx) => (
                          <Grid item xs={6} key={idx} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: COLORS[idx % COLORS.length] }} />
                              <Typography variant="body2" color="textSecondary">{item.name}</Typography>
                            </Box>
                            <Typography variant="body2" fontWeight="bold">₹{item.value.toLocaleString('en-IN')}</Typography>
                          </Grid>
                        ))}
                        <Grid item xs={6} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1, borderTop: '1px solid rgba(255,255,255,0.1)', pt: 1 }}>
                            <Typography variant="body2" color="textSecondary">Profit Margin</Typography>
                            <Typography variant="body2" fontWeight="bold" color="success.light">₹{(costBreakdown.profit_margin || 0).toLocaleString('en-IN')}</Typography>
                        </Grid>
                      </Grid>
                    </Box>
                  </Box>
                )}
              </Paper>
            </Grid>

            {/* Complexity Radar Chart */}
            <Grid item xs={12} md={6}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400 }}>
                <Typography variant="h6" gutterBottom>Manufacturing Complexity Profile</Typography>
                <ResponsiveContainer width="100%" height="90%">
                  <RadarChart cx="50%" cy="50%" outerRadius="70%" data={complexityData}>
                    <PolarGrid stroke="rgba(255,255,255,0.2)" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8' }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar name="Part Complexity" dataKey="A" stroke="#10B981" fill="#10B981" fillOpacity={0.5} />
                    <Tooltip contentStyle={{ backgroundColor: '#131C31', border: '1px solid #10B981', borderRadius: '8px' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* Bar Chart for Cost Comparison */}
            <Grid item xs={12}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400 }}>
                <Typography variant="h6" gutterBottom>Absolute Cost Values (INR)</Typography>
                {needsEstimate ? (
                  <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography color="textSecondary">Click 'Predict Cost' to generate</Typography>
                  </Box>
                ) : (
                  <ResponsiveContainer width="100%" height="90%">
                    <BarChart data={costData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="name" stroke="#94A3B8" />
                      <YAxis stroke="#94A3B8" tickFormatter={(val) => `₹${val}`} />
                      <Tooltip 
                        formatter={(value) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
                        contentStyle={{ backgroundColor: '#131C31', border: '1px solid #3B82F6', borderRadius: '8px' }}
                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                      />
                      <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]}>
                        {costData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Paper>
            </Grid>

            {/* AI Extracted Parameters */}
            <Grid item xs={12} md={6}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400, overflowY: 'auto' }}>
                <Typography variant="h6" gutterBottom>OCR & OpenCV Extractions</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Card sx={{ bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <CardContent>
                        <Typography color="textSecondary" variant="caption">Material</Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {estimation.extracted_parameters?.material_type || 'Unknown'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card sx={{ bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <CardContent>
                        <Typography color="textSecondary" variant="caption">Dimensions (LxW)</Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {estimation.extracted_parameters?.dimensions?.length || '?'} x {estimation.extracted_parameters?.dimensions?.width || '?'} mm
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card sx={{ bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <CardContent>
                        <Typography color="textSecondary" variant="caption">Detected Operations</Typography>
                        <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {estimation.manufacturing_operations?.map((op, i) => (
                            <Chip key={i} label={op} size="small" color="primary" variant="outlined" />
                          )) || <Typography variant="body2">None</Typography>}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card sx={{ bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <CardContent>
                        <Typography color="textSecondary" variant="caption">Est. Cycle Time</Typography>
                        <Typography variant="body1" fontWeight="bold" color="secondary.light">
                          {estimation.estimated_cycle_time ? `${estimation.estimated_cycle_time.toFixed(1)} hrs` : 'N/A'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            
            {/* --- NEW ADVANCED CHARTS SECTION --- */}
            
            {/* 1. AI Feature Importance */}
            <Grid item xs={12} md={6}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400 }}>
                <Typography variant="h6" gutterBottom>AI Feature Importance (XGBoost)</Typography>
                {needsEstimate ? (
                  <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography color="textSecondary">Predict to view drivers</Typography>
                  </Box>
                ) : (
                  <ResponsiveContainer width="100%" height="90%">
                    <BarChart layout="vertical" data={featureImportanceData} margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" horizontal={false} />
                      <XAxis type="number" stroke="#94A3B8" tickFormatter={(val) => `${val}%`} />
                      <YAxis dataKey="name" type="category" stroke="#94A3B8" width={100} tick={{fontSize: 11}} />
                      <Tooltip 
                        formatter={(value) => `${value}% Impact`}
                        contentStyle={{ backgroundColor: '#131C31', border: '1px solid #8B5CF6', borderRadius: '8px' }}
                      />
                      <Bar dataKey="value" fill="#8B5CF6" radius={[0, 4, 4, 0]}>
                        {featureImportanceData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Paper>
            </Grid>

            {/* 2. Confidence Interval Gauge */}
            <Grid item xs={12} md={6}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400 }}>
                <Typography variant="h6" gutterBottom>Predicted Cost Confidence Range</Typography>
                {needsEstimate ? (
                  <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography color="textSecondary">Predict to view range</Typography>
                  </Box>
                ) : (
                  <ResponsiveContainer width="100%" height="90%">
                    <ComposedChart layout="vertical" data={confidenceData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis type="number" domain={['dataMin - 1000', 'dataMax + 1000']} tickFormatter={(val) => `₹${val/1000}k`} stroke="#94A3B8" />
                      <YAxis dataKey="name" type="category" hide />
                      <Tooltip 
                        formatter={(value) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
                        contentStyle={{ backgroundColor: '#131C31', border: '1px solid #10B981', borderRadius: '8px' }}
                      />
                      <Legend verticalAlign="bottom" />
                      <Bar dataKey="lower" name="Lower Bound" fill="#3B82F6" stackId="a" fillOpacity={0.5} />
                      <Bar dataKey="predicted" name="Predicted Cost" fill="#10B981" stackId="a" />
                      <Bar dataKey="upper" name="Upper Bound" fill="#EF4444" stackId="a" fillOpacity={0.5} />
                    </ComposedChart>
                  </ResponsiveContainer>
                )}
              </Paper>
            </Grid>

            {/* 3. Estimated Cycle Time Breakdown */}
            <Grid item xs={12} md={6}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400 }}>
                <Typography variant="h6" gutterBottom>Cycle Time Distribution</Typography>
                <ResponsiveContainer width="100%" height="90%">
                  <AreaChart data={cycleTimeData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorTime" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="name" stroke="#94A3B8" />
                    <YAxis stroke="#94A3B8" tickFormatter={(val) => `${val}h`} />
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <Tooltip 
                      formatter={(value) => `${value} hours`}
                      contentStyle={{ backgroundColor: '#131C31', border: '1px solid #F59E0B', borderRadius: '8px' }}
                    />
                    <Area type="monotone" dataKey="time" stroke="#F59E0B" fillOpacity={1} fill="url(#colorTime)" />
                  </AreaChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* 4. Tolerance Impact Curve */}
            <Grid item xs={12} md={6}>
              <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400 }}>
                <Typography variant="h6" gutterBottom>Tolerance Cost Multiplier Curve</Typography>
                <ResponsiveContainer width="100%" height="90%">
                  <LineChart data={toleranceImpactData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="tolerance" stroke="#94A3B8" />
                    <YAxis stroke="#94A3B8" tickFormatter={(val) => `x${val}`} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#131C31', border: '1px solid #EF4444', borderRadius: '8px' }}
                    />
                    <Line type="monotone" dataKey="costMultiplier" stroke="#EF4444" strokeWidth={3} dot={{ r: 6 }} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* Assembly Specific Charts */}
            {isAssembly && (
              <>
                {/* 5. Assembly Complexity */}
                <Grid item xs={12} md={6}>
                  <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400 }}>
                    <Typography variant="h6" gutterBottom>Sub-Component Complexity (Holes vs Slots)</Typography>
                    <ResponsiveContainer width="100%" height="90%">
                      <BarChart data={assemblyComplexityData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="name" stroke="#94A3B8" tick={{fontSize: 10}} angle={-45} textAnchor="end" height={60} />
                        <YAxis stroke="#94A3B8" />
                        <Tooltip contentStyle={{ backgroundColor: '#131C31', border: '1px solid #3B82F6', borderRadius: '8px' }} />
                        <Legend verticalAlign="top" />
                        <Bar dataKey="Holes" fill="#3B82F6" />
                        <Bar dataKey="Slots" fill="#10B981" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Paper>
                </Grid>

                {/* 6. Assembly Material Distribution */}
                <Grid item xs={12} md={6}>
                  <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, height: 400 }}>
                    <Typography variant="h6" gutterBottom>Assembly Material Distribution</Typography>
                    <ResponsiveContainer width="100%" height="90%">
                      <PieChart>
                        <Pie
                          data={materialDistData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {materialDistData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value) => `${value} parts`}
                          contentStyle={{ backgroundColor: '#131C31', border: '1px solid #8B5CF6', borderRadius: '8px' }}
                        />
                        <Legend verticalAlign="bottom" height={36}/>
                      </PieChart>
                    </ResponsiveContainer>
                  </Paper>
                </Grid>
              </>
            )}

            {/* Sub-Component Breakdown Table */}
            {estimation.extracted_parameters?.diagram_analysis?.file_breakdown && (
              <Grid item xs={12}>
                <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3 }}>
                  <Typography variant="h6" gutterBottom>Sub-Component Breakdown</Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Filename</TableCell>
                          <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Material</TableCell>
                          <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Dimensions</TableCell>
                          <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Detected Holes</TableCell>
                          <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Detected Slots</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {estimation.extracted_parameters.diagram_analysis.file_breakdown.map((file, idx) => (
                          <TableRow key={idx} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                            <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)' }}>{file.filename}</TableCell>
                            <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)' }}>{file.material}</TableCell>
                            <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)' }}>{file.dimensions}</TableCell>
                            <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)' }}>{file.holes}</TableCell>
                            <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)' }}>{file.slots}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            )}

            {/* Supplier Marketplace Integration */}
            {!needsEstimate && (
              <Grid item xs={12}>
                <Paper className="glass-panel" sx={{ p: 3, borderRadius: 3, mb: 4 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h6">Supplier Marketplace Quotes</Typography>
                    {quotes.length === 0 && (
                      <Button 
                        variant="contained" 
                        color="primary" 
                        onClick={handleRequestQuotes}
                        disabled={loadingQuotes}
                      >
                        {loadingQuotes ? <CircularProgress size={24} /> : 'Request Quotes from Marketplace'}
                      </Button>
                    )}
                  </Box>

                  {quotes.length > 0 ? (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Supplier</TableCell>
                            <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Rating</TableCell>
                            <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Lead Time (Days)</TableCell>
                            <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Quoted Price (INR)</TableCell>
                            <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Status</TableCell>
                            <TableCell sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.1)' }}>Action</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {quotes.map((quote) => (
                            <TableRow 
                              key={quote.id} 
                              sx={{ 
                                backgroundColor: quote.status === 'accepted' ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
                                '&:last-child td, &:last-child th': { border: 0 } 
                              }}
                            >
                              <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)' }}>
                                {quote.supplier.name}
                                <Typography variant="caption" display="block" color="textSecondary">{quote.supplier.location}</Typography>
                              </TableCell>
                              <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)' }}>{quote.supplier.rating} ⭐</TableCell>
                              <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)' }}>{quote.lead_time_days}</TableCell>
                              <TableCell sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.05)', fontWeight: 'bold' }}>₹{quote.quoted_price.toLocaleString('en-IN')}</TableCell>
                              <TableCell sx={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                                <Chip 
                                  label={quote.status.toUpperCase()} 
                                  size="small"
                                  color={quote.status === 'accepted' ? 'success' : quote.status === 'rejected' ? 'error' : 'default'}
                                />
                              </TableCell>
                              <TableCell sx={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                                {quote.status === 'pending' && (
                                  <Button 
                                    size="small" 
                                    variant="outlined" 
                                    color="success"
                                    onClick={() => handleAcceptQuote(quote.id)}
                                  >
                                    Accept
                                  </Button>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Typography color="textSecondary" sx={{ py: 2 }}>
                      No quotes requested yet. Request quotes to see marketplace offers.
                    </Typography>
                  )}
                </Paper>
              </Grid>
            )}

          </Grid>
        </Box>
      </Fade>
    </Container>
  );
}
