import { useEffect, useState } from "react";

import { getImageObjectUrl } from "@/api/documents";

interface AuthImageProps {
  documentId: number;
  alt: string;
  className?: string;
}

export function AuthImage({ documentId, alt, className = "" }: AuthImageProps) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    getImageObjectUrl(documentId)
      .then((value) => {
        if (active) {
          objectUrl = value;
          setUrl(value);
        }
      })
      .catch(() => undefined);
    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [documentId]);

  if (!url) {
    return <div className={`animate-pulse bg-foam-200 dark:bg-roast-800 ${className}`} />;
  }
  return <img src={url} alt={alt} className={className} />;
}
