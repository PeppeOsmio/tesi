import { Alert, Button, CircularProgress } from "@mui/material";
import React, { useEffect, useState } from "react";

import { Box, Grid } from '@mui/material';
import { ZappaiLocation } from "../utils/classes";
import LocationCard from "./LocationCard";
import axios from "axios";
import { Add } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";


interface LocationsProps {
}

const Locations: React.FC<LocationsProps> = () => {

    const [locations, setLocations] = useState<ZappaiLocation[] | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const navigate = useNavigate();

    const updateLocations = async () => {
        const zappai_access_token = localStorage.getItem("zappai_access_token");
        while (true) {
            axios.get<ZappaiLocation[]>(`${import.meta.env.VITE_API_URL!}/api/locations`, {
                headers: {
                    "Authorization": `Bearer ${zappai_access_token}`
                }
            }).then((response) => {
                setLocations(response.data);
            }).catch((error) => {
                console.log(error);
                setErrorMessage(error.toString());
            });
            await new Promise((resolve) => setTimeout(resolve, 30000));
        }
    }

    useEffect(() => {
        updateLocations();
    }, []);

    const onDeleteLocation = (location: ZappaiLocation) => {
        const zappai_access_token = localStorage.getItem("zappai_access_token");
        axios.delete(`${import.meta.env.VITE_API_URL!}/api/locations/${location.id}`, { headers: { Authorization: `Bearer ${zappai_access_token}` } })
            .then(
                (response) => {
                    setLocations(old => old?.filter(loc => loc.id !== location.id) ?? null);
                    setErrorMessage(null);
                }
            )
            .catch((error) => setErrorMessage(error.toString()));
    }

    const onDownloadData = (location: ZappaiLocation) => {
        const zappai_access_token = localStorage.getItem("zappai_access_token");
        axios.get(`${import.meta.env.VITE_API_URL!}/api/locations/past_climate_data/${location.id}`, { headers: { Authorization: `Bearer ${zappai_access_token}` } })
            .then(
                (response) => {
                    setLocations(old => old?.map((loc) => {
                        if (loc.id !== location.id) {
                            return loc;
                        }
                        loc.isDownloadingPastClimateData = true;
                        return loc;
                    }) ?? null);
                    setErrorMessage(null);
                }
            )
            .catch((error) => setErrorMessage(error.toString()));
    }

    const onMakePrediction = () => {
        navigate("/locat")
    }


    return <Box sx={{ paddingTop: 2, paddingRight: 16, paddingLeft: 16, flexGrow: 1, width: "100%", display: "flex", flexDirection: "column", gap: 2 }}>
        {errorMessage !== null ? <Alert severity="error" style={{}}>{errorMessage}</Alert> : <></>}
        {
            locations === null
                ? <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flexGrow: 1 }}>
                    <CircularProgress sx={{}}></CircularProgress>
                </Box>
                : <Grid container spacing={2}>
                    {locations.map((location, index) => (
                        <Grid item xs={12} sm={6} key={index}>
                            <LocationCard
                                location={location}
                                onDelete={onDeleteLocation}
                                onDownloadData={onDownloadData}
                            />
                        </Grid>
                    ))}
                </Grid>
        }
        <Button
            variant="contained"
            color="primary"
            sx={{
                mt: 2, position: 'fixed',
                bottom: '32px',
                right: '32px'
            }}
            startIcon={<Add />}
            onClick={() => navigate("/locations/create")}>
            Create a Location
        </Button>
    </Box>
}

export default Locations;