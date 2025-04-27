"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  // Handle opening/closing of the menu
  const toggleMenu = () => setIsOpen(!isOpen);

  // Handle clicking a link, automatically close the menu
  const handleLinkClick = () => setIsOpen(false);

  return (
    <nav className="fixed top-4 right-4 z-50">
      <details className="relative group">
        {/* Hamburger icon */}
        <summary
          className="cursor-pointer list-none text-4xl text-foreground"
          onClick={toggleMenu}
        >
          &#9776;
        </summary>

        {/* Sliding menu */}
        <div
          className={`absolute right-0 mt-2 flex flex-col items-end space-y-2 bg-background text-foreground p-4 rounded-lg shadow-lg opacity-0 scale-95 transform transition-all duration-300 ease-out ${
            isOpen ? "opacity-100 scale-100" : "opacity-0 scale-95"
          }`}
        >
          <NavLink href="/" currentPath={pathname} label="Home" onClick={handleLinkClick} />
          <NavLink href="/pages/chat" currentPath={pathname} label="Chat" onClick={handleLinkClick} />
          <NavLink href="/pages/graph" currentPath={pathname} label="Graph" onClick={handleLinkClick} />
          <NavLink href="/pages/3dgraph" currentPath={pathname} label="3D Graph" onClick={handleLinkClick} />
        </div>
      </details>
    </nav>
  );
}

// NavLink component for highlighting the current page and handling clicks
function NavLink({
  href,
  currentPath,
  label,
  onClick,
}: {
  href: string;
  currentPath: string;
  label: string;
  onClick: () => void;
}) {
  const isActive = currentPath === href;
  return (
    <Link
      href={href}
      onClick={onClick} // Auto-close when clicking the link
      className={`text-lg font-semibold ${
        isActive
          ? "font-bold underline text-blue-500"
          : "opacity-70 hover:opacity-100"
      } whitespace-nowrap`} // Prevent text from breaking into multiple lines
    >
      {label}
    </Link>
  );
}
