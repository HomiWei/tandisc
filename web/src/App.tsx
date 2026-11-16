import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { GithubDetailPage } from "./pages/GithubDetailPage";
import { GithubListPage } from "./pages/GithubListPage";
import { HomePage } from "./pages/HomePage";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { ProductListPage } from "./pages/ProductListPage";

function NotFoundPage() {
  return (
    <div className="stack">
      <h1>没有这个页面</h1>
      <p>
        <Link to="/">返回首页</Link>
      </p>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductListPage />} />
          <Route path="/products/:id" element={<ProductDetailPage />} />
          <Route path="/github" element={<GithubListPage />} />
          <Route path="/github/:id" element={<GithubDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
