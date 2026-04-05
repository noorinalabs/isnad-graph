import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../Card"

describe("Card", () => {
  it("renders card with all sections", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
        </CardHeader>
        <CardContent>Content</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>,
    )
    expect(screen.getByText("Title")).toBeInTheDocument()
    expect(screen.getByText("Description")).toBeInTheDocument()
    expect(screen.getByText("Content")).toBeInTheDocument()
    expect(screen.getByText("Footer")).toBeInTheDocument()
  })

  it("applies custom className", () => {
    const { container } = render(<Card className="custom-class">Test</Card>)
    expect(container.firstChild).toHaveClass("custom-class")
  })
})
