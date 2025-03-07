"use client";

import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

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
        <source src="/background.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* Placeholder for the circle image */}
      <div className="w-32 h-32 border-4 border-gray-300 rounded-full mb-8 bg-white opacity-90 z-10"></div>

      {/* Button */}
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
