import { createFileRoute, Outlet } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
export const Route = createFileRoute("/admin")({
  component: () => (<AppShell><Outlet /></AppShell>),
});