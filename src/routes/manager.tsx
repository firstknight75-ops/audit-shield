import { createFileRoute, Outlet } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
export const Route = createFileRoute("/manager")({
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
});
