import { createContext } from "react";
import { UserProfile } from "@/services/authService";

export interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<UserProfile>;
  signup: (email: string, password: string, fullName: string) => Promise<UserProfile>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
