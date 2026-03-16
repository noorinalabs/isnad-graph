import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/narrators', label: 'Narrators' },
  { to: '/hadiths', label: 'Hadiths' },
  { to: '/collections', label: 'Collections' },
  { to: '/search', label: 'Search' },
  { to: '/timeline', label: 'Timeline' },
]

export default function Sidebar() {
  return (
    <nav style={{ width: 220, padding: '1rem', borderRight: '1px solid #ddd' }}>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {navItems.map((item) => (
          <li key={item.to} style={{ marginBottom: '0.5rem' }}>
            <NavLink
              to={item.to}
              style={({ isActive }) => ({
                textDecoration: 'none',
                fontWeight: isActive ? 700 : 400,
                color: isActive ? '#1a73e8' : '#333',
              })}
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
