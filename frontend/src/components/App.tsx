import { useContext, useEffect, useState } from "react";
import { AuthContext } from "./AuthProvider";
import { getUserInfo } from "../utils/utils";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Splash from "./Splash";
import Login from "./Login";
import Locations from "./Locations";
import ProtectedRoute from "./ProtectedRoute";
import NavBar from "./NavBar";

export default function App() {

    const authContext = useContext(AuthContext);

    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        getUserInfo().then((user) => {
            authContext!.setCurrentUser(user);
            setIsLoading(false);
        });
    }, []);

    return (
        isLoading
            ? <Splash />
            : <div style={{ width: "100vw", height: "100vh" }}>
                <BrowserRouter>
                    {
                        window.location.pathname === "/login" || window.location.pathname === "/"
                            ? <></>
                            : <NavBar />
                    }
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/locations" element={
                            <ProtectedRoute>
                                <Locations />
                            </ProtectedRoute>
                        } />
                        <Route path="/predictions" element={
                            <ProtectedRoute>
                                <Locations />
                            </ProtectedRoute>
                        } />
                        <Route path="/users" element={
                            <ProtectedRoute>
                                <Locations />
                            </ProtectedRoute>
                        } />
                        <Route path="/" element={<Navigate to="/locations" />} />
                    </Routes>
                </BrowserRouter>
            </div>
    );
}