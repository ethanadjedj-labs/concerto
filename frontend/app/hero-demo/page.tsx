import { HeroDemo } from "@/components/HeroDemo";

export default function HeroDemoPage() {
  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{ background: "#0a0a0a" }}
    >
      <div className="w-full max-w-2xl">
        <HeroDemo />
      </div>
    </div>
  );
}
