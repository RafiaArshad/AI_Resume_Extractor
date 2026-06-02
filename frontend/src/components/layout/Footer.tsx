import { FileText } from "lucide-react";
import { Link } from "react-router-dom";

const Footer = () => (
  <footer className="border-t border-border/50 bg-card/50 backdrop-blur-sm">
    <div className="container mx-auto px-4 py-12">
      <div className="grid md:grid-cols-3 gap-8">
        <div>
          <Link to="/" className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center">
              <FileText className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-display font-bold text-lg">ResumeAI</span>
          </Link>
          <p className="text-sm text-muted-foreground max-w-xs">
            AI-powered resume extraction and analysis. Upload once, get structured data instantly.
          </p>
        </div>
        <div>
          <h4 className="font-display font-semibold mb-4">Quick Links</h4>
          <div className="space-y-2">
            {[
              { to: "/", label: "Home" },
              { to: "/upload", label: "Upload Resume" },
              { to: "/search", label: "Search Resumes" },
              { to: "/about", label: "About" },
            ].map((link) => (
              <Link key={link.to} to={link.to} className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                {link.label}
              </Link>
            ))}
          </div>
        </div>
        <div>
          <h4 className="font-display font-semibold mb-4">Supported Formats</h4>
          <div className="flex flex-wrap gap-2">
            {["PDF", "DOCX"].map((fmt) => (
              <span key={fmt} className="px-3 py-1 text-xs font-medium rounded-full bg-accent text-accent-foreground">
                {fmt}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-8 pt-8 border-t border-border/50 text-center text-sm text-muted-foreground">
        © {new Date().getFullYear()} ResumeAI. All rights reserved.
      </div>
    </div>
  </footer>
);

export default Footer;
