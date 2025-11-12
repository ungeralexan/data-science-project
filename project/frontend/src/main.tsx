import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import 'antd/dist/reset.css';
import './index.css';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <ConfigProvider
      
        // The components are based on Ant-Design but we adjust the design a little.
        theme={{
          components: {
            Layout: {
              headerBg: '#fff',
              headerColor: '#000',
            },
          },
          token: {
            colorBgContainer: '#fff',
            colorBgLayout: '#fff'
          }
        }}
      >
        <App />
      </ConfigProvider>
    </BrowserRouter>
  </StrictMode>
);
