import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { ClimateDataDetails, PredictionsResponse, ZappaiLocation } from '../utils/types';
import { Alert, Box, CircularProgress, MenuItem, Paper, Select, SelectChangeEvent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography, Grid } from '@mui/material';
import { useSearchParams } from 'react-router-dom';
import { LineChart } from '@mui/x-charts';

const PredictionPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const cropName = searchParams.get('cropName');
    const locationId = searchParams.get('locationId');

    const [predictions, setPredictions] = useState<PredictionsResponse | null>(null);
    const [selectedForecast, setSelectedForecast] = useState<string>('temperature2M');
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [location, setLocation] = useState<ZappaiLocation | null>(null);

    const loadData = async () => {
        if (!cropName || !locationId) {
            setErrorMessage('Missing cropName or locationId parameter');
            setIsLoading(false);
            return;
        }

        const zappai_access_token = localStorage.getItem("zappai_access_token");
        await axios.get<ZappaiLocation>(`${import.meta.env.VITE_API_URL!}/api/locations/${locationId}`, {
            headers: {
                Authorization: `Bearer ${zappai_access_token}`
            }
        }).then((response) => {
            setLocation(response.data);
            setErrorMessage(null);
        }).catch((error) => {
            setErrorMessage(error.toString());
        });

        await axios.get<PredictionsResponse>(`${import.meta.env.VITE_API_URL!}/api/predictions`, {
            headers: {
                Authorization: `Bearer ${zappai_access_token}`
            },
            params: {
                crop_name: cropName,
                location_id: locationId
            }
        })
            .then((response) => {
                setPredictions(response.data);
                setErrorMessage(null);
                setIsLoading(false);
            })
            .catch((error) => {
                console.error('Error fetching predictions:', error);
                setErrorMessage(error.toString());
            });
    }

    useEffect(() => {
        loadData();
    }, []);

    const handleForecastChange = (event: SelectChangeEvent<{ value: unknown }>) => {
        setSelectedForecast(event.target.value as string);
    };

    return (
        <Box sx={{ width: "100%", height: "100%", display: "flex", overflow: "scroll", flexDirection: "column", justifyContent: "start", alignItems: "center", padding: 2 }}>
            {errorMessage !== null ? <Alert severity="error">{errorMessage}</Alert> : <></>}
            {isLoading
                ? <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flexGrow: 1 }}>
                    <Typography variant='h4' gutterBottom>
                    Evaluating prediction...
                    </Typography>
                    <CircularProgress></CircularProgress>
                </Box>
                : <Box sx={{ padding: 2, width: "100%" }}>
                    {location && (
                        <Box sx={{ marginBottom: 4, textAlign: 'center' }}>
                            <Typography variant="h4" gutterBottom>
                                {location.name}, {location.country}
                            </Typography>
                            <Typography variant="h6" color="textSecondary">
                                Crop: {cropName}
                            </Typography>
                        </Box>
                    )}

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
                                {predictions!.bestCombinations.map((combination, index) => (
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

                    <Grid container spacing={2} alignItems="center" sx={{ marginBottom: 4 }}>
                        <Grid item xs={12} md={3}>
                            <Select title={selectedForecast} fullWidth value={selectedForecast as any} onChange={handleForecastChange}>
                                <MenuItem value="temperature2M">Temperature (2m)</MenuItem>
                                <MenuItem value="totalPrecipitation">Total Precipitation</MenuItem>
                                <MenuItem value="surfaceSolarRadiationDownwards">Surface Solar Radiation Downwards</MenuItem>
                                <MenuItem value="surfaceThermalRadiationDownwards">Surface Thermal Radiation Downwards</MenuItem>
                                <MenuItem value="surfaceNetSolarRadiation">Surface Net Solar Radiation</MenuItem>
                                <MenuItem value="surfaceNetThermalRadiation">Surface Net Thermal Radiation</MenuItem>
                                <MenuItem value="totalCloudCover">Total Cloud Cover</MenuItem>
                                <MenuItem value="dewpointTemperature2M">Dewpoint Temperature (2m)</MenuItem>
                                <MenuItem value="soilTemperatureLevel3">Soil Temperature (Level 3)</MenuItem>
                                <MenuItem value="volumetricSoilWaterLayer3">Volumetric Soil Water (Layer 3)</MenuItem>
                            </Select>
                        </Grid>
                        <Grid item xs={12} md={9}>
                            <LineChart
                                series={[
                                    {
                                        data: predictions!.forecast.map(data => data[selectedForecast as keyof ClimateDataDetails])
                                    }
                                ]}
                                xAxis={[{ scaleType: "point", data: predictions!.forecast.map((data) => `${data.month}/${data.year}`) }]}
                                height={400}
                                sx={{ width: "100%" }}
                            />
                        </Grid>
                    </Grid>
                </Box>}
        </Box>
    );
};

export default PredictionPage;
