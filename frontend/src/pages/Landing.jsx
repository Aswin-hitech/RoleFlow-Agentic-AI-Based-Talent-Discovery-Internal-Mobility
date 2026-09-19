import CallToAction from "../components/CallToAction.jsx";
import Features from "../components/Features.jsx";
import Footer from "../components/Footer.jsx";
import Hero from "../components/Hero.jsx";
import Navbar from "../components/Navbar.jsx";
import Personas from "../components/Personas.jsx";
import Pipeline from "../components/Pipeline.jsx";
import Quadrant from "../components/Quadrant.jsx";
import TechStack from "../components/TechStack.jsx";

export default function Landing() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <Hero />
        <Pipeline />
        <Quadrant />
        <Personas />
        <Features />
        <TechStack />
        <CallToAction />
      </main>
      <Footer />
    </div>
  );
}
