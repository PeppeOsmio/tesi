import { List } from "@mui/material";
import React from "react";

import { Box, Card, CardContent, Typography, Button, Grid } from '@mui/material';
import { ZappaiLocation } from "../utils/classes";
import LocationCard from "./LocationCard";


interface LocationsProps {
}

const Locations: React.FC<LocationsProps> = () => {

    const locations: ZappaiLocation[] = [
        {
            country: 'United States',
            name: 'Location 1',
            coordinates: '40.7128° N, 74.0060° W',
            isModelReady: true,
            isDownloadingPastClimateData: false,
            lastPastClimateDataYear: 2023,
            lastPastClimateDataMonth: 7,
        },
        {
            country: 'Canada',
            name: 'Location 2',
            coordinates: '45.4215° N, 75.6972° W',
            isModelReady: false,
            isDownloadingPastClimateData: true,
            lastPastClimateDataYear: null,
            lastPastClimateDataMonth: null,
        },
        // Add more locations as needed
    ];

    return <Box sx={{ paddingTop: 2, paddingRight: 16, paddingLeft: 16 }}>
        <Grid container spacing={2}>
            {locations.map((location, index) => (
                <Grid item xs={12} sm={6} key={index}>
                    <LocationCard
                        location={location}
                    />
                </Grid>
            ))}
        </Grid>
    </Box>
}

export default Locations;