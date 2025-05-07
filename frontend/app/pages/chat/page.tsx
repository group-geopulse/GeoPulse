"use client";

import { useState, useRef } from "react";

export default function ChatPage() {
  const [userInput, setUserInput] = useState("");
  const [chatHistory, setChatHistory] = useState<
    { role: string; message: string; headlines?: string[] }[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const sendMessage = async () => {
    if (!userInput.trim()) return;
    setLoading(true);
    setChatHistory((prev) => [...prev, { role: "user", message: userInput }]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_question: userInput }),
      });
      const data = await res.json();
      setChatHistory((prev) => [
        ...prev,
        { role: "bot", message: data.summary, headlines: data.headlines },
      ]);
      setUserInput(""); // This clears the input field after sending
    } catch {
      setChatHistory((prev) => [
        ...prev,
        { role: "bot", message: "⚠️ Error retrieving response." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleListening = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    if (!recognitionRef.current) {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = "en-US";

      recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = event.results[0][0].transcript;
        setUserInput(transcript);
        setListening(false);
      };

      recognitionRef.current.onerror = () => {
        setListening(false);
      };

      recognitionRef.current.onend = () => {
        setListening(false);
      };
    }

    if (!listening) {
      recognitionRef.current.start();
      setListening(true);
    } else {
      recognitionRef.current.stop();
      setListening(false);
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen overflow-hidden">
      {/* Background Video */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute top-0 left-0 w-full h-full object-cover -z-10 opacity-30"
      >
        <source src="/background_video.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      <h1 className="text-3xl font-bold mb-4 z-10">GeoPulse Chat</h1>
      <div className="w-full max-w-2xl bg-[var(--background)] shadow-md rounded-lg p-4 space-y-4 z-10">
        <div className="h-96 overflow-y-auto border-b border-gray-300 p-2">
          {chatHistory.map((chat, i) => (
            <div
              key={i}
              className={`p-2 ${chat.role === "user" ? "text-right" : "text-left"}`}
            >
              <span
                className={`inline-block px-4 py-2 rounded-lg ${
                  chat.role === "user"
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-black"
                }`}
              >
                {chat.message}
              </span>
              {chat.role === "bot" && Array.isArray(chat.headlines) && chat.headlines.length > 0 && (
                <ul className="mt-2 list-disc list-inside text-sm text-gray-700">
                  {chat.headlines.map((hl, idx) => (
                    <li key={idx}>{hl}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
        <div className="flex items-center space-x-2 pt-2 pl-12">
          <input
            type="text"
            className="flex-grow border p-2 rounded-md text-black"
            placeholder="Ask about oil prices..."
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button
            onClick={toggleListening}
            className={`px-3 py-2 rounded-md ${
              listening ? "bg-red-500" : "bg-gray-300"
            } text-white`}
          >
            🎤
          </button>
          <button
            onClick={sendMessage}
            className="bg-blue-500 text-white px-4 py-2 rounded-md disabled:opacity-50"
            disabled={loading}
          >
            {loading ? "Loading..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );  
}
