export interface User {
    id: string;
    username: string;
}

export interface ZappaiLocation {
    id: string;
    country: string;
    name: string;
    longitude: number;
    latitude: number;
    isModelReady: boolean;
    isDownloadingPastClimateData: boolean;
    lastPastClimateDataYear: number | null;
    lastPastClimateDataMonth: number | null;
}
  

// Define a type for the context
export interface AuthContextType {
    currentUser: User | null;
    setCurrentUser: React.Dispatch<React.SetStateAction<User | null>>;
}

export interface Crop {
    name: string;
}