import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { lazy, Suspense } from "react";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/context/ThemeContext";
import { UploadProvider } from "@/context/UploadContext";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import HomePage from "@/pages/HomePage";

const UploadPage = lazy(() => import("@/pages/UploadPage"));
const ResultsPage = lazy(() => import("@/pages/ResultsPage"));
const AboutPage = lazy(() => import("@/pages/AboutPage"));
const SearchPage = lazy(() => import("@/pages/SearchPage"));
const NotFound = lazy(() => import("@/pages/NotFound"));

const queryClient = new QueryClient();

const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
  </div>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <UploadProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Header />
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/results/:resumeId" element={<ResultsPage />} />
                <Route path="/search" element={<SearchPage />} /> 
                <Route path="/about" element={<AboutPage />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
            <Footer />
          </BrowserRouter>
        </TooltipProvider>
      </UploadProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;


