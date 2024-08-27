import * as React from 'react';
import { useState } from "react";
import Button from '@mui/material/Button';
import { Alert, createTheme, CssBaseline, Input, TextField, ThemeProvider, Typography } from '@mui/material';
import axios, { AxiosError } from 'axios';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

export default function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <div style={{ width: "100vw", height: "100vh", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: "16px" }}>

          <Typography variant='h3' component="h3" style={{ marginBottom: "16px" }}>
            Welcome to ZappAI 🌱⚡
          </Typography>

          {errorMessage !== null ? <Alert severity="error" style={{ width: "100%" }}>{errorMessage}</Alert> : <></>}

          <TextField label="Username" placeholder='John Doe' type="email" style={{ width: "100%" }} defaultValue={username} onBlur={(event) => setUsername(event.currentTarget.value)}>
          </TextField>
          <TextField label="Password" type='password' placeholder='ComplexPassword!' style={{ width: "100%" }} defaultValue={password} onBlur={(event) => setPassword(event.currentTarget.value)}>
          </TextField>

          <Button variant='contained' style={{ width: "100%" }} onClick={async () => {
            if (username.trim() === "" || password.trim() === "") {
              return;
            }
            try {
              const result = await axios.post(`${import.meta.env.VITE_API_URL}/auth/`, new URLSearchParams({ username: username, password: password }), { withCredentials: true });
            } catch (error) {
              if (axios.isAxiosError(error)) {
                const axiosError = error as AxiosError;
                if (axiosError.status === 401) {
                  setErrorMessage("Invalid credentials")
                } else {
                  setErrorMessage(`Error ${axiosError.status}: "${axiosError.message}"`);
                }
              } else {
                setErrorMessage((error as Error).toString());
              }
              return;
            }
            setErrorMessage(null);
          }}>Login</Button>

        </div>
      </div>
    </ThemeProvider>
  );
}