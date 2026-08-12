import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { LoginPage } from "./LoginPage";

vi.mock("../api/resources", () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn(),
    logout: vi.fn(),
  },
}));

import { authApi } from "../api/resources";

function renderPage() {
  return render(
    <AuthProvider>
      <LoginPage />
    </AuthProvider>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.mocked(authApi.login).mockReset();
    vi.mocked(authApi.me).mockReset();
  });

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

  it("prefills and submits the demo credentials", async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      user: {
        id: "1",
        email: "admin@mediavault.dev",
        full_name: "Ada Admin",
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString(),
      },
      tokens: {
        access_token: "access",
        refresh_token: "refresh",
        token_type: "bearer",
        expires_in: 1800,
      },
    });

    renderPage();
    await userEvent.click(screen.getByRole("button", { name: /use demo/i }));
    expect(screen.getByLabelText(/email/i)).toHaveValue("admin@mediavault.dev");
    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith("admin@mediavault.dev", "ChangeMe123!");
    });
  });
});
