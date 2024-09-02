import React, { useState } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Select, MenuItem, SelectChangeEvent } from '@mui/material';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { ClimateDataDetails, PredictionsResponse, SowingAndHarvestingDetails } from '../utils/types';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface ViewPredictionResultProps {
    predictions: PredictionsResponse;
}

const ViewPredictionResult: React.FC<ViewPredictionResultProps> = ({ predictions }) => {
    const [selectedForecast, setSelectedForecast] = useState<string>('temperature2m');

    const handleForecastChange = (event: SelectChangeEvent<{ value: unknown }>) => {
        setSelectedForecast(event.target.value as string);
    };

    const forecastLabels = predictions.forecast.map(data => `${data.month}/${data.year}`);
    const forecastData = predictions.forecast.map(data => data[selectedForecast as keyof ClimateDataDetails]);

    const chartData = {
        labels: forecastLabels,
        datasets: [
            {
                label: selectedForecast.replace(/([A-Z])/g, ' $1').trim(), // Format label
                data: forecastData,
                fill: false,
                borderColor: 'rgba(75,192,192,1)',
                tension: 0.1,
            },
        ],
    };

    return (
        <Box sx={{ padding: 2 }}>
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
            <Select value={{value: selectedForecast}} onChange={handleForecastChange} sx={{ marginBottom: 2 }}>
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
            <Line data={chartData} />
        </Box>
    );
};

export default ViewPredictionResult;
