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
    expect(screen.getByAltText("AskVigil Logo")).toBeInTheDocument();
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Scam Help")).toBeInTheDocument();
    expect(screen.getByText("Learning")).toBeInTheDocument();
    expect(screen.getByText("Quiz")).toBeInTheDocument();
    expect(screen.getByText("Scam Feed")).toBeInTheDocument();
  });

  it("clicking logo navigates to home", () => {
    renderWithRouter("/guidance/job-scam");
    fireEvent.click(screen.getByAltText("AskVigil Logo"));
    expect(router.state.location.pathname).toBe("/");
  });
});
