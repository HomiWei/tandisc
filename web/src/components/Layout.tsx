import { NavLink, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="shell">
      <aside className="rail">
        <NavLink to="/" className="brand" end>
          探盘
        </NavLink>
        <nav className="rail-nav" aria-label="榜单">
          <NavLink to="/products" className="nav-link">
            产品收录
          </NavLink>
          <NavLink to="/github" className="nav-link">
            GitHub 月榜
          </NavLink>
        </nav>
        <p className="rail-note">净增 star 不是收入。</p>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
