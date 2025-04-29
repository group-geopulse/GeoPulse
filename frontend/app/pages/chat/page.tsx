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
      setUserInput("");
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
    <div className="flex flex-col h-screen w-screen bg-gray-100">
      <h1 className="text-3xl font-bold p-4">GeoPulse Chat</h1>
      <div className="flex flex-col flex-1 bg-white shadow-inner rounded-t-lg p-4 mx-4 mb-2">
        <div className="flex-1 overflow-y-auto border-b border-gray-300 p-2">
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
              {chat.role === "bot" && chat.headlines?.length > 0 && (
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
            className="flex-grow border p-2 rounded-md"
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
