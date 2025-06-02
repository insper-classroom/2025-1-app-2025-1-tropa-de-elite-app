import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ThemeProvider } from '@/components/theme-provider';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Sistema de Detecção de Fraudes',
  description: 'Sistema para detecção de fraudes em transações',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          disableTransitionOnChange
        >
          <div className="min-h-screen flex flex-col">
            <header className="border-b">
              <div className="container mx-auto p-4">
                <nav className="flex items-center justify-between">
                  <Link href="/" className="text-xl font-bold">
                    Sistema de Fraudes
                  </Link>
                  <div className="flex gap-4">
                    <Button variant="ghost" asChild>
                      <Link href="/">Upload</Link>
                    </Button>
                    <Button variant="ghost" asChild>
                      <Link href="/transacao">Transação Única</Link>
                    </Button>
                    <Button variant="ghost" asChild>
                      <Link href="/mensal">Análise Mensal</Link>
                    </Button>
                  </div>
                </nav>
              </div>
            </header>
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}