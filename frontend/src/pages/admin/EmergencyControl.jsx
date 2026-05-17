import { useState, useEffect } from 'react';
import { AlertTriangle, Activity, Users, Shield, Phone, FileText } from 'lucide-react';
import StatCard from '../../components/StatCard';
import Navbar from '../../components/Navbar.jsx';
import {
  getAdminEmergencyAlerts,
  getAdminEmergencyProtocols,
  getAdminEmergencyContacts,
  getAdminEmergencyIncidents,
  getAdminEmergencyPredictions,
  acknowledgeEmergencyPrediction,
} from '../../api/index.js';

export default function EmergencyControl() {
  const [alerts, setAlerts] = useState([]);
  const [protocols, setProtocols] = useState({});
  const [contacts, setContacts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEmergencyData();
  }, []);

  const fetchEmergencyData = async () => {
    try {
      const [alertsRes, protocolsRes, contactsRes, incidentsRes, predictionsRes] = await Promise.all([
        getAdminEmergencyAlerts(),
        getAdminEmergencyProtocols(),
        getAdminEmergencyContacts(),
        getAdminEmergencyIncidents(),
        getAdminEmergencyPredictions(),
      ]);
      setAlerts(alertsRes.data.alerts || []);
      setProtocols(protocolsRes.data.protocols || {});
      setContacts(contactsRes.data.contacts || []);
      setIncidents(incidentsRes.data.incidents || []);
      setPredictions(predictionsRes.data.predictions || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching emergency data:', error);
      setLoading(false);
    }
  };

  const handleAcknowledgePrediction = async (patientId) => {
    try {
      await acknowledgeEmergencyPrediction(patientId);
      // Optimistically update
      setPredictions(prev => prev.map(p => p.patient_id === patientId ? { ...p, acknowledged: true } : p));
    } catch (error) {
      console.error('Failed to acknowledge prediction:', error);
    }
  };

  const getAlertColor = (level) => {
    const colors = {
      critical: 'bg-red-100 border-red-500 text-red-800',
      high: 'bg-orange-100 border-orange-500 text-orange-800',
      medium: 'bg-yellow-100 border-yellow-500 text-yellow-800',
      low: 'bg-blue-100 border-blue-500 text-blue-800',
    };
    return colors[level] || colors.low;
  };

  const getAlertIcon = (type) => {
    const icons = {
      surge: AlertTriangle,
      capacity: Activity,
      staffing: Users,
      equipment: Shield,
    };
    return icons[type] || AlertTriangle;
  };

  const activateProtocol = (protocolType) => {
    if (confirm(`Are you sure you want to activate the ${protocolType} protocol?`)) {
      console.log(`Activating ${protocolType} protocol...`);
      // In a real app, this would trigger the protocol activation
      alert(`${protocolType} protocol activated!`);
    }
  };

  const acknowledgeAlert = (alertId) => {
    console.log(`Acknowledging alert ${alertId}`);
    setAlerts(alerts.filter(alert => alert.id !== alertId));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading emergency control panel...</div>
      </div>
    );
  }

  const activeAlerts = alerts.filter(a => a.status === 'active');
  const criticalAlerts = activeAlerts.filter(a => a.level === 'critical');

  return (
    <div className="space-y-6">
      <Navbar title="Emergency Control" subtitle="Emergency Management" />

      {/* Protocol Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => activateProtocol('surge')}
          className="px-4 py-2 bg-orange-600 text-white rounded-xl hover:bg-orange-700 text-sm font-semibold"
        >
          Activate Surge Protocol
        </button>
        <button
          onClick={() => activateProtocol('mass_casualty')}
          className="px-4 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 text-sm font-semibold"
        >
          Mass Casualty Protocol
        </button>
      </div>

      {/* Auto-Alert for Critical Unacknowledged Predictions */}
      {predictions.some(p => p.risk_level === 'Critical' && !p.acknowledged) && (
        <div className="bg-red-600 text-white px-6 py-4 rounded-xl shadow-lg flex items-center justify-between animate-pulse">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8" />
            <div>
              <h3 className="font-bold text-lg">AI CRITICAL ALERT</h3>
              <p>One or more patients are predicted to have a critical deterioration in vitals. Immediate doctor action required.</p>
            </div>
          </div>
        </div>
      )}

      {/* Predictive Risk Analysis */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-600" />
          Predictive Risk Analysis (AI)
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="p-3 font-semibold text-slate-700 rounded-tl-lg">Patient</th>
                <th className="p-3 font-semibold text-slate-700">Latest Vitals</th>
                <th className="p-3 font-semibold text-slate-700">AI Risk Level</th>
                <th className="p-3 font-semibold text-slate-700">Reasoning</th>
                <th className="p-3 font-semibold text-slate-700 rounded-tr-lg">Action</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map((p) => {
                const latest = p.vitals_history[p.vitals_history.length - 1];
                return (
                  <tr key={p.patient_id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="p-3 font-medium text-slate-900">{p.patient_name}</td>
                    <td className="p-3 text-slate-600">
                      HR: {latest.heart_rate} | BP: {latest.blood_pressure_sys}/{latest.blood_pressure_dia} | SpO2: {latest.spo2}%
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold \${
                        p.risk_level === 'Critical' ? 'bg-red-100 text-red-800 border border-red-200' :
                        p.risk_level === 'High' ? 'bg-orange-100 text-orange-800 border border-orange-200' :
                        p.risk_level === 'Moderate' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                        'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      }`}>
                        {p.risk_level} ({p.risk_score}/100)
                      </span>
                    </td>
                    <td className="p-3 text-slate-600 max-w-xs truncate" title={p.anomaly_reason}>
                      {p.anomaly_reason}
                    </td>
                    <td className="p-3">
                      {p.risk_level === 'Critical' && !p.acknowledged ? (
                        <button
                          onClick={() => handleAcknowledgePrediction(p.patient_id)}
                          className="px-3 py-1 bg-red-600 text-white rounded-md text-xs font-semibold hover:bg-red-700 transition"
                        >
                          Acknowledge
                        </button>
                      ) : p.acknowledged ? (
                        <span className="text-slate-400 text-xs italic">Acknowledged</span>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          label="Active Alerts"
          value={activeAlerts.length}
          icon={AlertTriangle}
          accent="text-orange-600"
        />
        <StatCard
          label="Critical Alerts"
          value={criticalAlerts.length}
          icon={Activity}
          accent="text-red-600"
        />
        <StatCard
          label="Emergency Contacts"
          value={contacts.length}
          icon={Phone}
          accent="text-blue-600"
        />
        <StatCard
          label="Recent Incidents"
          value={incidents.length}
          icon={FileText}
          accent="text-purple-600"
        />
      </div>

      {/* Active Alerts */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-600" />
          Active Alerts
        </h2>
        {activeAlerts.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No active alerts</p>
        ) : (
          <div className="space-y-4">
            {activeAlerts.map((alert) => {
              const Icon = getAlertIcon(alert.type);
              return (
                <div
                  key={alert.id}
                  className={`border-l-4 p-4 rounded-lg ${getAlertColor(alert.level)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <Icon className="w-6 h-6 mt-1" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{alert.title}</h3>
                          <span className="text-xs px-2 py-1 bg-white rounded-full">
                            {alert.level.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm mb-2">{alert.description}</p>
                        <div className="text-xs space-y-1">
                          <p><strong>Department:</strong> {alert.department}</p>
                          <p><strong>Time:</strong> {new Date(alert.timestamp).toLocaleString()}</p>
                          {alert.affected_areas && (
                            <p><strong>Affected Areas:</strong> {alert.affected_areas.join(', ')}</p>
                          )}
                        </div>
                        {alert.recommended_actions && alert.recommended_actions.length > 0 && (
                          <div className="mt-3">
                            <p className="text-sm font-semibold mb-1">Recommended Actions:</p>
                            <ul className="text-sm list-disc list-inside space-y-1">
                              {alert.recommended_actions.map((action, idx) => (
                                <li key={idx}>{action}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => acknowledgeAlert(alert.id)}
                      className="ml-4 px-3 py-1 bg-white text-gray-700 rounded hover:bg-gray-100 text-sm"
                    >
                      Acknowledge
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Emergency Protocols */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-600" />
          Emergency Protocols
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(protocols).map(([key, protocol]) => (
            <div key={key} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <h3 className="font-semibold mb-2">{protocol.name}</h3>
              <p className="text-sm text-gray-600 mb-3">
                Activation time: {protocol.estimated_activation_time}
              </p>
              <div className="text-sm mb-3">
                <p className="font-medium mb-1">Steps:</p>
                <ol className="list-decimal list-inside space-y-1 text-gray-700">
                  {protocol.steps.slice(0, 3).map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                  {protocol.steps.length > 3 && (
                    <li className="text-gray-500">+{protocol.steps.length - 3} more steps</li>
                  )}
                </ol>
              </div>
              <button
                onClick={() => activateProtocol(key)}
                className="w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
              >
                Activate Protocol
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Emergency Contacts */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Phone className="w-5 h-5 text-green-600" />
          Emergency Contacts
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {contacts.map((contact, idx) => (
            <div key={idx} className="border rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{contact.name}</h3>
                  <p className="text-sm text-gray-600">{contact.role}</p>
                  <div className="mt-2 space-y-1 text-sm">
                    <p><strong>Phone:</strong> {contact.phone}</p>
                    <p><strong>Email:</strong> {contact.email}</p>
                    <p><strong>Availability:</strong> {contact.availability}</p>
                  </div>
                </div>
                <button className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm">
                  Call
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Incidents */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-purple-600" />
          Recent Incidents
        </h2>
        {incidents.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No recent incidents</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-semibold">Date</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">Type</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">Description</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">Severity</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">Patients</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {incidents.map((incident) => (
                  <tr key={incident.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{incident.date}</td>
                    <td className="px-4 py-3 text-sm capitalize">{incident.type.replace('_', ' ')}</td>
                    <td className="px-4 py-3 text-sm">{incident.description}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        incident.severity === 'high' ? 'bg-red-100 text-red-800' :
                        incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {incident.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{incident.patients_affected}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs">
                        {incident.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// Made with Bob
