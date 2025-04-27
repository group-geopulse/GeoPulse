"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Home() {
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(false);

  // Trigger the animation when the component is mounted
  useEffect(() => {
    setIsVisible(true); // This triggers the pop-in animation
  }, []);

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen overflow-hidden">
      {/* Background Video */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute top-0 left-0 w-full h-full object-cover -z-10"
      >
        <source src="/background_video.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* Button with logo (animation and floating effect) */}
      <button
        onClick={() => router.push("/pages/graph")}
        className={`z-10 relative flex items-center justify-center w-32 h-32 rounded-full mb-8 bg-transparent opacity-90 shadow-lg transition-transform duration-700 ${
          isVisible
            ? "transform scale-110 opacity-100 animate-popIn"
            : "opacity-0 scale-90"
        }`}
      >
        <img
          src="/logo.png" // Ensure your logo is at this path
          alt="Logo"
          className="w-full h-full object-contain animate-floatEffect"
        />
      </button>

      {/* Button for Chat */}
      <button
        onClick={() => router.push("/pages/chat")}
        className="z-10 flex items-center justify-between w-72 px-8 py-4 text-2xl font-semibold text-gray-500 border-2 border-black rounded-xl shadow-md transition hover:bg-gray-100 bg-white opacity-90 mt-14"
      >
        <span>Ask me anything</span>
        <span className="text-2xl">➜</span>
      </button>
    </div>
  );
}
