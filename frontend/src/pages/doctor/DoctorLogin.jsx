import { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getAvailableDoctors, loginAsDoctor } from "../../api/index.js";
import { AppContext } from "../../context/AppContext.jsx";

const DoctorLogin = () => {
  const navigate = useNavigate();
  const { setSelectedDoctor } = useContext(AppContext);
  const [doctors, setDoctors] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    getAvailableDoctors().then((response) => {
      setDoctors(response.data);
      setSelectedId(response.data[0]?.id ?? null);
    });
  }, []);

  const selectedDoctor = useMemo(
    () => doctors.find((doctor) => doctor.id === Number(selectedId)),
    [doctors, selectedId]
  );

  const handleContinue = async () => {
    if (!selectedDoctor) return;

    setIsLoading(true);
    try {
      const response = await loginAsDoctor(selectedDoctor.id);
      setSelectedDoctor(response.data.doctor);
      navigate("/doctor");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden font-body-md text-body-md bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 flex justify-between items-center w-full px-margin-desktop py-4 bg-surface-bright border-b border-white/5">
        <div className="font-display-lg text-[24px] font-bold text-primary tracking-tighter">
          MediFlow OS
        </div>
        <button
          onClick={() => navigate("/")}
          className="text-on-surface-variant hover:text-surface-tint transition-colors text-sm"
        >
          ← Back to Home
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex items-center justify-center px-6 py-12">
        <div className="max-w-5xl w-full grid gap-gutter lg:grid-cols-[1.1fr_0.9fr]">
          {/* Doctor Selection Panel */}
          <div className="glass-panel p-8 rounded-xl">
            <p className="font-data-label text-data-label text-primary-container uppercase tracking-wider">
              Doctor Access
            </p>
            <h1 className="font-headline-lg text-headline-lg text-primary mt-4">
              Choose a doctor profile
            </h1>
            <p className="text-on-surface-variant mt-4 leading-relaxed">
              No password is required. Select a doctor to open the matching dashboard with only that doctor's connected patients, appointments, and prescriptions.
            </p>

            <label className="mt-8 block text-sm text-on-surface-variant">Doctor profile</label>
            <select
              className="mt-3 w-full rounded-xl border border-outline-variant bg-surface-container-low px-4 py-3 text-on-surface outline-none focus:border-primary-container focus:shadow-glow-cyan transition-all"
              value={selectedId ?? ""}
              onChange={(event) => setSelectedId(Number(event.target.value))}
            >
              <option value="" disabled>
                Select a doctor
              </option>
              {doctors.map((doctor) => (
                <option key={doctor.id} value={doctor.id}>
                  {doctor.name} - {doctor.department}
                  {doctor.specialization ? ` (${doctor.specialization})` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Preview Panel */}
          <div className="glass-panel p-8 rounded-xl">
            <p className="font-data-label text-data-label text-on-surface-variant uppercase tracking-wider">
              Preview
            </p>
            <div className="mt-6 rounded-xl bg-gradient-to-br from-primary-container/20 to-secondary-container/10 border border-primary-container/30 p-6">
              <p className="text-sm text-on-surface-variant">Selected doctor</p>
              <h2 className="font-headline-lg text-2xl font-semibold text-black mt-2">
                {selectedDoctor?.name ?? "Select a doctor"}
              </h2>
              <p className="text-on-surface-variant mt-1">
                {selectedDoctor?.department ?? "Department will appear here"}
              </p>
            </div>

            <button
              className="mt-6 w-full rounded-xl bg-primary-container text-on-primary-container py-3.5 font-bold disabled:opacity-50 hover:scale-105 transition-transform duration-150 active:scale-95"
              disabled={!selectedDoctor || isLoading}
              onClick={handleContinue}
            >
              {isLoading ? "Opening dashboard..." : "Open doctor dashboard"}
            </button>

            <p className="text-xs text-on-surface-variant mt-4 leading-relaxed">
              This selection is stored locally so the dashboard and patient workspace stay aligned to the same connected mock record set.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DoctorLogin;

// Made with Bob
