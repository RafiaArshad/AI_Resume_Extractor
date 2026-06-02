import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Upload, Zap, BarChart3, Shield, ArrowRight, Sparkles, Clock, CheckCircle2 } from "lucide-react";
import PageTransition from "@/components/layout/PageTransition";
import { useUpload } from "@/context/UploadContext";
import heroBanner from "@/assets/hero-banner.webp";

const features = [
  { icon: Upload, title: "Easy Upload", desc: "Drag & drop PDF, DOCX, PNG, or JPG files" },
  { icon: Zap, title: "AI Extraction", desc: "Instant parsing of all resume fields" },
  { icon: BarChart3, title: "Skill Analysis", desc: "Visual breakdown with domain classification" },
  { icon: Shield, title: "Secure & Private", desc: "Your data is processed and never stored" },
];

const stats = [
  { value: "95%+", label: "Accuracy Rate" },
  { value: "<3s", label: "Processing Time" },
  { value: "10K+", label: "Resumes Parsed" },
  { value: "4", label: "File Formats" },
];

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

const HomePage = () => {
  const { hasUploaded } = useUpload();

  return (
    <PageTransition>
      <div className="min-h-screen pt-16">
        {/* Hero with Banner */}
        <section className="relative overflow-hidden min-h-[85vh] flex items-center">
          {/* Background image */}
          <div className="absolute inset-0">
            <img
              src={heroBanner}
              alt=""
              className="w-full h-full object-cover"
              loading="eager"
              fetchPriority="high"
            />
            <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-background/60 to-background" />
            <div className="absolute inset-0 hero-gradient opacity-60" />
          </div>

          {/* Floating orbs */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-20 left-1/4 w-64 h-64 bg-primary/8 rounded-full blur-3xl animate-float" />
            <div className="absolute bottom-32 right-1/4 w-80 h-80 bg-primary/5 rounded-full blur-3xl animate-float" style={{ animationDelay: "3s" }} />
          </div>

          <div className="relative container mx-auto px-4 py-20 md:py-28 text-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
              <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/15 text-primary text-sm font-medium mb-8 border border-primary/25 backdrop-blur-sm">
                <Sparkles className="w-3.5 h-3.5" /> AI-Powered Resume Extraction
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-4xl md:text-6xl lg:text-7xl font-bold max-w-4xl mx-auto leading-[1.1] text-white"
            >
              Transform Any Resume{" "}
              <span className="gradient-text">into Structured Data</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mt-6 text-lg md:text-xl max-w-2xl mx-auto text-white/75 leading-relaxed"
            >
              Upload any CV and let our AI instantly extract skills, experience, education, and more — beautifully organized and ready to use.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mt-10 flex flex-col sm:flex-row gap-4 justify-center"
            >
              <Link
                to="/upload"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl gradient-bg text-primary-foreground font-semibold shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 animate-pulse-glow text-base"
              >
                Upload Resume <ArrowRight className="w-4 h-4" />
              </Link>
              {hasUploaded && (
                <Link
                  to="/results"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-white/10 text-white font-semibold hover:bg-white/20 transition-colors border border-white/20 backdrop-blur-sm text-base"
                >
                  View Results
                </Link>
              )}
            </motion.div>

            {/* Stats row */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.45 }}
              className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-2xl mx-auto"
            >
              {stats.map((stat) => (
                <div key={stat.label} className="text-center p-3 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                  <p className="text-2xl md:text-3xl font-bold gradient-text">{stat.value}</p>
                  <p className="text-xs text-white/60 mt-1 font-medium">{stat.label}</p>
                </div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Features */}
        <section className="container mx-auto px-4 py-24">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="text-sm font-semibold text-primary uppercase tracking-widest mb-3 block">Features</span>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-muted-foreground max-w-lg mx-auto">
              Three simple steps to go from document to structured data.
            </p>
          </motion.div>

          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {features.map((f, i) => (
              <motion.div key={i} variants={fadeUp} className="glass-card-hover rounded-xl p-6">
                <div className="w-12 h-12 rounded-lg gradient-bg flex items-center justify-center mb-4">
                  <f.icon className="w-6 h-6 text-primary-foreground" />
                </div>
                <h3 className="font-display font-semibold text-lg mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground">{f.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* Process Steps */}
        <section className="container mx-auto px-4 pb-24">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="text-sm font-semibold text-primary uppercase tracking-widest mb-3 block">Process</span>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Simple as 1-2-3</h2>
          </motion.div>

          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto"
          >
            {[
              { step: "01", icon: Upload, title: "Upload", desc: "Drop your resume in any supported format" },
              { step: "02", icon: Clock, title: "Process", desc: "Our AI extracts all structured data in seconds" },
              { step: "03", icon: CheckCircle2, title: "Results", desc: "View beautifully organized skills, experience & more" },
            ].map((item, i) => (
              <motion.div key={i} variants={fadeUp} className="text-center relative">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl gradient-bg mb-5 shadow-lg">
                  <item.icon className="w-7 h-7 text-primary-foreground" />
                </div>
                <p className="text-xs font-bold text-primary/60 uppercase tracking-widest mb-2">Step {item.step}</p>
                <h3 className="font-display font-semibold text-xl mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* CTA */}
        <section className="container mx-auto px-4 pb-24">
          <div className="glass-card-hover rounded-2xl p-8 md:p-16 text-center relative overflow-hidden">
            <div className="absolute inset-0 gradient-bg opacity-5" />
            <h2 className="relative text-3xl md:text-4xl font-bold mb-4">Ready to Get Started?</h2>
            <p className="relative text-muted-foreground mb-8 max-w-md mx-auto">
              Upload your first resume and see the magic of AI extraction.
            </p>
            <Link
              to="/upload"
              className="relative inline-flex items-center gap-2 px-8 py-3.5 rounded-xl gradient-bg text-primary-foreground font-semibold shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5"
            >
              Start Extracting <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>
      </div>
    </PageTransition>
  );
};

export default HomePage;
