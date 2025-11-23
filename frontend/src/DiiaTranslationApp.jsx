import React, { useState, useEffect, useRef } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { login as apiLogin, fetchDocuments as apiFetchDocuments, uploadFile, startProcessing, checkStatus } from './api';
import {
  FileText,
  Upload,
  Check,
  ChevronRight,
  ArrowLeft,
  Download,
  Languages,
  MoreHorizontal,
  Search,
  X,
  Plus,
  Loader2,
  FileCheck,
  User,
  LogOut,
  ScanLine,
  Maximize2,
  Camera,
  RotateCw,
  XCircle
} from 'lucide-react';

/* --- MOCK DATA & ASSETS ---
  Simulating backend responses
*/
// Using a standard W3C dummy PDF for visualization
const SAMPLE_PDF = "https://www.buds.com.ua/images/Lorem_ipsum.pdf";

const MOCK_DOCS = [
  {
    id: 'doc-001',
    title: 'Birth Certificate',
    type: 'Certificate',
    date: '22 Nov 2025',
    status: 'completed',
    originalLang: 'Ukrainian',
    targetLang: 'English',
    originalPdf: SAMPLE_PDF,
    translatedPdf: SAMPLE_PDF
  },
  {
    id: 'doc-002',
    title: 'University Diploma',
    type: 'Education',
    date: '20 Nov 2025',
    status: 'processing',
    originalLang: 'Ukrainian',
    targetLang: 'German',
    originalPdf: SAMPLE_PDF,
    translatedPdf: null
  },
  {
    id: 'doc-003',
    title: 'Vaccination Record',
    type: 'Medical',
    date: '15 Oct 2025',
    status: 'completed',
    originalLang: 'Ukrainian',
    targetLang: 'English',
    originalPdf: SAMPLE_PDF,
    translatedPdf: SAMPLE_PDF
  }
];

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'pl', name: 'Polish', flag: '🇵🇱' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
];

/* --- COMPONENT: BUTTONS ---
*/
const Button = ({ children, variant = 'primary', className = '', onClick, icon: Icon, disabled }) => {
  const baseStyles = "relative font-bold text-sm sm:text-base transition-all active:scale-95 flex items-center justify-center gap-2";
  const variants = {
    primary: "bg-black text-white hover:bg-gray-800 rounded-full py-4 px-8 shadow-lg shadow-black/20",
    secondary: "bg-transparent border-2 border-black text-black hover:bg-black/5 rounded-full py-3.5 px-8",
    ghost: "bg-transparent text-black hover:bg-black/5 rounded-lg p-2",
    diia: "bg-gradient-to-r from-[#D4F4E4] to-[#E3D4F4] text-black rounded-xl py-4 px-6 font-bold" // Simulated Diia gradient
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variants[variant]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {Icon && <Icon size={20} />}
      {children}
    </button>
  );
};

/* --- COMPONENT: INPUTS ---
*/
const Input = ({ label, placeholder, type = "text", value, onChange }) => (
  <div className="flex flex-col gap-2 w-full">
    {label && <label className="text-sm font-bold text-gray-500 ml-1">{label}</label>}
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className="w-full h-14 bg-[#F5F5F7] rounded-2xl px-4 font-medium outline-none focus:ring-2 focus:ring-black transition-all"
    />
  </div>
);

/* --- COMPONENT: HEADER ---
*/
const Header = ({ user, onLogout, title }) => (
  <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-100 h-16 sm:h-20 flex items-center justify-between px-4 sm:px-8">
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 sm:w-10 sm:h-10 bg-black rounded-full flex items-center justify-center text-white font-bold text-xs sm:text-sm tracking-tighter">
        diia
      </div>
      <h1 className="font-bold text-lg sm:text-xl tracking-tight">{title}</h1>
    </div>

    {user && (
      <div className="flex items-center gap-2 sm:gap-4">
        <div className="hidden sm:flex flex-col items-end">
          <span className="text-sm font-bold">{user.name}</span>
          <span className="text-xs text-gray-500">{user.email}</span>
        </div>
        <button onClick={onLogout} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <LogOut size={20} className="text-gray-600" />
        </button>
        <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-tr from-[#FFC2E3] to-[#00D2BA] p-0.5">
          <div className="w-full h-full bg-white rounded-full flex items-center justify-center">
            <User size={16} className="text-black" />
          </div>
        </div>
      </div>
    )}
  </header>
);

/* --- MAIN APP COMPONENT ---
*/
export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState('login'); // login, dashboard, upload, detail
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all'); // 'all', 'processing', 'completed'

  // Load documents from backend
  const loadDocuments = async () => {
    try {
      const data = await apiFetchDocuments();

      // Transform backend data to frontend format
      const transformedDocs = data.documents.map(doc => ({
        id: doc.id,
        title: doc.title,
        type: doc.type,
        date: new Date(doc.date * 1000).toLocaleDateString('en-GB', {
          day: 'numeric',
          month: 'short',
          year: 'numeric'
        }),
        status: doc.status,
        originalLang: 'Ukrainian',
        targetLang: 'English', // TODO: get from backend
        originalPdf: doc.original_url,
        translatedPdf: doc.translated_url || null,
        requestId: doc.id
      }));

      setDocuments(transformedDocs);
    } catch (err) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents');
    }
  };

  // Check for existing session on mount
  useEffect(() => {
    const restoreSession = async () => {
      const credential = localStorage.getItem('google_credential');
      const userInfoStr = localStorage.getItem('user_info');

      if (credential && userInfoStr) {
        try {
          // Restore user info from localStorage
          const userInfo = JSON.parse(userInfoStr);
          setUser(userInfo);

          // Try to fetch documents to validate the session
          const data = await apiFetchDocuments();

          // Transform and set documents
          const transformedDocs = data.documents.map(doc => ({
            id: doc.id,
            title: doc.title,
            type: doc.type,
            date: new Date(doc.date * 1000).toLocaleDateString('en-GB', {
              day: 'numeric',
              month: 'short',
              year: 'numeric'
            }),
            status: doc.status,
            originalLang: 'Ukrainian',
            targetLang: 'English',
            originalPdf: doc.original_url,
            translatedPdf: doc.translated_url || null,
            requestId: doc.id
          }));

          setDocuments(transformedDocs);
          setView('dashboard');
        } catch (err) {
          console.error('Session restoration failed:', err);
          // Session is invalid, clear it
          localStorage.removeItem('google_credential');
          localStorage.removeItem('user_info');
          setUser(null);
        }
      }

      setIsCheckingSession(false);
    };

    restoreSession();
  }, []);

  // Poll for updates on processing documents
  useEffect(() => {
    if (view === 'dashboard' && documents.some(doc => doc.status === 'processing')) {
      const interval = setInterval(() => {
        loadDocuments();
      }, 5000); // Poll every 5 seconds

      return () => clearInterval(interval);
    }
  }, [view, documents]);

  // AUTH HANDLERS
  const handleGoogleLoginSuccess = async (credentialResponse) => {
    setLoading(true);
    setError(null);

    try {
      // Send the credential (ID token) to our backend using API utility
      const data = await apiLogin(credentialResponse.credential);

      // Store the credential and user info for authenticated requests
      localStorage.setItem('google_credential', credentialResponse.credential);
      localStorage.setItem('user_info', JSON.stringify(data.user));

      setUser(data.user);

      // Load user's documents
      await loadDocuments();

      setView('dashboard');
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Failed to log in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLoginError = () => {
    setLoading(false);
    setError('Google login failed. Please try again.');
  };

  const handleLogout = () => {
    localStorage.removeItem('google_credential');
    localStorage.removeItem('user_info');
    setUser(null);
    setView('login');
  };

  // NAVIGATION HANDLERS
  const goDashboard = () => setView('dashboard');

  const handleOpenDoc = (doc) => {
    setSelectedDoc(doc);
    setView('detail');
  };

  const handleCreateDoc = (newDoc) => {
    setDocuments([newDoc, ...documents]);
    setView('dashboard');
  };

  /* --- VIEW: LOGIN ---
  */
  if (view === 'login') {
    // Show loading while checking for existing session
    if (isCheckingSession) {
      return (
        <div className="min-h-screen bg-white flex items-center justify-center">
          <Loader2 className="animate-spin text-black" size={40} />
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-white flex flex-col font-sans text-black selection:bg-[#FFC2E3]">
        <main className="flex-1 flex flex-col items-center justify-center p-6 relative overflow-hidden">
          {/* Decorative Circles mimicking Diia style */}
          <div className="absolute top-[-10%] left-[-10%] w-[50vh] h-[50vh] bg-[#FFC2E3] rounded-full blur-[100px] opacity-20 pointer-events-none" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[50vh] h-[50vh] bg-[#00D2BA] rounded-full blur-[100px] opacity-20 pointer-events-none" />

          <div className="w-full max-w-md flex flex-col items-center text-center space-y-8 z-10">
            <div className="w-20 h-20 bg-black text-white rounded-[24px] flex items-center justify-center mb-4 shadow-2xl shadow-black/20">
              <span className="font-bold text-3xl tracking-tighter">diia</span>
            </div>

            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl font-black tracking-tight leading-[1.1]">
                Document<br/>Translation
              </h1>
              <p className="text-gray-500 text-lg sm:text-xl max-w-xs mx-auto">
                Fast, official translations.
                <br/>State in a smartphone.
              </p>
            </div>

            <div className="w-full pt-8 space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {loading ? (
                <div className="w-full h-16 bg-white border-2 border-black/10 rounded-full flex items-center justify-center">
                  <Loader2 className="animate-spin text-black" />
                </div>
              ) : (
                <div className="flex justify-center">
                  <GoogleLogin
                    onSuccess={handleGoogleLoginSuccess}
                    onError={handleGoogleLoginError}
                    useOneTap
                    theme="outline"
                    size="large"
                    text="continue_with"
                    shape="pill"
                    width="100%"
                  />
                </div>
              )}

              <p className="text-xs text-gray-400 font-medium text-center">
                By continuing, you accept the Terms of Service
              </p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  /* --- VIEW: DASHBOARD ---
  */
  if (view === 'dashboard') {
    return (
      <div className="min-h-screen bg-[#F5F5F7] font-sans text-black pb-24 sm:pb-0">
        <Header user={user} onLogout={handleLogout} title="Documents" />

        <main className="max-w-5xl mx-auto p-4 sm:p-8 space-y-8">
          {/* Action Bar */}
          <div className="bg-black text-white rounded-[32px] p-6 sm:p-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 relative overflow-hidden shadow-xl shadow-black/10">
            {/* Abstract Design Elements */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#00D2BA] rounded-full blur-[80px] opacity-20 translate-x-1/3 -translate-y-1/3 pointer-events-none" />

            <div className="relative z-10 space-y-2">
              <h2 className="text-2xl sm:text-3xl font-bold">New Translation</h2>
              <p className="text-gray-400 max-w-md">Upload a document or select from your Diia archive to get an official translation.</p>
            </div>
            <div className="relative z-10 w-full sm:w-auto">
              <Button
                variant="primary"
                className="bg-gradient-to-r from-[#D4F4E4] to-[#E3D4F4] !text-black hover:from-[#C4E4D4] hover:to-[#D3C4E4] shadow-lg w-full sm:w-auto"
                onClick={() => setView('upload')}
                icon={Plus}
              >
                Start Request
              </Button>
            </div>
          </div>

          {/* Filter / Status Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-2">
            {[
              { label: 'All Documents', value: 'all' },
              { label: 'Processing', value: 'processing' },
              { label: 'Completed', value: 'completed' },
              { label: 'Failed', value: 'failed' }
            ].map((tab) => (
              <button
                key={tab.value}
                onClick={() => setFilterStatus(tab.value)}
                className={`whitespace-nowrap px-6 py-2.5 rounded-full text-sm font-bold transition-colors ${
                  filterStatus === tab.value
                  ? 'bg-black text-white'
                  : 'bg-white text-gray-500 hover:bg-gray-100 border border-transparent'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Document Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents
              .filter((doc) => {
                if (filterStatus === 'all') return true;
                return doc.status === filterStatus;
              })
              .map((doc) => (
                <DocumentCard key={doc.id} doc={doc} onClick={() => handleOpenDoc(doc)} />
              ))}
          </div>
        </main>

        {/* Mobile FAB */}
        <div className="fixed bottom-6 right-6 sm:hidden z-50">
          <button
            onClick={() => setView('upload')}
            className="w-16 h-16 bg-black text-white rounded-full flex items-center justify-center shadow-2xl shadow-black/30 active:scale-90 transition-transform"
          >
            <Plus size={28} />
          </button>
        </div>
      </div>
    );
  }

  /* --- VIEW: UPLOAD / CREATE ---
  */
  if (view === 'upload') {
    return (
      <UploadView
        onBack={goDashboard}
        onComplete={async () => {
          await loadDocuments();
          setView('dashboard');
        }}
      />
    );
  }

  /* --- VIEW: DETAIL / SPLIT VIEW ---
  */
  if (view === 'detail' && selectedDoc) {
    return (
      <DocumentDetailView
        doc={selectedDoc}
        onBack={goDashboard}
      />
    );
  }

  return null;
}

/* --- SUB-COMPONENT: DOCUMENT CARD ---
*/
const DocumentCard = ({ doc, onClick }) => {
  const isCompleted = doc.status === 'completed';
  const isFailed = doc.status === 'failed';
  const isProcessing = doc.status === 'processing';

  // Determine styling based on status
  const getStatusStyles = () => {
    if (isCompleted) {
      return {
        bg: 'bg-[#D4F4E4]',
        text: 'text-[#008F7E]',
        icon: <FileCheck size={24} />,
        label: 'Done'
      };
    }
    if (isFailed) {
      return {
        bg: 'bg-[#FFE5E5]',
        text: 'text-[#DC2626]',
        icon: <XCircle size={24} />,
        label: 'Failed'
      };
    }
    return {
      bg: 'bg-[#FFF4CB]',
      text: 'text-[#B88E00]',
      icon: <Loader2 size={24} className="animate-spin-slow" />,
      label: 'Processing'
    };
  };

  const statusStyles = getStatusStyles();

  return (
    <div
      onClick={onClick}
      className="group bg-white rounded-[24px] p-5 cursor-pointer border border-transparent hover:border-black/5 hover:shadow-xl hover:shadow-black/5 transition-all duration-300 active:scale-[0.99]"
    >
      <div className="flex justify-between items-start mb-4">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${statusStyles.bg} ${statusStyles.text}`}>
          {statusStyles.icon}
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-bold ${statusStyles.bg} ${statusStyles.text}`}>
          {statusStyles.label}
        </div>
      </div>

      <div className="space-y-1 mb-4">
        <h3 className="font-bold text-lg leading-tight group-hover:text-black/80">{doc.title}</h3>
        <p className="text-sm text-gray-400">{doc.type} • {doc.date}</p>
      </div>

      <div className="flex items-center gap-2 text-xs font-bold text-gray-500 bg-[#F5F5F7] p-3 rounded-xl">
        <span>{doc.originalLang}</span>
        <ChevronRight size={14} className="text-gray-300" />
        <span className={isCompleted ? 'text-black' : 'text-gray-400'}>
          {doc.targetLang}
        </span>
      </div>
    </div>
  );
};

/* --- SUB-COMPONENT: CAMERA CAPTURE ---
*/
const CameraCapture = ({ onCapture, onClose }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [error, setError] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // 'user' for front camera, 'environment' for back

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, [facingMode]);

  const startCamera = async () => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      console.error('Camera error:', err);
      setError('Unable to access camera. Please check permissions.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  };

  const switchCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  const capturePhoto = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    setCapturing(true);

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob
    canvas.toBlob((blob) => {
      if (blob) {
        // Create a File object from the blob
        const file = new File([blob], `scan_${Date.now()}.jpg`, {
          type: 'image/jpeg',
          lastModified: Date.now()
        });

        stopCamera();
        onCapture(file);
      }
      setCapturing(false);
    }, 'image/jpeg', 0.95);
  };

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/50 to-transparent p-4 flex items-center justify-between">
        <button
          onClick={() => {
            stopCamera();
            onClose();
          }}
          className="p-2 text-white hover:bg-white/20 rounded-full transition-colors"
        >
          <X size={24} />
        </button>
        <span className="text-white font-bold">Scan Document</span>
        <button
          onClick={switchCamera}
          className="p-2 text-white hover:bg-white/20 rounded-full transition-colors"
        >
          <RotateCw size={24} />
        </button>
      </div>

      {/* Camera View */}
      <div className="flex-1 relative overflow-hidden">
        {error ? (
          <div className="absolute inset-0 flex items-center justify-center text-white text-center p-6">
            <div className="space-y-4">
              <Camera size={48} className="mx-auto opacity-50" />
              <p className="text-lg">{error}</p>
              <button
                onClick={() => {
                  stopCamera();
                  onClose();
                }}
                className="px-6 py-3 bg-white text-black rounded-full font-bold"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />
            <canvas ref={canvasRef} className="hidden" />

            {/* Document Frame Overlay */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="relative w-full h-full">
                <div className="absolute top-4 left-4 w-12 h-12 border-t-4 border-l-4 border-white" />
                <div className="absolute top-4 right-4 w-12 h-12 border-t-4 border-r-4 border-white" />
                <div className="absolute bottom-24 left-4 w-12 h-12 border-b-4 border-l-4 border-white" />
                <div className="absolute bottom-24 right-4 w-12 h-12 border-b-4 border-r-4 border-white" />
              </div>
            </div>
          </>
        )}
      </div>

      {/* Capture Button */}
      {!error && (
        <div className="absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-black/50 to-transparent p-8 flex flex-col items-center gap-4">
          <p className="text-white text-sm text-center">Position the document within the frame</p>
          <button
            onClick={capturePhoto}
            disabled={capturing}
            className="w-20 h-20 rounded-full bg-white border-4 border-white/30 flex items-center justify-center active:scale-90 transition-transform disabled:opacity-50"
          >
            {capturing ? (
              <Loader2 className="animate-spin text-black" size={32} />
            ) : (
              <div className="w-16 h-16 rounded-full bg-white border-4 border-black" />
            )}
          </button>
        </div>
      )}
    </div>
  );
};

/* --- SUB-VIEW: UPLOAD ---
*/
const UploadView = ({ onBack, onComplete }) => {
  const [step, setStep] = useState(1); // 1: Select File, 2: Select Language, 3: Review
  const [file, setFile] = useState(null);
  const [selectedLang, setSelectedLang] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setStep(2);
    }
  };

  const handleCameraCapture = (capturedFile) => {
    setFile(capturedFile);
    setShowCamera(false);
    setStep(2);
  };

  const openCamera = () => {
    setShowCamera(true);
  };

  const handleSubmit = async () => {
    setIsUploading(true);
    setUploadError(null);

    try {
      // Step 1: Upload file directly to backend
      const uploadData = await uploadFile(file, 'custom_upload');

      // Step 2: Notify backend to start processing
      await startProcessing(uploadData.request_id);

      // Step 3: Complete and reload documents
      onComplete();
    } catch (err) {
      console.error('Upload error:', err);
      setUploadError(err.message || 'Failed to upload document. Please try again.');
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col font-sans">
      {/* Camera Capture Modal */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}

      {/* Header */}
      <div className="h-16 flex items-center px-4 border-b border-gray-100">
        <button onClick={onBack} className="p-2 -ml-2 hover:bg-gray-100 rounded-full">
          <ArrowLeft size={24} />
        </button>
        <div className="ml-2 font-bold text-lg">New Translation</div>
      </div>

      <main className="flex-1 max-w-2xl w-full mx-auto p-6 flex flex-col">
        {/* Progress Stepper */}
        <div className="flex items-center justify-between mb-8 px-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                step >= s ? 'bg-black text-white' : 'bg-gray-100 text-gray-400'
              }`}>
                {s}
              </div>
              {s !== 3 && <div className={`w-12 h-1 mx-2 rounded-full ${step > s ? 'bg-black' : 'bg-gray-100'}`} />}
            </div>
          ))}
        </div>

        <div className="flex-1 flex flex-col items-center justify-center animate-in fade-in slide-in-from-bottom-4 duration-500">

          {/* STEP 1: FILE */}
          {step === 1 && (
            <div className="w-full text-center space-y-6">
              <h2 className="text-2xl font-bold">Select Document</h2>

              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".pdf,.jpg,.jpeg,.png"
                className="hidden"
              />

              <div
                className="w-full h-64 border-2 border-dashed border-gray-300 rounded-[32px] flex flex-col items-center justify-center gap-4 bg-[#F5F5F7] hover:bg-gray-50 hover:border-black transition-colors cursor-pointer group"
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform">
                  <Upload size={24} className="text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="font-bold text-lg">Tap to upload</p>
                  <p className="text-sm text-gray-400">PDF, JPG or PNG up to 10MB</p>
                </div>
              </div>

              {uploadError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {uploadError}
                </div>
              )}

              <div className="relative">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200"></div></div>
                <div className="relative flex justify-center text-sm"><span className="px-2 bg-white text-gray-500">Or import from</span></div>
              </div>

              <Button variant="secondary" className="w-full" icon={ScanLine} onClick={openCamera}>
                Scan with Camera
              </Button>
            </div>
          )}

          {/* STEP 2: LANGUAGE */}
          {step === 2 && (
            <div className="w-full space-y-6">
              <h2 className="text-2xl font-bold text-center">Choose Target Language</h2>
              <div className="space-y-3">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => { setSelectedLang(lang); setStep(3); }}
                    className="w-full p-4 rounded-2xl bg-[#F5F5F7] hover:bg-black/5 flex items-center justify-between group transition-all"
                  >
                    <div className="flex items-center gap-4">
                      <span className="text-2xl">{lang.flag}</span>
                      <span className="font-bold text-lg">{lang.name}</span>
                    </div>
                    <div className="w-6 h-6 rounded-full border-2 border-gray-300 group-hover:border-black" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* STEP 3: REVIEW */}
          {step === 3 && (
            <div className="w-full space-y-8">
               {isUploading ? (
                 <div className="flex flex-col items-center justify-center py-20 space-y-6">
                   <div className="relative">
                     <div className="w-20 h-20 border-4 border-gray-100 border-t-black rounded-full animate-spin" />
                     <div className="absolute inset-0 flex items-center justify-center font-bold text-xs">DIYA</div>
                   </div>
                   <h3 className="font-bold text-xl">Uploading securely...</h3>
                 </div>
               ) : (
                 <>
                  <h2 className="text-2xl font-bold text-center">Summary</h2>

                  <div className="bg-[#F5F5F7] p-6 rounded-[24px] space-y-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-gray-500">
                        <FileText size={24} />
                      </div>
                      <div className="flex-1">
                        <p className="font-bold">{file?.name}</p>
                        <p className="text-sm text-gray-400">
                          {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Unknown size'}
                        </p>
                      </div>
                    </div>
                    <div className="h-px bg-gray-200" />
                    <div className="flex justify-between items-center">
                      <span className="text-gray-500 font-medium">Translate to</span>
                      <span className="font-bold flex items-center gap-2">
                        {selectedLang?.flag} {selectedLang?.name}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-500 font-medium">Estimated Time</span>
                      <span className="font-bold">~24 Hours</span>
                    </div>
                  </div>

                  {uploadError && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                      {uploadError}
                    </div>
                  )}

                  <div className="fixed bottom-0 left-0 w-full p-6 bg-white border-t border-gray-100">
                    <Button onClick={handleSubmit} className="w-full">
                      Confirm & Send
                    </Button>
                  </div>
                 </>
               )}
            </div>
          )}

        </div>
      </main>
    </div>
  );
};

/* --- SUB-VIEW: DOCUMENT DETAIL (SPLIT VIEW) ---
*/
const DocumentDetailView = ({ doc, onBack }) => {
  const [viewMode, setViewMode] = useState('split'); // 'split', 'original', 'translated'
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  const [originalPdfUrl, setOriginalPdfUrl] = useState(null);
  const [translatedPdfUrl, setTranslatedPdfUrl] = useState(null);
  const [loadingPdfs, setLoadingPdfs] = useState(true);

  // Fetch PDFs with authentication and create blob URLs
  useEffect(() => {
    const fetchPdfs = async () => {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const credential = localStorage.getItem('google_credential');

      if (!credential) {
        console.error('Not authenticated');
        setLoadingPdfs(false);
        return;
      }

      try {
        // Fetch original PDF
        if (doc.originalPdf) {
          const originalResponse = await fetch(`${API_URL}/api${doc.originalPdf}`, {
            headers: { 'Authorization': `Bearer ${credential}` },
          });
          if (originalResponse.ok) {
            const blob = await originalResponse.blob();
            const url = window.URL.createObjectURL(blob);
            setOriginalPdfUrl(url);
          }
        }

        // Fetch translated PDF if available
        if (doc.translatedPdf && doc.status === 'completed') {
          const translatedResponse = await fetch(`${API_URL}/api${doc.translatedPdf}`, {
            headers: { 'Authorization': `Bearer ${credential}` },
          });
          if (translatedResponse.ok) {
            const blob = await translatedResponse.blob();
            const url = window.URL.createObjectURL(blob);
            setTranslatedPdfUrl(url);
          }
        }
      } catch (err) {
        console.error('Error fetching PDFs:', err);
      } finally {
        setLoadingPdfs(false);
      }
    };

    fetchPdfs();

    // Cleanup: revoke blob URLs when component unmounts
    return () => {
      if (originalPdfUrl) window.URL.revokeObjectURL(originalPdfUrl);
      if (translatedPdfUrl) window.URL.revokeObjectURL(translatedPdfUrl);
    };
  }, [doc]);

  const handleDownload = async () => {
    try {
      // Download the translated document if available, otherwise the original
      const downloadUrl = doc.translatedPdf || doc.originalPdf;
      if (!downloadUrl) {
        alert('Download URL not available');
        return;
      }

      const credential = localStorage.getItem('google_credential');
      if (!credential) {
        alert('Not authenticated. Please log in.');
        return;
      }

      // Fetch the file with authentication
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api${downloadUrl}`, {
        headers: {
          'Authorization': `Bearer ${credential}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download file');
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${doc.title}_${doc.status === 'completed' ? doc.targetLang : 'original'}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
      alert('Failed to download file. Please try again.');
    }
  };

  return (
    <div className="h-screen flex flex-col bg-[#F5F5F7] font-sans text-black">
      {/* Header */}
      <div className="bg-white h-16 sm:h-20 px-4 flex items-center justify-between border-b border-gray-200 shrink-0 z-20">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 -ml-2 hover:bg-gray-100 rounded-full">
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="font-bold text-lg sm:text-xl leading-none">{doc.title}</h1>
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
              <span className={`w-2 h-2 rounded-full ${
                doc.status === 'completed' ? 'bg-[#00D2BA]' :
                doc.status === 'failed' ? 'bg-red-500' :
                'bg-yellow-400'
              }`} />
              {doc.status === 'completed' ? 'Signed & Verified' :
               doc.status === 'failed' ? 'Translation Failed' :
               'Processing'}
            </div>
          </div>
        </div>
        <Button variant="secondary" onClick={handleDownload} className="hidden sm:flex py-2 px-4 text-sm" icon={Download}>
          Download PDF
        </Button>
        <button onClick={handleDownload} className="sm:hidden p-2 bg-black text-white rounded-full">
          <Download size={20} />
        </button>
      </div>

      {/* Toolbar (Mobile) */}
      <div className="sm:hidden bg-white px-4 py-2 border-b border-gray-200 flex justify-center">
        <div className="flex bg-[#F5F5F7] p-1 rounded-lg">
          {['original', 'translated'].map(m => (
            <button
              key={m}
              onClick={() => setViewMode(m)}
              className={`px-6 py-2 rounded-md text-sm font-bold capitalize transition-all ${
                viewMode === m ? 'bg-white shadow-sm text-black' : 'text-gray-400'
              }`}
              disabled={m === 'translated' && doc.status !== 'completed'}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden relative flex justify-center p-0 sm:p-6 gap-6">

        {/* ORIGINAL DOC */}
        <div
          className={`
            bg-white shadow-sm sm:rounded-2xl overflow-hidden flex flex-col w-full max-w-2xl
            ${isMobile && viewMode !== 'original' ? 'hidden' : 'flex'}
            ${!isMobile && 'flex-1'}
          `}
        >
          <div className="h-10 bg-gray-50 border-b flex items-center justify-between px-4 shrink-0">
             <span className="font-mono text-xs uppercase tracking-widest text-gray-500">Original • {doc.originalLang}</span>
             <Maximize2 size={14} className="text-gray-400" />
          </div>
          <div className="flex-1 bg-gray-100 relative">
            {loadingPdfs ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="animate-spin text-gray-400" size={40} />
              </div>
            ) : originalPdfUrl ? (
              <iframe
                src={`${originalPdfUrl}#toolbar=0&navpanes=0&scrollbar=0&view=FitH`}
                className="w-full h-full border-none"
                title="Original Document PDF"
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                Failed to load document
              </div>
            )}
          </div>
        </div>

        {/* TRANSLATED DOC */}
        <div
          className={`
            bg-white shadow-lg shadow-blue-900/5 sm:rounded-2xl overflow-hidden flex flex-col w-full max-w-2xl
            ${isMobile && viewMode !== 'translated' ? 'hidden' : 'flex'}
            ${!isMobile && 'flex-1'}
            ${doc.status !== 'completed' ? 'items-center justify-center bg-gray-50' : ''}
          `}
        >
          {doc.status === 'completed' ? (
            <>
              <div className="h-10 bg-[#D4F4E4]/30 border-b border-[#D4F4E4] flex items-center justify-between px-4 shrink-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs uppercase tracking-widest font-bold text-[#008F7E]">Translation • {doc.targetLang}</span>
                  <div className="flex items-center gap-1 bg-[#D4F4E4] px-1.5 py-0.5 rounded text-[10px] font-bold text-[#008F7E]">
                    <Check size={10} /> VALID
                  </div>
                </div>
                <Maximize2 size={14} className="text-[#008F7E]" />
              </div>
              <div className="flex-1 bg-gray-100 relative">
                {loadingPdfs ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="animate-spin text-gray-400" size={40} />
                  </div>
                ) : translatedPdfUrl ? (
                  <iframe
                    src={`${translatedPdfUrl}#toolbar=0&navpanes=0&scrollbar=0&view=FitH`}
                    className="w-full h-full border-none"
                    title="Translated Document PDF"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400">
                    Failed to load translated document
                  </div>
                )}
              </div>
            </>
          ) : doc.status === 'failed' ? (
            <div className="text-center space-y-4 p-8">
              <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto">
                <XCircle size={40} className="text-red-500" />
              </div>
              <h3 className="font-bold text-xl text-red-600">Translation Failed</h3>
              <p className="text-gray-500 text-sm max-w-xs mx-auto">
                An error occurred while processing this document. Please try uploading it again or contact support if the issue persists.
              </p>
            </div>
          ) : (
            <div className="text-center space-y-4 p-8">
              <Loader2 size={40} className="animate-spin mx-auto text-gray-400" />
              <h3 className="font-bold text-xl">Translation in Progress</h3>
              <p className="text-gray-500 text-sm max-w-xs mx-auto">
                Our certified translators are working on this document. You will be notified when it is ready.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};