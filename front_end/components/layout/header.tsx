"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldAlertIcon } from "lucide-react";

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
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center">
        <div className="mr-4 flex items-center space-x-2">
          <ShieldAlertIcon className="h-6 w-6 text-primary" />
          <span className="hidden font-bold sm:inline-block text-lg">
            FraudGuard
          </span>
        </div>
        <nav className="flex flex-1 items-center space-x-1 sm:space-x-4">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-3 py-2 text-sm font-medium transition-colors hover:text-primary",
                pathname === item.href
                  ? "text-primary"
                  : "text-muted-foreground"
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