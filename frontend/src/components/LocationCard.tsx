import React from 'react';
import { Card, CardContent, Typography, Button } from '@mui/material';
import { ZappaiLocation } from '../utils/classes';

interface LocationCardProps {
    location: ZappaiLocation;
}

const LocationCard: React.FC<LocationCardProps> = ({ location }) => {
    const {
        country,
        name,
        coordinates,
        isModelReady,
        isDownloadingPastClimateData,
        lastPastClimateDataYear,
        lastPastClimateDataMonth,
    } = location;

    // Determine the "last updated" value
    const lastUpdated = lastPastClimateDataYear && lastPastClimateDataMonth
        ? `${lastPastClimateDataMonth}/${lastPastClimateDataYear}`
        : "never";

    return (
        <Card>
            <CardContent>
                <Typography variant="h6">{name}</Typography>
                <Typography variant="subtitle1">{country}</Typography>
                <Typography variant="body2" color="text.secondary">
                    Coordinates: {coordinates}
                </Typography>
                <Typography variant="body2" color={isModelReady ? 'green' : 'red'}>
                    Weather AI model {isModelReady ? 'ready' : 'not ready'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Last past climate data : {lastUpdated}
                </Typography>
                {isDownloadingPastClimateData
                    ? <Button
                        variant="contained"
                        color="primary"
                        sx={{ mt: 2 }}
                        disabled>
                        Downloading data for AI model...
                    </Button>
                    : <Button
                        variant="contained"
                        color="primary"
                        sx={{ mt: 2 }}>
                        Download data and create AI model
                    </Button>}
            </CardContent>
        </Card>
    );
};

export default LocationCard;
