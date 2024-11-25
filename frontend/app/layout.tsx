"use client";

import Footer from "@/components/Footer";
import Header from "@/components/Header";
import ScrollToTop from "@/components/ScrollToTop";
import { Inter, Poppins } from "next/font/google";
import "node_modules/react-modal-video/css/modal-video.css";
import "../styles/index.css";

const inter = Inter({ subsets: ["latin"] });

const poppins = Poppins({
  weight: ['400', '500', '600', '700', '800'],
  subsets: ['latin'],
  display: 'swap',
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html suppressHydrationWarning lang="en">
      {/*
        <head /> will contain the components returned by the nearest parent
        head.js. Find out more at https://beta.nextjs.org/docs/api-reference/file-conventions/head
      */}
      <head />

      <body className={`bg-[#FCFCFC] dark:bg-black ${inter.className}`}>
        <ThemeProvider attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange>
        {/* <Providers> */}
          <Header />
          {children}
          <Footer />
          <ScrollToTop />
        {/* </Providers> */}
        </ThemeProvider>
      </body>
    </html>
  );
}

import { Providers } from "./providers";import { ThemeProvider } from "@/components/theme-provider";

