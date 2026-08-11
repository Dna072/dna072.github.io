import Dashboard from './Dashboard';
import Login from './components/Login';
import { useAuth } from './context/AuthContext';

export default function App() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Dashboard /> : <Login />;
}
