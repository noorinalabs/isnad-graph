import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect } from "vitest"
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "../Dialog"

describe("Dialog", () => {
  it("opens when trigger is clicked", async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Title</DialogTitle>
            <DialogDescription>Description</DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>,
    )
    expect(screen.queryByText("Title")).not.toBeInTheDocument()
    await userEvent.click(screen.getByText("Open"))
    expect(screen.getByText("Title")).toBeInTheDocument()
    expect(screen.getByText("Description")).toBeInTheDocument()
  })

  it("has an accessible close button", async () => {
    render(
      <Dialog defaultOpen>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Test Dialog</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>,
    )
    expect(screen.getByText("Close")).toBeInTheDocument()
  })
})
