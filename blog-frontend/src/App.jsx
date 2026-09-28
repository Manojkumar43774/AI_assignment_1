import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./AuthContext";
import Navbar from "./components/Navbar";
import AuthCallback from "./pages/AuthCallback";
import EditBlog from "./pages/EditBlog";
import Home from "./pages/Home";
import Login from "./pages/Login";
import MyBlogs from "./pages/MyBlogs";
import NewBlog from "./pages/NewBlog";
import PostDetail from "./pages/PostDetail";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import UserProfile from "./pages/UserProfile";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="app-shell">
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/new" element={<NewBlog />} />
            <Route path="/my-blogs" element={<MyBlogs />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/users/:username" element={<UserProfile />} />
            <Route path="/posts/:id" element={<PostDetail />} />
            <Route path="/posts/:id/edit" element={<EditBlog />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
