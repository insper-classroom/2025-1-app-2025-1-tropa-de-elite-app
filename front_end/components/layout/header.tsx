"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldAlertIcon } from "lucide-react";
import Image from "next/image";

import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ui/theme-toggle";

const navItems = [
  { name: "Dashboard", href: "/" },
  { name: "Single Analysis", href: "/single-predict" },
  { name: "Batch Processing", href: "/batch-predict" },
  { name: "Audit Logs", href: "/logs" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-[#ffe600] shadow-md">
      <div className="max-w-5xl mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center">
          <img
            src="/mercado-pago-logo.png"
            width={140}
            height={50}
            className="bg-transparent object-contain"
          />
        </div>
        <nav className="flex items-center space-x-1 sm:space-x-4">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-4 py-2 text-base font-semibold rounded-full transition-colors hover:bg-[#005ea6]/10 hover:text-[#005ea6]",
                pathname === item.href
                  ? "text-[#005ea6] bg-white shadow"
                  : "text-[#222]"
              )}
            >
              {item.name}
            </Link>
          ))}
        </nav>
        <div className="flex items-center space-x-4">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}