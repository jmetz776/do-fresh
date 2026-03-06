export const metadata = {
  title: 'DemandOrchestrator',
  description: 'MVP queue UI',
};

export default function RootLayout({ children }: { children: any }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
