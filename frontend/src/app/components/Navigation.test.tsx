import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { Navigation } from "./Navigation";

let router: ReturnType<typeof createMemoryRouter>;

function renderWithRouter(initialPath = "/") {
  router = createMemoryRouter([{ path: "*", element: <Navigation /> }], {
    initialEntries: [initialPath],
  });
  return render(<RouterProvider router={router} />);
}

describe("Navigation", () => {
  it("renders logo and primary nav labels", () => {
    renderWithRouter();
    expect(screen.getByText("AskVigil")).toBeInTheDocument();
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Guidance")).toBeInTheDocument();
    expect(screen.getByText("Learning")).toBeInTheDocument();
    expect(screen.getByText("Quiz")).toBeInTheDocument();
  });

  it("clicking logo navigates to home", () => {
    renderWithRouter("/guidance/job-scam");
    fireEvent.click(screen.getByText("AskVigil"));
    expect(router.state.location.pathname).toBe("/");
  });
});
