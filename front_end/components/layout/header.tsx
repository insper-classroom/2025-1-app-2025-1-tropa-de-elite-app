"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Análise", href: "/" },
  { name: "Modelos", href: "/modelos" },
  { name: "Histórico", href: "/logs" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo do Mercado Libre */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="bg-[#3483fa] text-white px-3 py-1 rounded font-bold text-lg">
              ML
            </div>
            <span className="text-xl font-semibold text-gray-800">
              Análise de Fraude
            </span>
          </Link>

          {/* Navegação Simplificada */}
          <nav className="flex items-center space-x-6">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-[#3483fa]",
                  pathname === item.href 
                    ? "text-[#3483fa] border-b-2 border-[#3483fa] pb-1" 
                    : "text-gray-600"
                )}
              >
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
    </header>
  );
}