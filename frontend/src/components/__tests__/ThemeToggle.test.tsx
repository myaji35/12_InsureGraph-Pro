import { render, screen } from '@testing-library/react'
import { ThemeToggle } from '../ThemeToggle'

describe('ThemeToggle', () => {
  it('renders theme toggle button', () => {
    render(<ThemeToggle />)

    // Should render a button
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('displays sun or moon icon based on theme', () => {
    const { container } = render(<ThemeToggle />)

    // Should have an SVG icon
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })
})
