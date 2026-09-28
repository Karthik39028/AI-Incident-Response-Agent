import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Applications from "./pages/Applications";
import AddApplication from "./pages/AddApplication";
import ApplicationDetails from "./pages/ApplicationDetails";
import IncidentDetails from "./pages/IncidentDetails";
import Hindsight from "./pages/Hindsight";
import Activity from "./pages/Activity";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/login" element={<Login />} />

        <Route path="/dashboard" element={<Dashboard />} />

        <Route path="/applications" element={<Applications />} />

        <Route
          path="/applications/new"
          element={<AddApplication />}
        />

        <Route
          path="/applications/:id"
          element={<ApplicationDetails />}
        />

        <Route
          path="/incidents/:id"
          element={<IncidentDetails />}
        />

        <Route path="/hindsight" element={<Hindsight />} />

        <Route path="/activity" element={<Activity />} />

        <Route
          path="/"
          element={<Navigate to="/login" replace />}
        />

        <Route
          path="*"
          element={<Navigate to="/login" replace />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;