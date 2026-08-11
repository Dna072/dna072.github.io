import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { LoginPage } from "./LoginPage";

function renderPage() {
  return render(
    <AuthProvider>
      <LoginPage />
    </AuthProvider>,
  );
}

describe("LoginPage", () => {
  it("renders the sign-in form by default", () => {
    renderPage();
    expect(screen.getByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("shows the value branches in the marketing panel", () => {
    renderPage();
    expect(screen.getByText(/Role-based access/i)).toBeInTheDocument();
    expect(screen.getByText(/Signed, expiring links/i)).toBeInTheDocument();
  });

  it("switches to the registration form", async () => {
    renderPage();
    await userEvent.click(screen.getByRole("button", { name: /create one/i }));
    expect(screen.getByRole("heading", { name: /create your account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
  });

  it("prefills the demo credentials", async () => {
    renderPage();
    await userEvent.click(screen.getByRole("button", { name: /use demo/i }));
    expect(screen.getByLabelText(/email/i)).toHaveValue("admin@mediavault.dev");
  });
});
