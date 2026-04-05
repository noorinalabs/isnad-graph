import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableCaption } from "../Table"

describe("Table", () => {
  it("renders a complete table", () => {
    render(
      <Table>
        <TableCaption>Narrators</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Era</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Al-Bukhari</TableCell>
            <TableCell>9th century</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    )
    expect(screen.getByText("Name")).toBeInTheDocument()
    expect(screen.getByText("Al-Bukhari")).toBeInTheDocument()
    expect(screen.getByText("Narrators")).toBeInTheDocument()
  })

  it("applies custom className to cells", () => {
    const { container } = render(
      <Table>
        <TableBody>
          <TableRow>
            <TableCell className="text-end">RTL cell</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    )
    const cell = container.querySelector("td")
    expect(cell).toHaveClass("text-end")
  })
})
