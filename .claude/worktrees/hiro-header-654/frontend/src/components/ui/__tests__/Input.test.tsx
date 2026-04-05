import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, vi } from "vitest"
import { Input } from "../Input"

describe("Input", () => {
  it("renders an input element", () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument()
  })

  it("accepts typed input", async () => {
    render(<Input placeholder="Type here" />)
    const input = screen.getByPlaceholderText("Type here")
    await userEvent.type(input, "hello")
    expect(input).toHaveValue("hello")
  })

  it("supports disabled state", () => {
    render(<Input disabled placeholder="Disabled" />)
    expect(screen.getByPlaceholderText("Disabled")).toBeDisabled()
  })

  it("supports different types", () => {
    render(<Input type="email" placeholder="Email" />)
    expect(screen.getByPlaceholderText("Email")).toHaveAttribute("type", "email")
  })

  it("forwards ref", () => {
    const ref = vi.fn()
    render(<Input ref={ref} />)
    expect(ref).toHaveBeenCalled()
  })

  it("renders correctly in RTL context", () => {
    render(
      <div dir="rtl">
        <Input placeholder="Arabic input" />
      </div>,
    )
    expect(screen.getByPlaceholderText("Arabic input")).toBeInTheDocument()
  })
})
