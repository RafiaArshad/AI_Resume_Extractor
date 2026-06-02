import { createContext, useContext, useState, ReactNode } from "react";

interface UploadContextType {
  hasUploaded: boolean;
  setHasUploaded: (v: boolean) => void;
}

const UploadContext = createContext<UploadContextType>({ hasUploaded: false, setHasUploaded: () => {} });

export const useUpload = () => useContext(UploadContext);

export const UploadProvider = ({ children }: { children: ReactNode }) => {
  const [hasUploaded, setHasUploaded] = useState(false);
  return (
    <UploadContext.Provider value={{ hasUploaded, setHasUploaded }}>
      {children}
    </UploadContext.Provider>
  );
};
