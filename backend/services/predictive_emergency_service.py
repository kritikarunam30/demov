import random
from datetime import datetime, timedelta

class PredictiveEmergencyService:
    # A class-level dictionary to simulate a database for acknowledged alerts
    _acknowledged_alerts = set()

    @staticmethod
    def generate_mock_vitals():
        """Generates 6 realistic time-series vital readings for multiple patients"""
        base_time = datetime.utcnow()
        
        patients = [
            {"id": 101, "name": "Vikram Singh", "base_hr": 75, "base_sys": 120, "base_dia": 80, "base_spo2": 98, "trend": "stable"},
            {"id": 102, "name": "Priya Sharma", "base_hr": 85, "base_sys": 130, "base_dia": 85, "base_spo2": 96, "trend": "worsening"},
            {"id": 103, "name": "Arjun Nair", "base_hr": 60, "base_sys": 110, "base_dia": 70, "base_spo2": 99, "trend": "stable"},
            {"id": 104, "name": "Sneha Reddy", "base_hr": 95, "base_sys": 140, "base_dia": 90, "base_spo2": 94, "trend": "critical"}
        ]
        
        results = []
        for p in patients:
            readings = []
            hr = p["base_hr"]
            sys = p["base_sys"]
            dia = p["base_dia"]
            spo2 = p["base_spo2"]
            
            for i in range(6):
                timestamp = base_time - timedelta(minutes=(5 - i) * 15) # 15 min intervals
                
                # Apply trends
                if p["trend"] == "worsening":
                    hr += random.randint(1, 3)
                    sys += random.randint(1, 4)
                    spo2 -= random.uniform(0.2, 0.8)
                elif p["trend"] == "critical":
                    hr += random.randint(3, 7)
                    sys -= random.randint(2, 6) # Dropping BP
                    spo2 -= random.uniform(0.5, 1.5)
                else:
                    hr += random.randint(-2, 2)
                    sys += random.randint(-3, 3)
                    spo2 += random.uniform(-0.5, 0.5)
                
                # Clamp spo2 to realistic values
                spo2 = max(70.0, min(100.0, spo2))
                
                readings.append({
                    "timestamp": timestamp.isoformat(),
                    "heart_rate": int(hr),
                    "blood_pressure_sys": int(sys),
                    "blood_pressure_dia": int(dia),
                    "spo2": round(spo2, 1)
                })
                
            risk_level, score, reason = PredictiveEmergencyService.predict_risk(readings, p["trend"])
            
            results.append({
                "patient_id": p["id"],
                "patient_name": p["name"],
                "vitals_history": readings,
                "risk_score": score,
                "risk_level": risk_level,
                "anomaly_reason": reason,
                "acknowledged": p["id"] in PredictiveEmergencyService._acknowledged_alerts
            })
            
        return results

    @staticmethod
    def predict_risk(readings, trend_category):
        """Mock ML algorithm analyzing vitals variance and trend"""
        latest = readings[-1]
        hr = latest["heart_rate"]
        sys = latest["blood_pressure_sys"]
        spo2 = latest["spo2"]
        
        # Calculate Delta over the 6 readings
        hr_delta = hr - readings[0]["heart_rate"]
        spo2_delta = spo2 - readings[0]["spo2"]
        
        score = 10
        reason = "Stable vitals"
        level = "Stable"
        
        if trend_category == "critical" or spo2 < 90 or hr > 120 or sys < 90:
            level = "Critical"
            score = random.randint(85, 99)
            reason = f"Rapid deterioration: SpO2 dropped by {abs(round(spo2_delta, 1))}%, HR spiked to {hr} bpm"
        elif trend_category == "worsening" or spo2 < 94 or hr > 100:
            level = "High"
            score = random.randint(60, 84)
            reason = "Warning: Sustained elevated heart rate and decreasing SpO2 trend"
        elif abs(hr_delta) > 10 or abs(spo2_delta) > 2:
            level = "Moderate"
            score = random.randint(30, 59)
            reason = "Minor vital fluctuations detected"
        else:
            score = random.randint(5, 29)
            
        return level, score, reason
        
    @staticmethod
    def acknowledge_alert(patient_id: int):
        PredictiveEmergencyService._acknowledged_alerts.add(patient_id)
        return {"success": True, "message": "Alert acknowledged"}
