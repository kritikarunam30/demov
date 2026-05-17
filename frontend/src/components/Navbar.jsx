import { Bell, UserCircle } from "lucide-react";
import { useContext } from "react";

import { AppContext } from "../context/AppContext.jsx";

const Navbar = ({ title, subtitle, displayName }) => {
  const { activeRole, selectedDoctor, selectedPatient, selectedAdmin } = useContext(AppContext);
  const resolvedName =
    displayName ||
    (activeRole === "doctor" && selectedDoctor?.name) ||
    (activeRole === "patient" && selectedPatient?.name) ||
    (activeRole === "admin" && selectedAdmin?.department) ||
    "Demo User";

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-slate-400">{subtitle}</p>
        <h2 className="text-2xl font-semibold text-black">{title}</h2>
      </div>
      <div className="flex items-center gap-3">
        <button className="h-10 w-10 rounded-full border border-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-900">
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5">
          <UserCircle className="h-5 w-5 text-slate-500" />
          <span className="text-sm text-slate-700">{resolvedName}</span>
        </div>
      </div>
    </div>
  );
};

export default Navbar;
