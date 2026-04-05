import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { Badge } from "../Badge"

describe("Badge", () => {
  it("renders badge text", () => {
    render(<Badge>Status</Badge>)
    expect(screen.getByText("Status")).toBeInTheDocument()
  })

  it("applies variant classes", () => {
    const { container } = render(<Badge variant="sunni">Sunni</Badge>)
    expect(container.firstChild).toHaveClass("bg-sunni-bg")
  })

  it("applies default variant", () => {
    const { container } = render(<Badge>Default</Badge>)
    expect(container.firstChild).toHaveClass("bg-primary")
  })

  it("applies custom className", () => {
    const { container } = render(<Badge className="extra">Test</Badge>)
    expect(container.firstChild).toHaveClass("extra")
  })

  it("renders destructive variant", () => {
    const { container } = render(<Badge variant="destructive">Error</Badge>)
    expect(container.firstChild).toHaveClass("bg-destructive")
  })
})
