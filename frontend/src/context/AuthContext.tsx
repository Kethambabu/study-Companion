import React, { useEffect, useState } from "react";
import { UserProfile, authService } from "@/services/authService";
import { AuthContext } from "./authContextInstance";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Restore session on mount
  useEffect(() => {
    const restoreSession = async () => {
      const token = authService.getToken();
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const userProfile = await authService.getMe();
        setUser(userProfile);
      } catch {
        authService.clearToken();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    restoreSession();
  }, []);

  const login = async (email: string, password: string): Promise<UserProfile> => {
    const data = await authService.login(email, password);
    setUser(data.user);
    return data.user;
  };

  const signup = async (email: string, password: string, fullName: string): Promise<UserProfile> => {
    const data = await authService.signup(email, password, fullName);
    setUser(data.user);
    return data.user;
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
