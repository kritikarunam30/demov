import { useState, useRef, useEffect } from "react";
import Navbar from "../../components/Navbar.jsx";
import { postDoctorScribe } from "../../api/index.js";

const AIScribe = () => {
  const [transcript, setTranscript] = useState("");
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mode, setMode] = useState("text"); // "text" or "audio"
  const [audioMode, setAudioMode] = useState("realtime"); // "realtime" or "upload"
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const wsRef = useRef(null);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);



  const startRecording = async () => {
    try {
      setTranscript("");

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      });
      streamRef.current = stream;

      if (audioMode === "realtime") {
        // WebSocket real-time transcription
        startWebSocketRecording(stream);
      } else {
        // Record for later upload
        startLocalRecording(stream);
      }

      setIsRecording(true);
      setIsPaused(false);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const startWebSocketRecording = (stream) => {
    // Connect to WebSocket
    const clientId = `client_${Date.now()}`;
    const ws = new WebSocket(`ws://localhost:8000/api/ws/scribe/${clientId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "transcript_final") {
        console.log("Received final transcript from WebSocket");
        setTranscript(data.transcript);
        generateFromTranscript(data.transcript);
      } else if (data.type === "error") {
        console.error("WebSocket error:", data.message);
        alert(`Transcription error: ${data.message}`);
        setIsRecording(false);
      } else if (data.type === "stopped") {
        console.log("WebSocket transcription stopped");
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      alert("WebSocket connection error. Make sure the backend is running.");
    };

    // Set up MediaRecorder to send audio chunks via WebSocket
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm'
    });
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      if (audioMode !== "realtime" || !wsRef.current) {
        return;
      }

      if (audioChunksRef.current.length > 0 && wsRef.current.readyState === WebSocket.OPEN) {
        const completeRecording = new Blob(audioChunksRef.current, { type: "audio/webm" });
        wsRef.current.send(completeRecording);
        wsRef.current.send(JSON.stringify({ command: "stop" }));
      }
    };

    audioChunksRef.current = [];
    mediaRecorder.start(1000); // Collect chunks until stop, then transcribe once
    mediaRecorderRef.current = mediaRecorder;
  };

  const startLocalRecording = (stream) => {
    audioChunksRef.current = [];
    
    const mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.start();
    mediaRecorderRef.current = mediaRecorder;
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "paused") {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    setIsRecording(false);
    setIsPaused(false);
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("audio", file);
    formData.append("patient_name", "Ravi Kumar");
    formData.append("patient_age", "35");

    setIsLoading(true);
    
    try {
      console.log("Uploading audio file:", file.name, file.size, "bytes");
      const response = await fetch("http://localhost:8000/api/doctor/scribe/audio", {
        method: "POST",
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("Audio upload response:", data);
      
      if (data.transcription) {
        setTranscript(data.transcription.formatted_transcript);
        console.log("✓ Transcript set from audio upload");
      }
      
      if (data.notes && data.prescription) {
        setResult({
          notes: data.notes,
          prescription: data.prescription
        });
        console.log("✓ Successfully set result with notes and prescription from audio");
      } else if (!data.notes || !data.prescription) {
        console.warn("Incomplete response - missing notes or prescription:", data);
        alert("Audio processed but notes or prescription generation failed.");
      }
    } catch (error) {
      console.error("Error uploading audio:", error);
      alert(`Error: Failed to process audio file. ${error.message || "Please try again."}`);
    } finally {
      setIsLoading(false);
    }
  };

  const generateFromTranscript = async (sourceTranscript) => {
    const trimmedTranscript = sourceTranscript.trim();
    if (!trimmedTranscript) return;

    setIsLoading(true);
    
    try {
      const response = await postDoctorScribe({ transcript: trimmedTranscript });
      
      if (!response.data) {
        throw new Error("No data in response");
      }
      
      const { notes, prescription, full_prescription } = response.data;
      
      // Validate response
      if (!notes) {
        alert("Error: Server returned no notes.");
        return;
      }
      
      if (!prescription) {
        alert("Error: Server returned no prescription.");
        return;
      }
      
      // Handle prescription - ensure it's an array
      let prescriptionData = prescription;
      
      if (!Array.isArray(prescriptionData)) {
        if (full_prescription && full_prescription.medications) {
          prescriptionData = full_prescription.medications;
        } else {
          prescriptionData = [];
        }
      }
      
      setResult({
        notes,
        prescription: prescriptionData,
        ...response.data
      });
    } catch (error) {
      console.error("Error generating from transcript:", error);
      alert(`Error: Failed to generate notes and prescription.\n\nDetails: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    await generateFromTranscript(transcript);
  };

  const handleCopy = () => {
    if (!result?.notes) return;
    navigator.clipboard.writeText(result.notes);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-8">
      <Navbar title="AI Scribe" subtitle="Consultation Assistant" />

      {/* Mode Selection */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Input Mode</h3>
        <div className="flex gap-4">
          <button
            className={`px-4 py-2 rounded-xl text-sm font-semibold ${
              mode === "text"
                ? "bg-blue-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
            onClick={() => setMode("text")}
          >
            Text Input
          </button>
          <button
            className={`px-4 py-2 rounded-xl text-sm font-semibold ${
              mode === "audio"
                ? "bg-blue-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
            onClick={() => setMode("audio")}
          >
            Audio Recording
          </button>
        </div>

        {mode === "audio" && (
          <div className="mt-4 flex gap-4">
            <button
              className={`px-4 py-2 rounded-xl text-sm font-semibold ${
                audioMode === "realtime"
                  ? "bg-green-600 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
              onClick={() => setAudioMode("realtime")}
            >
              Real-time Transcription
            </button>
            <button
              className={`px-4 py-2 rounded-xl text-sm font-semibold ${
                audioMode === "upload"
                  ? "bg-green-600 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
              onClick={() => setAudioMode("upload")}
            >
              Upload Audio File
            </button>
          </div>
        )}
      </div>

      {/* Patient Info */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-4">
        <div>
          <p className="text-sm text-slate-500">Current consultation</p>
          <h3 className="text-lg font-semibold text-slate-900">Ravi Kumar</h3>
          <p className="text-sm text-slate-600">Age: 35 | Chief complaint: Chest discomfort</p>
        </div>

        {/* Audio Recording Controls */}
        {mode === "audio" && audioMode === "realtime" && (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              {!isRecording ? (
                <button
                  className="px-6 py-3 rounded-xl bg-red-600 text-white text-sm font-semibold hover:bg-red-700 flex items-center gap-2"
                  onClick={startRecording}
                >
                  <span className="w-3 h-3 bg-white rounded-full"></span>
                  Start Recording
                </button>
              ) : (
                <>
                  {!isPaused ? (
                    <button
                      className="px-6 py-3 rounded-xl bg-yellow-600 text-white text-sm font-semibold hover:bg-yellow-700"
                      onClick={pauseRecording}
                    >
                      Pause
                    </button>
                  ) : (
                    <button
                      className="px-6 py-3 rounded-xl bg-green-600 text-white text-sm font-semibold hover:bg-green-700"
                      onClick={resumeRecording}
                    >
                      Resume
                    </button>
                  )}
                  <button
                    className="px-6 py-3 rounded-xl bg-slate-600 text-white text-sm font-semibold hover:bg-slate-700"
                    onClick={stopRecording}
                  >
                    Stop Recording
                  </button>
                  <div className="text-lg font-mono text-slate-700">
                    {formatTime(recordingTime)}
                  </div>
                  {isRecording && !isPaused && (
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></span>
                      <span className="text-sm text-slate-600">Recording...</span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* File Upload */}
        {mode === "audio" && audioMode === "upload" && (
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Upload Audio File
            </label>
            <input
              type="file"
              accept="audio/*"
              onChange={handleFileUpload}
              className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p className="text-xs text-slate-500 mt-2">
              Supported formats: WAV, MP3, FLAC, OGG
            </p>
          </div>
        )}

        {/* Text Input */}
        {mode === "text" && (
          <>
            <div>
              <label className="text-sm font-semibold text-slate-700">
                Conversation transcript
              </label>
              <textarea
                className="mt-2 w-full min-h-[160px] border border-slate-200 rounded-xl p-3 text-sm"
                value={transcript}
                onChange={(event) => setTranscript(event.target.value)}
                placeholder="Enter or paste the consultation transcript here..."
              />
            </div>

            <button
              className="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:bg-slate-300"
              onClick={handleGenerate}
              disabled={isLoading || !transcript}
            >
              {isLoading ? "Generating..." : "Generate Notes & Prescription"}
            </button>
          </>
        )}

        {/* Real-time Transcript Display */}
        {mode === "audio" && audioMode === "realtime" && transcript && (
          <div className="mt-4">
            <label className="text-sm font-semibold text-slate-700">Live Transcript</label>
            <div className="mt-2 w-full min-h-[160px] border border-slate-200 rounded-xl p-3 text-sm bg-slate-50 whitespace-pre-line">
              {transcript || "Transcript will appear here as you speak..."}
            </div>
            {isLoading && (
              <p className="mt-2 text-sm text-slate-500">Generating prescription from transcript...</p>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">SOAP Notes</h3>
              <button
                className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                onClick={handleCopy}
              >
                Copy
              </button>
            </div>
            <textarea
              className="w-full min-h-[200px] text-sm text-slate-600 border border-slate-200 rounded-xl p-3"
              value={result.notes}
              onChange={(e) => setResult({ ...result, notes: e.target.value })}
            />
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Prescription</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-slate-500">
                  <tr>
                    <th className="py-2 font-medium">Medication</th>
                    <th className="py-2 font-medium">Dosage</th>
                    <th className="py-2 font-medium">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(result.prescription) && result.prescription.length > 0 ? (
                    result.prescription.map((item, index) => (
                      <tr key={index} className="border-t border-slate-100">
                        <td className="py-2 text-slate-700">{item.name || item.medication || "-"}</td>
                        <td className="py-2 text-slate-700">{item.dosage || "-"}</td>
                        <td className="py-2 text-slate-700">{item.duration || "-"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr className="border-t border-slate-100">
                      <td colSpan="3" className="py-4 text-center text-slate-500">
                        No medications found in prescription
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIScribe;

// Made with Bob
