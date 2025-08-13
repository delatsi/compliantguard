import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';

// Mock the auth context since App component uses it
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn()
  }),
  AuthProvider: ({ children }) => children
}));

vi.mock('../contexts/AdminContext', () => ({
  useAdmin: () => ({
    isAdmin: false,
    adminUser: null,
    hasPermission: vi.fn(() => false),
    loginAdmin: vi.fn(),
    logoutAdmin: vi.fn()
  }),
  AdminProvider: ({ children }) => children
}));

vi.mock('../contexts/DemoContext', () => ({
  useDemoData: () => ({
    demoData: {},
    isDemoMode: false,
    setIsDemoMode: vi.fn()
  }),
  DemoProvider: ({ children }) => children
}));

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />);
    
    // The app should render without throwing errors
    expect(document.body).toBeTruthy();
  });

  it('contains the main app structure', () => {
    const { container } = render(<App />);
    
    // Check that the app renders with content
    expect(container.firstChild).toBeTruthy();
  });
});