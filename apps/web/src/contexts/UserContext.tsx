// Mock User type for anonymous access
interface User {
  id: string;
  email: string;
  user_metadata: Record<string, any>;
  app_metadata: Record<string, any>;
  aud: string;
  created_at: string;
  updated_at: string;
  role: string;
  confirmation_sent_at: string;
  recovery_sent_at: string;
  email_confirmed_at: string;
  confirmed_at: string;
  last_sign_in_at: string;
  phone: string;
  phone_confirmed_at: string | null;
  factors: any;
}
import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

type UserContentType = {
  getUser: () => Promise<User | undefined>;
  user: User | undefined;
  loading: boolean;
};

const UserContext = createContext<UserContentType | undefined>(undefined);

// Mock user data for anonymous access
const MOCK_USER: User = {
  id: "anonymous-user",
  email: "anonymous@example.com",
  user_metadata: {},
  app_metadata: {},
  aud: "authenticated",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  role: "authenticated",
  confirmation_sent_at: new Date().toISOString(),
  recovery_sent_at: new Date().toISOString(),
  email_confirmed_at: new Date().toISOString(),
  confirmed_at: new Date().toISOString(),
  last_sign_in_at: new Date().toISOString(),
  phone: "",
  phone_confirmed_at: null,
  factors: null,
};

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(MOCK_USER);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Always set the mock user immediately
    setUser(MOCK_USER);
    setLoading(false);
  }, []);

  async function getUser() {
    // Always return the mock user
    return MOCK_USER;
  }

  const contextValue: UserContentType = {
    getUser,
    user,
    loading,
  };

  return (
    <UserContext.Provider value={contextValue}>{children}</UserContext.Provider>
  );
}

export function useUserContext() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUserContext must be used within a UserProvider");
  }
  return context;
}
