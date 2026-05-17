import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AppContext } from "../context/AppContext.jsx";
import ParticleCanvas from "../components/ParticleCanvas.jsx";

const WORKSPACE_CARDS = [
  {
    title: "Admin Workspace",
    subtitle: "System Monitoring & Resource Allocation",
    icon: "shield_with_heart",
    features: [
      "Real-time Node Status",
      "Institutional Governance"
    ],
    to: "/admin/login",
    role: "admin",
  },
  {
    title: "Doctor Workspace",
    subtitle: "Diagnostic Intelligence & Clinical Flow",
    icon: "stethoscope",
    iconFilled: true,
    features: [
      "AI-Powered Diagnostics",
      "Patient Record Access"
    ],
    to: "/doctor/login",
    role: "doctor",
  },
  {
    title: "Patient Workspace",
    subtitle: "Personal Health Portal & Telemetry",
    icon: "person_pin_circle",
    features: [
      "Neural Link Health History",
      "AI Health Advisor"
    ],
    to: "/patient/login",
    role: "patient",
  },
];

const Home = () => {
  const navigate = useNavigate();
  const { setActiveRole } = useContext(AppContext);

  const handleSelect = (role, path) => {
    setActiveRole(role);
    navigate(path);
  };

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden font-body-md text-body-md">
      <ParticleCanvas />

      {/* TopAppBar */}
      <header
        id="main-header"
        className="sticky top-0 z-50 flex justify-between items-center w-full px-margin-desktop py-4 bg-surface-bright border-b border-white/5"
      >
        <div className="font-display-lg text-[24px] md:text-display-lg font-bold text-primary tracking-tighter">
          MediFlow OS
        </div>
        <nav className="hidden md:flex items-center gap-gutter">
          <a
            className="text-on-surface-variant font-medium hover:text-surface-tint hover:bg-surface-variant/30 transition-all duration-300 px-3 py-1 rounded-full"
            href="#"
          >
            Workspaces
          </a>
          <a
            className="text-on-surface-variant font-medium hover:text-surface-tint hover:bg-surface-variant/30 transition-all duration-300 px-3 py-1 rounded-full"
            href="#"
          >
            Intelligence
          </a>
          <a
            className="text-on-surface-variant font-medium hover:text-surface-tint hover:bg-surface-variant/30 transition-all duration-300 px-3 py-1 rounded-full"
            href="#"
          >
            Security
          </a>
          <a
            className="text-on-surface-variant font-medium hover:text-surface-tint hover:bg-surface-variant/30 transition-all duration-300 px-3 py-1 rounded-full"
            href="#"
          >
            Network
          </a>
        </nav>
        <div className="flex items-center gap-4">
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-surface-tint transition-all active:scale-95">
            settings
          </span>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-surface-tint transition-all active:scale-95">
            account_circle
          </span>
          <button className="bg-primary-container text-on-primary-container px-6 py-2 rounded-full font-bold hover:scale-105 transition-transform duration-150 active:scale-95">
            Launch OS
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex flex-col items-center justify-end px-margin-desktop relative pb-12 h-[calc(100vh-80px)]">
        {/* Hero Section */}
        <section id="hero-section" className="text-center mb-8 max-w-4xl mt-auto">
          <h1 className="font-display-lg text-display-lg text-primary mb-2">
            MediFlow OS
          </h1>
          <h2 className="font-headline-lg text-headline-lg text-black mb-4">
            Unified Intelligent Healthcare Infrastructure
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl mx-auto opacity-80">
            Connecting patients, doctors, and administrators through one seamless AI-powered
            ecosystem. Precision data management meets cinematic clinical workflow.
          </p>
        </section>

        {/* Workspace Selection UI (Curved Glassmorphic Cards) */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-gutter items-stretch w-full max-w-5xl">
          {WORKSPACE_CARDS.map((card) => (
            <div
              key={card.title}
              onClick={() => handleSelect(card.role, card.to)}
              className="glass-panel p-6 rounded-xl flex flex-col items-center text-center glow-hover transition-all duration-500 cursor-pointer group h-full"
            >
              <div className="w-14 h-14 rounded-full bg-surface-variant flex items-center justify-center mb-4 group-hover:bg-primary-container/20 transition-colors">
                <span
                  className="material-symbols-outlined text-3xl text-primary-container"
                  style={card.iconFilled ? { fontVariationSettings: '"FILL" 1' } : {}}
                >
                  {card.icon}
                </span>
              </div>
              <h3 className="font-headline-lg text-xl text-primary mb-2">{card.title}</h3>
              <p className="font-data-label text-data-label text-on-surface-variant mb-4 uppercase">
                {card.subtitle}
              </p>
              <div className="space-y-2 w-full text-left mt-auto">
                {card.features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-on-secondary-container">
                    <span className="material-symbols-outlined text-sm">check_circle</span>
                    <span className="text-xs font-data-label">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
      </main>

      {/* Footer */}
      <footer className="flex flex-col md:flex-row justify-between items-center px-margin-desktop py-8 gap-gutter bg-surface-container-lowest border-t border-surface-variant/20">
        <div className="flex flex-col gap-1">
          <div className="font-headline-lg text-xl font-semibold text-primary">MediFlow OS</div>
          <p className="text-on-surface-variant font-data-label text-[10px] tracking-widest">
            © 2024 MEDIFLOW OS. SYSTEM STATUS: AI HEARTBEAT ACTIVE
          </p>
        </div>
        <div className="flex gap-gutter">
          <a
            className="text-on-surface-variant font-body-md text-sm hover:text-surface-tint transition-colors"
            href="#"
          >
            Architecture
          </a>
          <a
            className="text-on-surface-variant font-body-md text-sm hover:text-surface-tint transition-colors"
            href="#"
          >
            Privacy Protocol
          </a>
          <a
            className="text-on-surface-variant font-body-md text-sm hover:text-surface-tint transition-colors"
            href="#"
          >
            Neural Link Status
          </a>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-3 h-3 rounded-full bg-primary-container animate-pulse shadow-glow-cyan"></div>
          <span className="font-data-label text-data-label text-primary-container">
            SYSTEMS_NOMINAL
          </span>
        </div>
      </footer>
    </div>
  );
};

export default Home;

// Made with Bob
