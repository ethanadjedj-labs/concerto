import { HeroClaudeDemo } from "@/components/HeroClaudeDemo";

export default function HeroDemoPage() {
  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{ background: "#faf9f5" }}
    >
      <div className="w-full max-w-3xl">
        <HeroClaudeDemo />
      </div>
    </div>
  );
}
