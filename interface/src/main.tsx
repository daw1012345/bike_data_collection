import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';
import { WebSocketConnectionProvider } from './utils/WebSocketConnection.tsx';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <WebSocketConnectionProvider url={"ws://10.42.0.1:9999"}> 
      <App />
    </WebSocketConnectionProvider>
  </React.StrictMode>,
)
