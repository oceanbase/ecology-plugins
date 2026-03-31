import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'UniSelect Course',
  description:
    'UniSelect Course is a university course selection management system. Manage courses, view details, add and delete reviews, and edit capacity.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
