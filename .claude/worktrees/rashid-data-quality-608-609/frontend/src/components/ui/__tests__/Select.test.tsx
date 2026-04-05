import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../Select"

describe("Select", () => {
  it("renders trigger with placeholder", () => {
    render(
      <Select>
        <SelectTrigger>
          <SelectValue placeholder="Choose..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="a">Option A</SelectItem>
          <SelectItem value="b">Option B</SelectItem>
        </SelectContent>
      </Select>,
    )
    expect(screen.getByRole("combobox")).toBeInTheDocument()
    expect(screen.getByText("Choose...")).toBeInTheDocument()
  })

  it("renders with correct aria attributes", () => {
    render(
      <Select>
        <SelectTrigger>
          <SelectValue placeholder="Choose..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="a">Option A</SelectItem>
          <SelectItem value="b">Option B</SelectItem>
        </SelectContent>
      </Select>,
    )
    const trigger = screen.getByRole("combobox")
    expect(trigger).toHaveAttribute("aria-expanded", "false")
    expect(trigger).toHaveAttribute("data-state", "closed")
  })
})
