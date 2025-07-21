import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { useFormik } from 'formik';
import * as yup from 'yup';
import { useCreateProject } from '../../hooks/useProjects';
import { ProjectFormData } from '../../types';

const validationSchema = yup.object({
  name: yup.string().required('Project name is required'),
  description: yup.string(),
  vessel_info: yup.object({
    vessel_name: yup.string().required('Vessel name is required'),
    imo_number: yup.string(),
    vessel_type: yup.string(),
    flag_state: yup.string(),
  }),
  incident_info: yup.object({
    incident_date: yup.date().required('Incident date is required'),
    incident_type: yup.string().required('Incident type is required'),
    location: yup.string().required('Location is required'),
    severity: yup.string().oneOf(['minor', 'moderate', 'major', 'catastrophic']),
  }),
});

const NewProject: React.FC = () => {
  const navigate = useNavigate();
  const createProject = useCreateProject();

  const formik = useFormik<ProjectFormData>({
    initialValues: {
      name: '',
      description: '',
      vessel_info: {
        vessel_name: '',
        imo_number: '',
        vessel_type: '',
        flag_state: '',
      },
      incident_info: {
        incident_date: new Date().toISOString().split('T')[0],
        incident_type: '',
        location: '',
        severity: 'moderate',
        injuries: 0,
        fatalities: 0,
      },
    },
    validationSchema: validationSchema,
    onSubmit: async (values) => {
      const result = await createProject.mutateAsync(values);
      navigate(`/projects/${result.id}`);
    },
  });

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/projects')}
        >
          Back to Projects
        </Button>
        <Typography variant="h4">New Project</Typography>
      </Box>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={formik.handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Project Information
              </Typography>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="name"
                name="name"
                label="Project Name"
                value={formik.values.name}
                onChange={formik.handleChange}
                error={formik.touched.name && Boolean(formik.errors.name)}
                helperText={formik.touched.name && formik.errors.name}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                id="description"
                name="description"
                label="Description"
                value={formik.values.description}
                onChange={formik.handleChange}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Vessel Information
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                id="vessel_info.vessel_name"
                name="vessel_info.vessel_name"
                label="Vessel Name"
                value={formik.values.vessel_info.vessel_name}
                onChange={formik.handleChange}
                error={
                  formik.touched.vessel_info?.vessel_name &&
                  Boolean(formik.errors.vessel_info?.vessel_name)
                }
                helperText={
                  formik.touched.vessel_info?.vessel_name &&
                  formik.errors.vessel_info?.vessel_name
                }
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                id="vessel_info.imo_number"
                name="vessel_info.imo_number"
                label="IMO Number"
                value={formik.values.vessel_info.imo_number}
                onChange={formik.handleChange}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                id="vessel_info.vessel_type"
                name="vessel_info.vessel_type"
                label="Vessel Type"
                value={formik.values.vessel_info.vessel_type}
                onChange={formik.handleChange}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                id="vessel_info.flag_state"
                name="vessel_info.flag_state"
                label="Flag State"
                value={formik.values.vessel_info.flag_state}
                onChange={formik.handleChange}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Incident Information
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="date"
                id="incident_info.incident_date"
                name="incident_info.incident_date"
                label="Incident Date"
                value={formik.values.incident_info.incident_date}
                onChange={formik.handleChange}
                InputLabelProps={{ shrink: true }}
                error={
                  formik.touched.incident_info?.incident_date &&
                  Boolean(formik.errors.incident_info?.incident_date)
                }
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                id="incident_info.incident_type"
                name="incident_info.incident_type"
                label="Incident Type"
                value={formik.values.incident_info.incident_type}
                onChange={formik.handleChange}
                error={
                  formik.touched.incident_info?.incident_type &&
                  Boolean(formik.errors.incident_info?.incident_type)
                }
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                id="incident_info.location"
                name="incident_info.location"
                label="Location"
                value={formik.values.incident_info.location}
                onChange={formik.handleChange}
                error={
                  formik.touched.incident_info?.location &&
                  Boolean(formik.errors.incident_info?.location)
                }
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                id="incident_info.severity"
                name="incident_info.severity"
                label="Severity"
                value={formik.values.incident_info.severity}
                onChange={formik.handleChange}
                SelectProps={{ native: true }}
              >
                <option value="minor">Minor</option>
                <option value="moderate">Moderate</option>
                <option value="major">Major</option>
                <option value="catastrophic">Catastrophic</option>
              </TextField>
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                id="incident_info.injuries"
                name="incident_info.injuries"
                label="Injuries"
                value={formik.values.incident_info.injuries}
                onChange={formik.handleChange}
                InputProps={{ inputProps: { min: 0 } }}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                id="incident_info.fatalities"
                name="incident_info.fatalities"
                label="Fatalities"
                value={formik.values.incident_info.fatalities}
                onChange={formik.handleChange}
                InputProps={{ inputProps: { min: 0 } }}
              />
            </Grid>

            {createProject.isError && (
              <Grid item xs={12}>
                <Alert severity="error">
                  Failed to create project. Please try again.
                </Alert>
              </Grid>
            )}

            <Grid item xs={12}>
              <Box display="flex" gap={2} justifyContent="flex-end">
                <Button
                  onClick={() => navigate('/projects')}
                  disabled={createProject.isLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={createProject.isLoading || !formik.isValid}
                >
                  {createProject.isLoading ? 'Creating...' : 'Create Project'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
};

export default NewProject;