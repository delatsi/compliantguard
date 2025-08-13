import { useState, useEffect } from 'react';

export const useVersion = () => {
  const [version, setVersion] = useState({
    app_version: 'loading...',
    api_version: 'loading...',
    build_date: 'loading...',
    git_commit: import.meta.env.VITE_VERSION || 'unknown'
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        // Try to fetch from version.json in public folder
        const response = await fetch('/version.json');
        if (response.ok) {
          const versionData = await response.json();
          setVersion({
            ...versionData,
            git_commit: import.meta.env.VITE_VERSION || versionData.git_commit || 'unknown'
          });
        } else {
          // Fallback to environment variables
          setVersion({
            app_version: import.meta.env.VITE_APP_VERSION || '1.2.0',
            api_version: import.meta.env.VITE_API_VERSION || '1.2.0',
            build_date: import.meta.env.VITE_BUILD_DATE || new Date().toISOString().split('T')[0],
            git_commit: import.meta.env.VITE_VERSION || 'development'
          });
        }
      } catch (error) {
        console.warn('Could not fetch version info:', error);
        // Use environment variables as fallback
        setVersion({
          app_version: import.meta.env.VITE_APP_VERSION || '1.2.0',
          api_version: import.meta.env.VITE_API_VERSION || '1.2.0',
          build_date: import.meta.env.VITE_BUILD_DATE || new Date().toISOString().split('T')[0],
          git_commit: import.meta.env.VITE_VERSION || 'development'
        });
      } finally {
        setLoading(false);
      }
    };

    fetchVersion();
  }, []);

  return { version, loading };
};