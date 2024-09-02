import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ViewPredictionResult from './ViewPredictionResult';
import { ClimateDataDetails, PredictionsResponse } from '../utils/types';
import { Alert, Box, CircularProgress, MenuItem, Paper, Select, SelectChangeEvent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material';
import { Line } from 'react-chartjs-2';
import { useSearchParams } from 'react-router-dom';


const PredictionPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const cropName = searchParams.get('cropName');
    const locationId = searchParams.get('locationId');
    
    const [predictions, setPredictions] = useState<PredictionsResponse | null>(null);
    const [selectedForecast, setSelectedForecast] = useState<string>('temperature2m');
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    useEffect(() => {
        if (!cropName || !locationId) {
            setError('Missing cropName or locationId parameter');
            setLoading(false);
            return;
        }
        // Fetch predictions data from the backend
        axios.get<PredictionsResponse>(`${import.meta.env.VITE_API_URL!}/api/predictions`, {
            params: {
                crop_name: cropName,
                location_id: locationId
            }
        })
            .then((response) => {
                setPredictions(response.data);
                setErrorMessage(null);
            })
            .catch((error) => {
                console.error('Error fetching predictions:', error);
                setErrorMessage(error.toString());
            });
    }, []);

    const handleForecastChange = (event: SelectChangeEvent<{ value: unknown }>) => {
        setSelectedForecast(event.target.value as string);
    };

    const chartData = predictions !== null ? {
        labels: predictions.forecast.map(data => `${data.month}/${data.year}`),
        datasets: [
            {
                label: selectedForecast.replace(/([A-Z])/g, ' $1').trim(), // Format label
                data: predictions.forecast.map(data => data[selectedForecast as keyof ClimateDataDetails]),
                fill: false,
                borderColor: 'rgba(75,192,192,1)',
                tension: 0.1,
            },
        ],
    } : null;

    return (
        <Box sx={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "start", alignItems: "center", paddingLeft: 16, paddingRight: 16, paddingTop: 2 }}>
            {errorMessage !== null ? <Alert severity="error" style={{}}>{errorMessage}</Alert> : <></>}
            {predictions === null
                ? <CircularProgress></CircularProgress>
                : <Box sx={{ padding: 2 }}>
                    <Typography variant="h4" gutterBottom>
                        Prediction Results
                    </Typography>

                    <Typography variant="h5" gutterBottom>
                        Best Combinations
                    </Typography>
                    <TableContainer component={Paper} sx={{ marginBottom: 4 }}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Sowing Date</TableCell>
                                    <TableCell>Harvest Date</TableCell>
                                    <TableCell>Estimated Yield (tons/ha)</TableCell>
                                    <TableCell>Duration (months)</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {predictions.bestCombinations.map((combination, index) => (
                                    <TableRow key={index}>
                                        <TableCell>{`${combination.sowingMonth}/${combination.sowingYear}`}</TableCell>
                                        <TableCell>{`${combination.harvestMonth}/${combination.harvestYear}`}</TableCell>
                                        <TableCell>{combination.estimatedYieldPerHectar}</TableCell>
                                        <TableCell>{combination.duration}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>

                    <Typography variant="h5" gutterBottom>
                        Climate Forecast
                    </Typography>
                    <Select value={{ value: selectedForecast }} onChange={handleForecastChange} sx={{ marginBottom: 2 }}>
                        <MenuItem value="temperature2m">Temperature (2m)</MenuItem>
                        <MenuItem value="totalPrecipitation">Total Precipitation</MenuItem>
                        <MenuItem value="surfaceSolarRadiationDownwards">Surface Solar Radiation Downwards</MenuItem>
                        <MenuItem value="surfaceThermalRadiationDownwards">Surface Thermal Radiation Downwards</MenuItem>
                        <MenuItem value="surfaceNetSolarRadiation">Surface Net Solar Radiation</MenuItem>
                        <MenuItem value="surfaceNetThermalRadiation">Surface Net Thermal Radiation</MenuItem>
                        <MenuItem value="totalCloudCover">Total Cloud Cover</MenuItem>
                        <MenuItem value="dewpointTemperature2m">Dewpoint Temperature (2m)</MenuItem>
                        <MenuItem value="soilTemperatureLevel3">Soil Temperature (Level 3)</MenuItem>
                        <MenuItem value="volumetricSoilWaterLayer3">Volumetric Soil Water (Layer 3)</MenuItem>
                    </Select>
                    <Line data={chartData!} />
                </Box>}
        </Box>
    );
};

export default PredictionPage;
