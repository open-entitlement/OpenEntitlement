import {createRoot} from 'react-dom/client';
import {initTelemetry} from './telemetry.ts';
import {ToastProvider, ReasonProvider} from './ui.tsx';
import {WorkspaceApp} from './workspace/app.tsx';
import './style.css';
import './design.css';

void initTelemetry();
createRoot(document.getElementById('root')!).render(<ToastProvider><ReasonProvider><WorkspaceApp/></ReasonProvider></ToastProvider>);
