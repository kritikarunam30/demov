import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  if (typeof window === "undefined") {
    return config;
  }

  try {
    const role = JSON.parse(window.localStorage.getItem("mediflow.activeRole") || "null");
    const admin = JSON.parse(window.localStorage.getItem("mediflow.selectedAdmin") || "null");
    const doctor = JSON.parse(window.localStorage.getItem("mediflow.selectedDoctor") || "null");
    const patient = JSON.parse(window.localStorage.getItem("mediflow.selectedPatient") || "null");
    const userId = role === "admin" ? admin?.id : role === "doctor" ? doctor?.id : role === "patient" ? patient?.id : null;

    if (role && userId) {
      config.headers["X-User-Role"] = role;
      config.headers["X-User-Id"] = String(userId);
    }
  } catch {
    // If localStorage is unavailable, skip headers.
  }

  return config;
});

export const getAdminStats = () => api.get("/api/admin/stats");
export const getAdminQueue = () => api.get("/api/admin/queue");
export const getAdminSurgeForecast = () => api.get("/api/admin/surge-forecast");
export const getSurgeForecastCustom = (days) =>
  api.post("/api/admin/surge-forecast/custom", { days });
export const getAdminLiveMap = () => api.get("/api/admin/live-map");
export const getAdminDepartments = () => api.get("/api/admin/departments");
export const createAdminPatient = (payload) => api.post("/api/admin/patients", payload);
export const createAdminDoctor = (payload) => api.post("/api/admin/doctors", payload);
export const getMedicineInventory = () => api.get("/api/admin/medicine-inventory");
export const getAdminEmergencyAlerts = () => api.get("/api/admin/emergency/alerts");
export const getAdminEmergencyProtocols = () => api.get("/api/admin/emergency/protocols");
export const getAdminEmergencyContacts = () => api.get("/api/admin/emergency/contacts");
export const getAdminEmergencyIncidents = () => api.get("/api/admin/emergency/incidents");
export const getAdminEmergencyPredictions = () => api.get("/api/admin/emergency/predictions");
export const acknowledgeEmergencyPrediction = (patientId) => api.post(`/api/admin/emergency/predictions/${patientId}/acknowledge`);

export const getEmergencyAlerts = () => api.get("/api/admin/emergency/alerts");
export const getEmergencyResources = () => api.get("/api/admin/emergency/resources");
export const escalateAlert = (alertId, level) =>
  api.post("/api/admin/emergency/escalate", { alertId, level });
export const getProtocol = (type) =>
  api.get("/api/admin/emergency/protocol", { params: { type } });

export const getAvailableAdmins = () => api.get("/api/auth/admins");
export const loginAsAdmin = (adminId) => api.get(`/api/auth/admins/${adminId}`);

export const getAvailableDoctors = () => api.get("/api/auth/doctors");
export const loginAsDoctor = (doctorId) => api.get(`/api/auth/doctors/${doctorId}`);

export const getAvailablePatients = (search = "") =>
  api.get("/api/auth/patients", { params: search ? { search } : undefined });
export const loginAsPatient = (patientId) => api.get(`/api/auth/patients/${patientId}`);
export const signupPatient = (payload) => api.post("/api/auth/patients/signup", payload);

export const getAllChat = () => api.get("/api/admin/chat/all");
export const getDepartmentChat = (department) => api.get(`/api/admin/chat/${department}`);
export const sendChatMessage = (department, senderUsername, messageText) =>
  api.post("/api/admin/chat", { department, sender_username: senderUsername, message_text: messageText });

export const getDoctorDashboard = (doctorId) =>
  api.get("/api/doctor/dashboard", { params: doctorId ? { doctor_id: doctorId } : undefined });
export const getDoctorPatients = (doctorId) =>
  api.get("/api/doctor/patients", { params: doctorId ? { doctor_id: doctorId } : undefined });
export const postDoctorScribe = (payload) => api.post("/api/doctor/scribe", payload);
export const getDoctorAppointmentsByStatus = (doctorId) =>
  api.get("/api/doctor/appointments-by-status", { params: doctorId ? { doctor_id: doctorId } : undefined });
export const getDoctorAppointmentsRange = (doctorId, startDate, endDate) =>
  api.get("/api/doctor/appointments-range", {
    params: doctorId
      ? {
          doctor_id: doctorId,
          start_date: startDate,
          end_date: endDate,
        }
      : undefined,
  });
export const updateDoctorAppointmentStatus = (appointmentId, status) =>
  api.put(`/api/doctor/appointment/${appointmentId}/status`, { status });

export const getPatientDashboard = (patientId) =>
  api.get("/api/patient/dashboard", { params: patientId ? { patient_id: patientId } : undefined });
export const getPatientHealthReport = (patientId) =>
  api.get("/api/patient/health-report", { params: patientId ? { patient_id: patientId } : undefined });
export const getPatientAvailableDoctors = () => api.get("/api/patient/doctors");
export const getPatientAvailableSlots = (doctorId, appointmentDate) =>
  api.get("/api/patient/available-slots", {
    params: { doctor_id: doctorId, appointment_date: appointmentDate },
  });
export const postPatientBookAppointment = (payload) => api.post("/api/patient/book-appointment", payload);
export const cancelPatientAppointment = (appointmentId, patientId) =>
  api.post(`/api/patient/appointments/${appointmentId}/cancel`, { patient_id: patientId });
export const reschedulePatientAppointment = (appointmentId, payload) =>
  api.post(`/api/patient/appointments/${appointmentId}/reschedule`, payload);

export default api;
