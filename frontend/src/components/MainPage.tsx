import React from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import NavBar from './NavBar';
import ProtectedRoute from './ProtectedRoute';
import Locations from './Locations';
import { Box } from '@mui/material';
import CreateLocation from './CreateLocation';
import ChooseCrop from './ChooseCrop';
import PredictionPage from './PredictionPage';

export const MainPage: React.FC = () => {
    return (
        <Box sx={{width: "100vw", height: "100vh", display: "flex", flexDirection: "column", justifyContent: "start", alignItems: "center"}}>
            <NavBar />
            <Routes>
                <Route path="/locations" element={
                    <ProtectedRoute>
                        <Locations />
                    </ProtectedRoute>
                } />
                <Route path="/locations/create" element={<CreateLocation/>}/>
                <Route path="/predictions/create/:locationId" element={
                    <ProtectedRoute>
                        <ChooseCrop />
                    </ProtectedRoute>
                } />
                <Route path="/predictions" element={<PredictionPage/>}/>
                <Route path="/users" element={
                    <ProtectedRoute>
                        <Locations />
                    </ProtectedRoute>
                } />
                <Route path="/" element={<Navigate to="/locations" />} />
            </Routes>
        </Box>
    )
}
