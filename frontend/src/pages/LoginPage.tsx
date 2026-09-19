import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@/context/useAuth";
import { loginSchema, LoginFormData } from "@/lib/validations/auth";
import { Sparkles, LogIn, AlertCircle } from "lucide-react";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || "/";

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      const userProfile = await login(data.email, data.password);
      const isAdmin = userProfile?.role === "admin" || userProfile?.is_admin;
      if (isAdmin) {
        const targetPath = from && from !== "/" && from.startsWith("/admin") ? from : "/admin";
        navigate(targetPath, { replace: true });
      } else {
        navigate(from, { replace: true });
      }
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = async (email: string) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      const userProfile = await login(email, "password123");
      const isAdmin = userProfile?.role === "admin" || userProfile?.is_admin;
      if (isAdmin) {
        navigate("/admin", { replace: true });
      } else {
        navigate("/", { replace: true });
      }
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md glass-panel p-8 rounded-2xl space-y-6 shadow-2xl">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 bg-primary/10 text-primary rounded-xl border border-primary/20 mb-1">
            <Sparkles className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground">Welcome Back</h2>
          <p className="text-xs text-muted-foreground">Sign in to your AI Study Companion workspace</p>
        </div>

        {/* Demo Quick Logins */}
        <div className="bg-secondary/30 border border-border p-3.5 rounded-xl space-y-2 text-xs">
          <p className="font-semibold text-foreground text-[11px] uppercase tracking-wider">
            1-Click Demo Profiles (Isolated Data)
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin("varshitha@example.com")}
              className="p-2 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 rounded-lg font-medium text-left transition"
            >
              <div className="font-bold">Student A</div>
              <div className="text-[10px] opacity-80">Varshitha (AI & Py)</div>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("studentb@example.com")}
              className="p-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 text-blue-300 rounded-lg font-medium text-left transition"
            >
              <div className="font-bold">Student B</div>
              <div className="text-[10px] opacity-80">DSA & DBMS</div>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("studentc@example.com")}
              className="p-2 bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/20 text-violet-300 rounded-lg font-medium text-left transition"
            >
              <div className="font-bold">Student C</div>
              <div className="text-[10px] opacity-80">Cyber & ML</div>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("admin@example.com")}
              className="p-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-amber-300 rounded-lg font-medium text-left transition"
            >
              <div className="font-bold">Admin</div>
              <div className="text-[10px] opacity-80">System Dashboard</div>
            </button>
          </div>
        </div>

        {serverError && (
          <div className="p-3 bg-red-500/10 text-red-400 border border-red-500/20 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{serverError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">Email Address</label>
            <input
              type="email"
              {...register("email")}
              className="w-full px-3.5 py-2.5 bg-secondary/50 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
              placeholder="name@example.com"
            />
            {errors.email && (
              <p className="text-[11px] text-red-400 mt-1">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">Password</label>
            <input
              type="password"
              {...register("password")}
              className="w-full px-3.5 py-2.5 bg-secondary/50 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
              placeholder="••••••••"
            />
            {errors.password && (
              <p className="text-[11px] text-red-400 mt-1">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2.5 px-4 bg-primary text-primary-foreground font-semibold rounded-lg text-sm shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <LogIn className="h-4 w-4" />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        <div className="text-center text-xs text-muted-foreground pt-2 border-t border-border">
          Don't have an account?{" "}
          <Link to="/signup" className="text-primary font-medium hover:underline">
            Create an Account
          </Link>
        </div>
      </div>
    </div>
  );
};
