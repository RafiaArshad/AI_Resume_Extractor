import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, Menu, X } from "lucide-react";
import ThemeToggle from "@/components/shared/ThemeToggle";
import { useUpload } from "@/context/UploadContext";
import { Search } from "lucide-react";
import { useState } from "react";

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { hasUploaded } = useUpload();

  const navItems = [
    { path: "/", label: "Home" },
    { path: "/upload", label: "Upload" },
    ...(hasUploaded ? [{ path: "/results", label: "Results" }] : []),
    { path: "/about", label: "About" },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center">
            <FileText className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-display font-bold text-lg text-foreground">ResumeAI</span>
        </Link>

<button
  onClick={() => navigate("/search")}
  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors inline-flex items-center gap-1.5 ${
    location.pathname === "/search"
      ? "bg-primary/10 text-primary"
      : "text-muted-foreground hover:text-foreground"
  }`}
>
  <Search className="w-3.5 h-3.5" strokeWidth={1.75} />
  Search
</button>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className="relative px-4 py-2 text-sm font-semibold text-foreground/70 hover:text-foreground transition-colors"
            >
              {location.pathname === item.path && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute inset-0 bg-primary/10 border border-primary/20 rounded-lg"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <span className="relative z-10">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button
            className="md:hidden p-2 rounded-lg hover:bg-secondary transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <motion.nav
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden bg-background/95 backdrop-blur-xl border-t border-border/50 p-4"
        >
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setMobileOpen(false)}
              className={`block px-4 py-3 rounded-lg text-sm font-semibold transition-colors ${
                location.pathname === item.path
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-foreground/70 hover:text-foreground hover:bg-secondary"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </motion.nav>
      )}
    </header>
  );
};

export default Header;
