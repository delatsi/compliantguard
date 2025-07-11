import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useDemoData } from '../contexts/DemoContext';
import {
  HomeIcon,
  DocumentMagnifyingGlassIcon,
  DocumentTextIcon,
  FolderIcon,
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  UserCircleIcon,
  ArrowLeftOnRectangleIcon,
  ExclamationTriangleIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useState } from 'react';

const DemoLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { demoData } = useDemoData();
  const location = useLocation();
  const navigate = useNavigate();

  const navigation = [
    { name: 'Dashboard', href: '/demo', icon: HomeIcon },
    { name: 'Scan Project', href: '/demo/scan', icon: DocumentMagnifyingGlassIcon },
    { name: 'Reports', href: '/demo/reports', icon: DocumentTextIcon },
    { name: 'Documentation', href: '/demo/documentation', icon: FolderIcon },
    { name: 'Settings', href: '/demo/settings', icon: Cog6ToothIcon },
  ];

  const isActive = (path) => location.pathname === path;

  const handleExitDemo = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Demo Mode Banner */}
      <div className="bg-orange-500 text-white px-4 py-2 text-center text-sm font-medium">
        <div className="flex items-center justify-center space-x-2">
          <EyeIcon className="h-4 w-4" />
          <span>Demo Mode - Explore ThemisGuard with sample data</span>
          <button
            onClick={handleExitDemo}
            className="ml-4 bg-orange-600 hover:bg-orange-700 px-3 py-1 rounded text-xs"
          >
            Exit Demo
          </button>
        </div>
      </div>

      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white shadow-xl">
          <div className="flex h-16 items-center justify-between px-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">TG</span>
                </div>
              </div>
              <span className="text-xl font-semibold text-gray-900">ThemisGuard</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 hover:text-gray-500"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <nav className="flex-1 px-4 py-4">
            <ul className="space-y-2">
              {navigation.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive(item.href)
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col mt-10">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200">
          <div className="flex h-16 items-center px-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">TG</span>
                </div>
              </div>
              <span className="text-xl font-semibold text-gray-900">ThemisGuard</span>
            </div>
          </div>
          <nav className="flex-1 px-4 py-4">
            <ul className="space-y-2">
              {navigation.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive(item.href)
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <item.icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64 mt-10">
        {/* Top bar */}
        <div className="sticky top-10 z-40 bg-white border-b border-gray-200">
          <div className="flex h-16 items-center justify-between px-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden -ml-2 p-2 text-gray-400 hover:text-gray-500"
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-700">
                <UserCircleIcon className="h-5 w-5" />
                <span>{demoData.user.email}</span>
                <span className="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full">
                  Demo User
                </span>
              </div>
              <button
                onClick={handleExitDemo}
                className="flex items-center space-x-2 text-sm text-gray-700 hover:text-gray-900"
              >
                <ArrowLeftOnRectangleIcon className="h-5 w-5" />
                <span>Exit Demo</span>
              </button>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default DemoLayout;