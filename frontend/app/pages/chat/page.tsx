"use client";

import { useState, useRef, useEffect } from "react";
import { MicrophoneIcon } from "@heroicons/react/24/outline";

type ChatEntry = {
  role: "user" | "bot";
  message: string;
  headlines?: string[];
};

export default function ChatPage() {
  const [userInput, setUserInput] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Initialize SpeechRecognition once
  useEffect(() => {
    if (typeof window === "undefined") return;
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SR) {
      console.warn("Web Speech API not supported in this browser");
      return;
    }

    const recog = new SR() as any;
    recog.continuous = false;
    recog.interimResults = false;
    recog.lang = "en-US";
    recog.maxAlternatives = 1;

    recog.onstart = () => console.log("recognition started");
    recog.onspeechend = () => {
      console.log("speech ended");
      recog.stop();
    };
    recog.onend = () => {
      console.log("recognition ended");
      isListeningRef.current = false;
    };
    recog.onerror = (e: any) => {
      console.error("recog error:", e.error);
      isListeningRef.current = false;
    };
    recog.onresult = (ev: any) => {
      const transcript = ev.results[0][0].transcript as string;
      setUserInput(transcript);
    };

    recognitionRef.current = recog;
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleMicClick = () => {
    if (recognitionRef.current && !isListeningRef.current) {
      isListeningRef.current = true;
      recognitionRef.current.start();
    }
  };

  const sendMessage = async () => {
    if (!userInput.trim()) return;

    setChatHistory((h) => [...h, { role: "user", message: userInput }]);
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_question: userInput }),
      });
      const data = await res.json();

      setChatHistory((h) => [
        ...h,
        { role: "bot", message: data.summary, headlines: data.headlines },
      ]);
    } catch {
      setChatHistory((h) => [
        ...h,
        { role: "bot", message: "⚠️ Error retrieving response." },
      ]);
    } finally {
      setUserInput("");
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="flex-none bg-white border-b px-6 py-4 shadow-sm">
        <h1 className="text-xl font-semibold">GeoPulse Chat</h1>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {chatHistory.map((c, i) => (
          <div
            key={i}
            className={`flex ${
              c.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[70%] px-4 py-2 rounded-lg ${
                c.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-800"
              }`}
            >
              {c.message}
              {c.role === "bot" && c.headlines?.length > 0 && (
                <ul className="mt-2 list-disc list-inside text-sm text-gray-700">
                  {c.headlines.map((hl, idx) => (
                    <li key={idx}>{hl}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </main>

      {/* Input + Mic + Send */}
      <footer className="flex-none bg-white border-t pl-12 px-6 py-4 flex items-center space-x-2">
        <textarea
          rows={1}
          className="flex-grow resize-none border rounded-md px-4 py-2 focus:outline-none focus:ring focus:border-blue-300"
          placeholder="Ask about oil prices..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
        />

        {/* Dictate button */}
        <button
          onClick={handleMicClick}
          className="p-2 rounded hover:bg-gray-100 cursor-pointer"
          title="Dictate"
          aria-label="Dictate"
        >
          <MicrophoneIcon className="h-6 w-6 text-gray-600 hover:text-blue-600" />
        </button>

        {/* Send button */}
        <button
          onClick={sendMessage}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-md disabled:opacity-50"
        >
          {loading ? "…" : "Send"}
        </button>
      </footer>
    </div>
  );
}
