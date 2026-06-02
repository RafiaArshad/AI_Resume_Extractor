import { motion } from "framer-motion";
import { Brain, Target, Shield, Users } from "lucide-react";
import PageTransition from "@/components/layout/PageTransition";

const values = [
  { icon: Brain, title: "AI-First Approach", desc: "We leverage state-of-the-art NLP models to extract and classify resume data with 95%+ accuracy." },
  { icon: Target, title: "Precision Extraction", desc: "Every field — from certifications to project details — is captured with structured output ready for integration." },
  { icon: Shield, title: "Privacy by Design", desc: "Documents are processed in-memory and never persisted. Your data stays yours." },
  { icon: Users, title: "Built for Teams", desc: "Whether you're a recruiter or an enterprise, our API scales with your needs." },
];

const AboutPage = () => (
  <PageTransition>
    <div className="min-h-screen pt-24 pb-16">
      <div className="container mx-auto px-4 max-w-4xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-16">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">About ResumeAI</h1>
          <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
            We're building the most accurate AI-powered resume extraction platform, making it effortless to convert unstructured CVs into actionable data.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6 mb-16">
          {values.map((v, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card-hover rounded-xl p-6"
            >
              <div className="w-12 h-12 rounded-lg gradient-bg flex items-center justify-center mb-4">
                <v.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2">{v.title}</h3>
              <p className="text-sm text-muted-foreground">{v.desc}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="glass-card rounded-2xl p-8 md:p-12 text-center"
        >
          <h2 className="text-2xl md:text-3xl font-bold mb-4">Our Mission</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            The hiring process involves sifting through thousands of resumes. We believe AI can eliminate the manual parsing, letting recruiters and HR teams focus on what matters — finding the right talent. ResumeAI transforms any document format into clean, structured data in seconds.
          </p>
        </motion.div>
      </div>
    </div>
  </PageTransition>
);

export default AboutPage;
