// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Register from './components/Register';
import Verify from './components/Verify';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import JobDetail from './components/JobDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/verify" element={<Verify />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/job-detail/:jobId" element={<JobDetail />} />
        <Route path="*" element={<Register />} /> {/* Default to register for now */}
      </Routes>
    </Router>
  );
}

export default App;