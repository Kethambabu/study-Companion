import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@/context/useAuth";
import { signupSchema, SignupFormData } from "@/lib/validations/auth";
import { Sparkles, UserPlus, AlertCircle } from "lucide-react";

export const SignupPage: React.FC = () => {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (data: SignupFormData) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      await signup(data.email, data.password, data.fullName);
      navigate("/", { replace: true });
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Registration failed.");
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
          <h2 className="text-2xl font-bold tracking-tight text-foreground">Create Account</h2>
          <p className="text-xs text-muted-foreground">Start your personalized learning and growth workspace</p>
        </div>

        {serverError && (
          <div className="p-3 bg-red-500/10 text-red-400 border border-red-500/20 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{serverError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">Full Name</label>
            <input
              type="text"
              {...register("fullName")}
              className="w-full px-3.5 py-2.5 bg-secondary/50 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
              placeholder="Jane Doe"
            />
            {errors.fullName && (
              <p className="text-[11px] text-red-400 mt-1">{errors.fullName.message}</p>
            )}
          </div>

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

          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">Confirm Password</label>
            <input
              type="password"
              {...register("confirmPassword")}
              className="w-full px-3.5 py-2.5 bg-secondary/50 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
              placeholder="••••••••"
            />
            {errors.confirmPassword && (
              <p className="text-[11px] text-red-400 mt-1">{errors.confirmPassword.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2.5 px-4 bg-primary text-primary-foreground font-semibold rounded-lg text-sm shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <span>Creating Account...</span>
            ) : (
              <>
                <UserPlus className="h-4 w-4" />
                <span>Register</span>
              </>
            )}
          </button>
        </form>

        <div className="text-center text-xs text-muted-foreground pt-2 border-t border-border">
          Already have an account?{" "}
          <Link to="/login" className="text-primary font-medium hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};
