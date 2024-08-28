import React, { useContext, useState } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { Box, Menu, MenuItem } from '@mui/material';
import { Link, useNavigate } from 'react-router-dom';
import { Person } from '@mui/icons-material';
import { AuthContext } from './AuthProvider';

const Navbar: React.FC = () => {

  const authContext = useContext(AuthContext);
  const navigate = useNavigate();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);


  return (
    <AppBar position="static">
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Typography variant="h6" sx={{ flexGrow: 0 }}>
          <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
            🌱⚡ ZappAI
          </Link>
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, flexGrow: 1, justifyContent: 'center' }}>
          <Button color="inherit" component={Link} to="/locations">
            Home
          </Button>
          <Button color="inherit" component={Link} to="/predictions">
            About
          </Button>
          <Button color="inherit" component={Link} to="/users">
            Services
          </Button>
          <Button color="inherit" component={Link} to="/contact">
            Contact
          </Button>
        </Box>

        <Button color="inherit" onClick={(event) => {
          setAnchorEl(event.currentTarget);
        }} startIcon={<Person />}>
          {authContext!.currentUser?.username}
        </Button>
        <Menu
          anchorEl={anchorEl}
          open={open}
          onClose={() => {
            setAnchorEl(null);
          }}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          <MenuItem onClick={() => {
            localStorage.removeItem("zappai_access_token");
            authContext!.setCurrentUser(null);
            setAnchorEl(null);
            navigate("/", {replace: true});
          }}>Logout</MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
