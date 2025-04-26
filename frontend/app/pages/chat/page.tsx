"use client";
 
import { useState } from "react";
 
export default function ChatPage() {
 
  const [userInput, setUserInput] = useState("");
 
  const [chatHistory, setChatHistory] = useState<{ role: string; message: string; headlines?: string[] }[]>([]);
 
  const [loading, setLoading] = useState(false);
 
  const sendMessage = async () => {
 
    if (!userInput.trim()) return;
 
    setLoading(true);
 
    setChatHistory((prev) => [...prev, { role: "user", message: userInput }]);
 
    try {
 
      const response = await fetch("/api/chat", {
 
        method: "POST",
 
        headers: { "Content-Type": "application/json" },
 
        body: JSON.stringify({ user_question: userInput }),
 
      });
 
      const data = await response.json();
 
      setChatHistory((prev) => [
 
        ...prev,
 
        { role: "bot", message: data.summary, headlines: data.headlines },
 
      ]);
 
      setUserInput("");
 
    } catch (error) {
 
      setChatHistory((prev) => [
 
        ...prev,
 
        { role: "bot", message: "⚠️ Error retrieving response." },
 
      ]);
 
    } finally {
 
      setLoading(false);
 
    }
 
  };
 
  return (
<div className="flex flex-col items-center justify-center min-h-screen p-4 bg-gray-100">
<h1 className="text-3xl font-bold mb-4">GeoPulse Chat</h1>
 
      <div className="w-full max-w-2xl bg-white shadow-md rounded-lg p-4 space-y-4">
<div className="h-96 overflow-y-auto border-b border-gray-300 p-2">
 
          {chatHistory.map((chat, index) => (
<div key={index} className={`p-2 ${chat.role === "user" ? "text-right" : "text-left"}`}>
<span className={`inline-block px-4 py-2 rounded-lg ${
 
                chat.role === "user" ? "bg-blue-500 text-white" : "bg-gray-200 text-black"
 
              }`}>
 
                {chat.message}
</span>
 
              {chat.role === "bot" && chat.headlines && chat.headlines.length > 0 && (
<ul className="mt-2 list-disc list-inside text-sm text-gray-700">
 
                  {chat.headlines.map((headline, idx) => (
<li key={idx}>{headline}</li>
 
                  ))}
</ul>
 
              )}
</div>
 
          ))}
</div>
 
        <div className="flex items-center space-x-2">
<input
 
            type="text"
 
            className="flex-grow border p-2 rounded-md"
 
            placeholder="Ask about oil prices..."
 
            value={userInput}
 
            onChange={(e) => setUserInput(e.target.value)}
 
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
 
          />
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